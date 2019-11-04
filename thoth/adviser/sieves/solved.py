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

"""A sieve for filtering out build time/installation errors of Python packages."""

import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from thoth.storages.exceptions import NotFoundError

from ..exceptions import NotAcceptable
from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SolvedSieve(Sieve):
    """Filter out build time/installation errors of Python packages."""

    PARAMETERS_DEFAULT = {"without_error": True}

    @classmethod
    def should_include(
        cls, context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Include solved pipeline sieve for adviser or Dependency Monkey on pipeline creation."""
        if not context.is_included(cls):
            return {}

        return None

    def run(self, package_version: PackageVersion) -> None:
        """Filter out packages based on build time/installation issues.."""
        environment = {
            "os_name": self.project.runtime_environment.operating_system.name,
            "os_version": self.project.runtime_environment.operating_system.version,
            "python_version": self.project.runtime_environment.python_version,
        }

        try:
            has_error = self.graph.has_python_solver_error(
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
                **environment,
            )
        except NotFoundError as exc:
            raise NotAcceptable(
                f"Removing package {package_version.to_tuple()!r} as it was not solved: {str(exc)!r}"
            )

        if has_error and self.parameters["without_error"]:
            raise NotAcceptable(
                f"Removing package {package_version.to_tuple()!r} due to build time error on {environment!r}"
            )

        return None
