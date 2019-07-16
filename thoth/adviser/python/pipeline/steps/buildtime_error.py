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

"""Filter out stacks which have buildtime errors."""

import logging

from thoth.adviser.python.exceptions import UnableLock
from thoth.adviser.python.dependency_graph import CannotRemovePackage

from ..step_context import StepContext
from ..step import Step

_LOGGER = logging.getLogger(__name__)


class BuildtimeErrorFiltering(Step):
    """Filtering of stacks which have errors."""

    def run(self, step_context: StepContext) -> None:
        """Filter out packages which have buildtime errors."""
        for package_tuple in step_context.iter_all_dependencies_tuple():
            has_error = self.graph.has_python_solver_error(
                package_name=package_tuple[0],
                package_version=package_tuple[1],
                index_url=package_tuple[2],
                os_name=self.project.runtime_environment.operating_system.name,
                os_version=self.project.runtime_environment.operating_system.version,
                python_version=self.project.runtime_environment.python_version,
            )
            if has_error:
                _LOGGER.debug("Removing package %s due to build time error", package_tuple)
                try:
                    with step_context.remove_package_tuples(package_tuple) as txn:
                        txn.commit()
                except CannotRemovePackage as exc:
                    _LOGGER.error("Cannot produce stack: %s", str(exc))
                    raise
