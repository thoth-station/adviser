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

"""Cut off unsolved packages from dependency graph."""

import logging

from ..step import Step
from ..step_context import StepContext
from thoth.adviser.python.dependency_graph import CannotRemovePackage

_LOGGER = logging.getLogger(__name__)


class CutUnsolved(Step):
    """Cut off parts of dependency graph which are not yet solved - remove unsolved packages."""

    def run(self, step_context: StepContext) -> None:
        """Cut off parts of dependency graph which are not yet solved."""
        for unsolved_package in step_context.unsolved_packages.values():
            package_tuple = unsolved_package.to_tuple()
            if (
                package_tuple
                not in step_context.dependency_graph_adaptation.packages_map
            ):
                # Removed based on previous operations on dependency graph.
                continue

            try:
                with step_context.remove_package_tuples(package_tuple) as txn:
                    _LOGGER.info(
                        "Removing unsolved package from dependency graph: %r",
                        package_tuple,
                    )
                    txn.commit()
            except CannotRemovePackage as exc:
                _LOGGER.debug(
                    "Dependency graph is not fully resolved, error during removing package: %s",
                    package_tuple,
                    str(exc)
                )
                raise
