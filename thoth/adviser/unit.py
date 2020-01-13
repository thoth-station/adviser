#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union
from contextlib import contextmanager

import attr
from voluptuous import Schema
from thoth.python import PackageVersion

from .context import Context
from .dm_report import DependencyMonkeyReport

if TYPE_CHECKING:
    from .pipeline_builder import PipelineBuilderContext
    from .report import Report


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Unit(metaclass=abc.ABCMeta):
    """A base class for implementing pipeline units - strides and steps."""

    _configuration = attr.ib(type=Dict[str, Any], kw_only=True)
    _name = attr.ib(type=str, default=None, kw_only=True)

    _CONTEXT: Optional[Context] = None
    # Schema used to validate unit configuration - None value does not validate configuration.
    CONFIGURATION_SCHEMA: Schema = None
    CONFIGURATION_DEFAULT: Dict[str, Any] = {}

    _RE_CAMEL2SNAKE = re.compile("(?!^)([A-Z]+)")
    _AICOE_PYTHON_PACKAGE_INDEX_URL = (
        "https://tensorflow.pypi.thoth-station.ninja/index/"
    )

    @classmethod
    def should_include(
        cls, builder_context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Check if the given pipeline unit should be included in the given pipeline configuration."""
        raise NotImplemented(
            f"Please implement method to register pipeline unit {cls.__name__!r} to pipeline configuration"
        )

    @classmethod
    @contextmanager
    def assigned_context(cls, context: Context) -> Generator[None, None, None]:
        """Assign context to all units."""
        try:
            cls._CONTEXT = context
            yield
        finally:
            cls._CONTEXT = None

    @classmethod
    def compute_expanded_configuration(
        cls, configuration_dict: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute configuration as they would be computed based on unit configuration."""
        result = dict(cls.CONFIGURATION_DEFAULT)

        if configuration_dict:
            result.update(configuration_dict)

        return result

    @_configuration.default
    def _initialize_default_configuration(self) -> Dict[str, Any]:
        """Initialize default unit configuration based on declared class' default configuration."""
        return dict(self.CONFIGURATION_DEFAULT)

    @property
    def context(self) -> Context:
        """Get context in which the unit runs in."""
        if self._CONTEXT is None:
            raise ValueError("Requesting resolver context outside of resolver run")

        return self._CONTEXT

    @property
    def name(self) -> str:
        """Get name of this pipeline unit."""
        return self.__class__.__name__

    @property
    def configuration(self) -> Dict[str, Any]:
        """Get configuration of instantiated pipeline unit."""
        return self._configuration

    def update_configuration(self, configuration_dict: Dict[str, Any]) -> None:
        """Set configuration for a pipeline unit.

        If setting configuration fails due to schema checks, configuration are kept in an invalid state.
        """
        self.configuration.update(configuration_dict)
        if self.CONFIGURATION_SCHEMA:
            _LOGGER.debug("Validating configuration for pipeline unit %r", self.name)
            try:
                self.CONFIGURATION_SCHEMA(self.configuration)
            except Exception as exc:
                _LOGGER.exception(
                    "Failed to validate schema for pipeline unit %r: %s",
                    self.name,
                    str(exc),
                )
                raise

    def to_dict(self) -> Dict[str, Any]:
        """Turn this pipeline step into its dictionary representation."""
        return {"name": self.__class__.__name__, "configuration": self.configuration}

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

    def pre_run(self) -> None:
        """Called before running any pipeline unit with context already assigned.

        This method should not raise any exception.
        """

    def post_run(self) -> None:
        """Called after the resolution is finished.

        This method should not raise any exception.
        """

    def post_run_report(self, report: Union["Report", DependencyMonkeyReport]) -> None:
        """Post-run method run after the resolving has finished - this method is called only if resolving with a report.

        This method should not raise any exception.
        """
