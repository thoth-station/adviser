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

"""Limit number of latest versions considered when resolving software stacks.

This way we reduce number of nodes traversed in the graph traversal. This step has
to be run *after* the semver sorting step so that packages are sorted according to semver and before any
scoring (as score gets discarded).
"""

import logging

from ..step import Step
from ..step_context import StepContext
from thoth.adviser.python.dependency_graph import CannotRemovePackage

_LOGGER = logging.getLogger(__name__)


class LimitLatestVersions(Step):
    """Limit number of latest versions considered when resolving software stacks."""

    PARAMETERS_DEFAULT = {"limit_latest_versions": 5}

    def run(self, step_context: StepContext) -> None:
        """Remove old versions of dependencies, consider only desired count of latest versions.

        We traverse available paths horizontally and we check each package version in paths in the same column. If
        there are present more versions then the limit provided, paths with additional versions are discarded.
        A prerequisite for this function is to have paths sorted according to semver.
        """
        limit_latest_versions = self._parameters["limit_latest_versions"]

        if limit_latest_versions is None:
            _LOGGER.info("All versions considered")
            return

        if limit_latest_versions < 1:
            raise ValueError(
                "Number of latest versions has to be non-negative number bigger than 0, got %d",
                limit_latest_versions,
            )

        versions_seen = {}

        for package_version in reversed(list(step_context.iter_all_dependencies())):
            if package_version.name not in versions_seen:
                versions_seen[package_version.name] = 1

            if versions_seen[package_version.name] > limit_latest_versions:
                try:
                    with step_context.remove_package_tuples(
                        package_version.to_tuple()
                    ) as txn:
                        if len(txn.to_remove_nodes) > 1:
                            txn.rollback()
                        else:
                            txn.commit()
                except CannotRemovePackage as exc:
                    _LOGGER.debug(
                        f"Cannot remove package {package_version.to_tuple()}: {str(exc)}"
                    )
                    continue

            versions_seen[package_version.name] += 1
