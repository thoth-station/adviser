#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""A sieve to filter out packages based on constraints supplied."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion
from packaging.specifiers import SpecifierSet
from packaging.markers import Marker
from voluptuous import Schema
from voluptuous import Required

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class ConstraintsSieve(Sieve):
    """A sieve to filter out packages based on constraints supplied."""

    CONFIGURATION_DEFAULT = {"package_name": None}
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): str, "specifier": str})
    _JUSTIFICATION_LINK = jl("constraints")

    packages_seen = attr.ib(type=Set[Tuple[str, str, str]], default=attr.Factory(set), init=False)
    specifier_set = attr.ib(type=SpecifierSet, default=attr.Factory(SpecifierSet), init=False)

    @classmethod
    def default_environment(cls, builder_context: "PipelineBuilderContext") -> Dict[str, str]:
        """Get environment for markers based on runtime environment configuration supplied."""
        return {
            # Not present ones based on the default environment created by packaging:
            "platform_release": "",
            "platform_version": "",
            "python_full_version": f"{builder_context.project.runtime_environment.python_version}.0",
            "implementation_name": "cpython",
            "os_name": "posix",
            "platform_machine": "x86_64",
            "platform_python_implementation": "CPython",
            "platform_system": "Linux",
            "python_version": builder_context.project.runtime_environment.python_version,
            "implementation_version": f"{builder_context.project.runtime_environment.python_version}.0",
            "sys_platform": "linux",
        }

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Enable this pipeline unit if the adjustment is enabled."""
        if builder_context.is_included(cls):
            yield from ()
            return None

        if not builder_context.project.constraints or not builder_context.project.constraints.package_versions:
            _LOGGER.debug("No constraints defined, not registering constraint sieve unit")
            yield from ()
            return None

        if builder_context.project.runtime_environment.python_version is None:
            _LOGGER.warning(
                "No Python version specified in the runtime environment, not registering constraints sieve unit"
            )
            yield from ()
            return None

        marker_default_environment = cls.default_environment(builder_context)

        for package_version in builder_context.project.constraints.package_versions.values():
            if package_version.markers:
                marker_instance = Marker(package_version.markers)
                marker_evaluation_result = marker_instance.evaluate(environment=marker_default_environment)
                if not marker_evaluation_result:
                    _LOGGER.warning(
                        "Skipping constraint on %r as marker does not apply to the environment %r",
                        package_version.name,
                        package_version.markers,
                    )
                    continue

            yield {"package_name": package_version.name, "specifier": package_version.version}

    def pre_run(self) -> None:
        """Initialize this pipeline unit before any resolution run."""
        self.packages_seen.clear()
        specifier = self.configuration.get("specifier")
        self.specifier_set = SpecifierSet(specifier if specifier not in ("*", None) else "")
        # Explicitly turn on pre-releases here, as pre-releases are handled by a different pipeline unit.
        self.specifier_set.prereleases = True
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Cut-off packages that do not meet desired specifier in constraints."""
        for package_version in package_versions:
            if package_version.locked_version in self.specifier_set:
                yield package_version
                continue

            package_tuple = package_version.to_tuple()
            if package_tuple not in self.packages_seen:
                self.packages_seen.add(package_tuple)
                msg = f"Removing package {package_tuple} based on constraint {str(self.specifier_set)!r}"
                _LOGGER.info("%s - see %s", msg, self._JUSTIFICATION_LINK)
                self.context.stack_info.append(
                    {
                        "type": "INFO",
                        "message": msg,
                        "link": self._JUSTIFICATION_LINK,
                    }
                )
