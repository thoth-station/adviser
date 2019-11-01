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
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Generator
from typing import TYPE_CHECKING
from contextlib import contextmanager

import attr
from voluptuous import Schema

from thoth.storages import GraphDatabase
from thoth.python import Project
from thoth.python import PackageVersion

from .context import Context

if TYPE_CHECKING:
    from .pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Unit(metaclass=abc.ABCMeta):
    """A base class for implementing pipeline units - strides and steps."""

    graph = attr.ib(type=GraphDatabase, kw_only=True)
    project = attr.ib(type=Project, kw_only=True)
    library_usage = attr.ib(
        type=Optional[Dict[str, Any]], default=attr.Factory(dict), kw_only=True
    )
    _parameters = attr.ib(type=Dict[str, Any], kw_only=True)
    _name = attr.ib(type=str, default=None, kw_only=True)
    _context = attr.ib(type=Optional[Context], default=None, kw_only=True)

    # Schema used to validate step parameters - None value does not validate parameters.
    PARAMETERS_SCHEMA: Schema = None
    PARAMETERS_DEFAULT: Dict[str, Any] = {}

    _RE_CAMEL2SNAKE = re.compile("(?!^)([A-Z]+)")
    _AICOE_PYTHON_PACKAGE_INDEX_URL = (
        "https://tensorflow.pypi.thoth-station.ninja/index/"
    )

    @classmethod
    def should_include(
        cls, context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Check if the given pipeline unit should be included in the given pipeline configuration."""
        raise NotImplemented(
            f"Please implement method to register pipeline unit {cls.__name__!r}to pipeline configuration"
        )

    @classmethod
    @contextmanager
    def assigned_context(cls, context: Context) -> Generator[None, None, None]:
        """Assign context to all units."""
        try:
            cls._context = context
            yield
        finally:
            cls._context = None

    @classmethod
    def compute_expanded_parameters(
        cls, parameters_dict: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute parameters as they would be computed based on unit configuration."""
        result = copy(cls.PARAMETERS_DEFAULT)

        if parameters_dict:
            result.update(parameters_dict)

        return result

    @_parameters.default
    def _initialize_default_parameters(self) -> Dict[str, Any]:
        """Initialize default parameters based on declared class' default parameters."""
        return copy(self.PARAMETERS_DEFAULT)

    @property
    def context(self) -> Context:
        """Get context in which the unit runs in."""
        if self._context is None:
            raise ValueError("Requesting pipeline context outside of pipeline run")
        return self._context

    @property
    def parameters(self) -> Dict[str, Any]:
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

    def update_parameters(self, parameters_dict: Dict[str, Any]) -> None:
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

    def to_dict(self) -> Dict[str, Any]:
        """Turn this pipeline step into its dictionary representation."""
        return {"name": self.__class__.__name__, "parameters": self.parameters}

    @classmethod
    def is_aicoe_release(cls, package_version: PackageVersion) -> bool:
        """Check if the given package-version is AICoE release."""
        return bool(
            package_version.index.url.startswith(cls._AICOE_PYTHON_PACKAGE_INDEX_URL)
        )

    @classmethod
    def get_aicoe_configuration(
        cls, package_version: PackageVersion
    ) -> Optional[Dict[str, Any]]:
        """Get AICoE specific configuration encoded in the AICoE index URL."""
        if not package_version.index.url.startswith(
            cls._AICOE_PYTHON_PACKAGE_INDEX_URL
        ):
            return None

        index_url = package_version.index.url[len(cls._AICOE_PYTHON_PACKAGE_INDEX_URL):]
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
            # TODO: We have dropped OS-specific builds, so this can go away in future releases...
            if conf_parts[0] != "os":
                _LOGGER.warning(
                    "Failed to parse operating system specific URL of AICoE index"
                )
                return None

            return {
                "os_name": conf_parts[1],
                "os_version": conf_parts[2],
                "configuration": conf_parts[3],
                "platform_tag": None,
            }

        _LOGGER.warning(
            "Failed to parse AICoE specific package source index configuration: %r",
            package_version.index.url,
        )
        return None
