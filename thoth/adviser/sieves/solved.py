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

"""A sieve for filtering out build time/installation errors of Python packages."""

import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from thoth.storages.exceptions import NotFoundError

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SolvedSieve(Sieve):
    """Filter out build time/installation errors of Python packages."""

    CONFIGURATION_DEFAULT = {"without_error": True}

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include solved pipeline sieve for adviser or Dependency Monkey on pipeline creation."""
        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out packages based on build time/installation issues.."""
        for package_version in package_versions:
            try:
                has_error = self.context.graph.has_python_solver_error(
                    package_version.name,
                    package_version.locked_version,
                    package_version.index.url,
                    os_name=self.context.project.runtime_environment.operating_system.name,
                    os_version=self.context.project.runtime_environment.operating_system.version,
                    python_version=self.context.project.runtime_environment.python_version,
                )
            except NotFoundError as exc:
                _LOGGER.debug(
                    "Removing package %r as it was not solved: %s", package_version.to_tuple(), str(exc),
                )
                continue

            if has_error and self.configuration["without_error"]:
                _LOGGER.debug(
                    "Removing package %r due to build time error in the software environment",
                    package_version.to_tuple(),
                )
                continue

            yield package_version
