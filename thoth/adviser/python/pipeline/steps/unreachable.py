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


"""Cut off unreachable dependencies - dependencies we know will never be resolved."""

import logging

from ..step import Step
from ..step_context import StepContext

_LOGGER = logging.getLogger(__name__)


class CutUnreachable(Step):
    """Cut off dependencies we know will never be resolved."""

    def run(self, step_context: StepContext) -> None:
        """Cut unreachable dependencies."""
        # Remove dependencies which are unreachable based on locked direct dependencies.
        direct_dependencies_map = {}
        for package_version in step_context.iter_direct_dependencies():
            if package_version.name not in direct_dependencies_map:
                direct_dependencies_map[package_version.name] = set()

            direct_dependencies_map[package_version.name].add(
                package_version.locked_version
            )

        for package_version in step_context.iter_transitive_dependencies():
            if (
                package_version.name in direct_dependencies_map
                and package_version.locked_version
                not in direct_dependencies_map[package_version.name]
            ):
                package_tuple = package_version.to_tuple()
                _LOGGER.debug(
                    "Removing package %r - unreachable based on direct dependencies",
                    package_tuple,
                )

                with step_context.remove_package_tuples(package_tuple) as txn:
                    txn.commit()
