#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""A base class for implementing pipeline units - strides and steps."""

import re
import abc
import logging
from copy import copy
from typing import Optional

import attr
from voluptuous import Schema

from thoth.storages import GraphDatabase
from thoth.python import Project
from thoth.python import PackageVersion

from .context_base import ContextBase

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PipelineUnitBase(metaclass=abc.ABCMeta):
    """A base class for implementing pipeline units - strides and steps."""

    graph = attr.ib(type=GraphDatabase)
    project = attr.ib(type=Project)
    library_usage = attr.ib(type=dict, default=attr.Factory(dict))
    _parameters = attr.ib(type=dict)
    _name = attr.ib(type=str, default=None)

    # Schema used to validate step parameters - None value does not validate parameters.
    PARAMETERS_SCHEMA: Schema = None
    PARAMETERS_DEFAULT = {}

    _RE_CAMEL2SNAKE = re.compile("(?!^)([A-Z]+)")

    @classmethod
    def compute_expanded_parameters(cls, parameters_dict: Optional[dict]):
        """Compute parameters as they would be computed based on unit configuration."""
        result = copy(cls.PARAMETERS_DEFAULT)

        if parameters_dict:
            result.update(parameters_dict)

        return result

    @_parameters.default
    def _initialize_default_parameters(self) -> dict:
        """Initialize default parameters based on declared class' default parameters."""
        return copy(self.PARAMETERS_DEFAULT)

    @property
    def parameters(self) -> dict:
        """Get parameters of instantiated pipeline step."""
        return self._parameters

    @property
    def name(self) -> str:
        """Name of a stack pipeline."""
        if not self._name:
            self._name = self._RE_CAMEL2SNAKE.sub(
                r"_\1", self.__class__.__name__
            ).lower()

        return self._name

    def update_parameters(self, parameters_dict: dict) -> None:
        """Set parameters for a stack pipeline.

        If setting parameters fails due to schema checks, parameters are kept in an invalid state.
        """
        self.parameters.update(parameters_dict)
        if self.PARAMETERS_SCHEMA:
            _LOGGER.debug("Validating parameters for pipeline unit %r", self.name)
            try:
                self.PARAMETERS_SCHEMA(self.parameters)
            except Exception as exc:
                _LOGGER.exception(
                    "Failed to validate schema for pipeline unit %r: %s",
                    self.name,
                    str(exc),
                )
                raise

    def to_dict(self) -> dict:
        """Turn this pipeline step into its dictionary representation."""
        return attr.asdict(self)

    @staticmethod
    def is_aicoe_release(package_version: PackageVersion) -> bool:
        """Check if the given package-version is AICoE release."""
        return package_version.index.url.startswith("https://tensorflow.pypi.thoth-station.ninja/")

    @classmethod
    def get_aicoe_configuration(cls, package_version: PackageVersion) -> Optional[dict]:
        """Get AICoE specific configuration encoded in the AICoE index URL."""
        if not package_version.index.url.startswith("https://tensorflow.pypi.thoth-station.ninja/index/"):
            return None

        index_url = package_version.index.url[len("https://tensorflow.pypi.thoth-station.ninja/index/"):]
        conf_parts = index_url.strip("/").split("/")  # the last is always "simple"

        if len(conf_parts) == 3:
            # No OS specific release - e.g. manylinux compliant release.
            if not conf_parts[0].startswith("manylinux"):
                _LOGGER.warning("Failed to parse a platform tag")
                return None

            return {
                "os_name": None,
                "os_version": None,
                "configuration": conf_parts[1],
                "platform_tag": conf_parts[0],
            }
        elif len(conf_parts) == 5:
            if conf_parts[0] != "os":
                _LOGGER.warning("Failed to parse operating system specific URL of AICoE index")
                return None

            return {
                "os_name": conf_parts[1],
                "os_version": conf_parts[2],
                "configuration": conf_parts[3],
                "platform_tag": None,
            }

        _LOGGER.warning(
            "Failed to parse AICoE specific package source index configuration: %r",
            package_version.index.url
        )
        return None

    @abc.abstractmethod
    def run(self, context: ContextBase) -> None:
        """Entrypoint for a stack pipeline unit."""
