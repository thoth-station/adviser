#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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

import abc
import logging
import os
import re
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Tuple
from typing import Union
from contextlib import contextmanager

import attr
from voluptuous import Schema
from voluptuous import Required
from voluptuous import Any as SchemaAny
from thoth.python import PackageVersion

from .context import Context
from .exceptions import ParseBaseImageError
from .exceptions import PipelineUnitConfigurationSchemaError
from .dm_report import DependencyMonkeyReport

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pipeline_builder import PipelineBuilderContext
    from .report import Report


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Unit(metaclass=abc.ABCMeta):
    """A base class for implementing pipeline units - strides and steps."""

    _CONTEXT: Optional[Context] = None
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): SchemaAny(str, None)})
    CONFIGURATION_DEFAULT: Dict[str, Any] = {"package_name": None}

    unit_run = attr.ib(type=bool, default=False, kw_only=True)
    _configuration = attr.ib(type=Dict[str, Any], kw_only=True)

    _RE_CAMEL2SNAKE = re.compile("(?!^)([A-Z]+)")
    _AICOE_PYTHON_PACKAGE_INDEX_URL = "https://tensorflow.pypi.thoth-station.ninja/index/"
    _VALIDATE_UNIT_CONFIGURATION_SCHEMA = bool(int(os.getenv("THOTH_ADVISER_VALIDATE_UNIT_CONFIGURATION_SCHEMA", 1)))
    _DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

    @classmethod
    def get_unit_name(cls) -> str:
        """Get name of the unit."""
        return cls.__name__

    @staticmethod
    def is_boot_unit_type() -> bool:
        """Check if the unit is of type boot."""
        return False

    @staticmethod
    def is_pseudonym_unit_type() -> bool:
        """Check if the unit is of type pseudonym."""
        return False

    @staticmethod
    def is_sieve_unit_type() -> bool:
        """Check if the unit is of type sieve."""
        return False

    @staticmethod
    def is_step_unit_type() -> bool:
        """Check if the unit is of type step."""
        return False

    @staticmethod
    def is_stride_unit_type() -> bool:
        """Check if the unit is of type step."""
        return False

    @staticmethod
    def is_wrap_unit_type() -> bool:
        """Check if the unit is of type wrap."""
        return False

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if the given pipeline unit should be included in the given pipeline configuration."""
        raise NotImplementedError(
            f"Please implement method to register pipeline unit {cls.get_unit_name()!r} to pipeline configuration"
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

    def __attrs_post_init__(self) -> None:
        """Initialize post-init attributes."""
        # Initialize unit_run always to False so the pipeline unit JSON report can be reused across
        # multiple pipeline unit runs.
        self.unit_run = False

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
        if self._VALIDATE_UNIT_CONFIGURATION_SCHEMA and self.CONFIGURATION_SCHEMA:
            _LOGGER.debug("Validating configuration for pipeline unit %r", self.name)
            try:
                self.CONFIGURATION_SCHEMA(self.configuration)
            except Exception as exc:
                _LOGGER.exception(
                    "Failed to validate schema for pipeline unit %r: %s",
                    self.name,
                    exc,
                )
                raise PipelineUnitConfigurationSchemaError(str(exc))

    def to_dict(self) -> Dict[str, Any]:
        """Turn this pipeline unit into its dictionary representation."""
        return {"name": self.name, "configuration": self.configuration, "unit_run": self.unit_run}

    @classmethod
    def is_aicoe_release(cls, package_version: PackageVersion) -> bool:
        """Check if the given package-version is AICoE release."""
        return bool(package_version.index.url.startswith(cls._AICOE_PYTHON_PACKAGE_INDEX_URL))

    @classmethod
    def get_aicoe_configuration(cls, package_version: PackageVersion) -> Optional[Dict[str, Any]]:
        """Get AICoE specific configuration encoded in the AICoE index URL."""
        if not package_version.index.url.startswith(cls._AICOE_PYTHON_PACKAGE_INDEX_URL):
            return None

        index_url = package_version.index.url[len(cls._AICOE_PYTHON_PACKAGE_INDEX_URL) :]
        conf_parts = index_url.strip("/").split("/")  # the last is always "simple"

        if len(conf_parts) == 3:
            # No OS specific release - e.g. manylinux compliant release.
            if not conf_parts[0].startswith("manylinux"):
                _LOGGER.error("Failed to parse a platform tag, unknown AICoE Index URL: %r", package_version.index.url)
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
                _LOGGER.error(
                    "Failed to parse operating system specific URL of AICoE index: %r", package_version.index.url
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

    @staticmethod
    def get_base_image(base_image: str, *, raise_on_error: bool = False) -> Optional[Tuple[str, str]]:
        """Return information about base image used."""
        parts = base_image.split(":", maxsplit=1)
        if len(parts) != 2:
            if raise_on_error:
                raise ParseBaseImageError(
                    f"Cannot determine Thoth s2i version information from {base_image}, "
                    "recommendations specific for ABI used will not be taken into account"
                )

            return None

        thoth_s2i_image_name, thoth_s2i_image_version = parts
        if thoth_s2i_image_version.startswith("v"):
            # Not nice as we always prefix with "v" but do not store it with "v" in the database
            # (based on env var exported and detected in Thoth's s2i).
            thoth_s2i_image_version = thoth_s2i_image_version[1:]

        return thoth_s2i_image_name, thoth_s2i_image_version

    def pre_run(self) -> None:  # noqa: D401
        """Called before running any pipeline unit with context already assigned.

        This method should not raise any exception.
        """
        self.unit_run = False

    def post_run(self) -> None:  # noqa: D401
        """Called after the resolution is finished.

        This method should not raise any exception.
        """

    def post_run_report(self, report):
        # type:('Unit', Union[Report, DependencyMonkeyReport]) -> None
        """Post-run method run after the resolving has finished - this method is called only if resolving with a report.

        This method should not raise any exception.
        """
