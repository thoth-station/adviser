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
from functools import cmp_to_key

from ..step import Step
from ..step_context import StepContext
from thoth.adviser.python.dependency_graph import CannotRemovePackage
from thoth.adviser.python.pipeline.units import semver_cmp_package_version

_LOGGER = logging.getLogger(__name__)


class ScoreCutoff(Step):
    """Cut off parts of dependency graph which have score bellow the given threshold."""

    PARAMETERS_DEFAULT = {"threshold": -0.1}

    def run(self, step_context: StepContext) -> None:
        """Cut off parts of dependency graph which have score bellow the given threshold."""
        _LOGGER.debug(
            "Threshold for score cut off set to %f", self.parameters["threshold"]
        )
        package_versions = sorted(
            step_context.iter_direct_dependencies(),
            key=cmp_to_key(semver_cmp_package_version),
            reverse=False,
        )

        for package_version in package_versions:
            package_tuple = package_version.to_tuple()
            if (
                package_tuple
                not in step_context.dependency_graph_adaptation.packages_map
            ):
                # Removed based on previous operations on dependency graph.
                continue

            if (
                step_context.dependency_graph_adaptation.packages_score[package_tuple]
                <= self.parameters["threshold"]
            ):
                try:
                    with step_context.remove_package_tuples(package_tuple) as txn:
                        any_positive = any(e.score > 0 for e in txn.to_remove_edges)
                        total_score = sum(e.score for e in txn.to_remove_edges)
                        if (
                            not any_positive
                            and total_score <= self.parameters["threshold"]
                        ):
                            _LOGGER.debug(
                                "Removing packages due to threshold (score %f): %r",
                                total_score,
                                list(txn.iter_package_tuples()),
                            )
                            txn.commit()
                        else:
                            _LOGGER.debug(
                                "Transaction has been rolled back for (score %f): %r",
                                total_score,
                                list(txn.iter_package_tuples()),
                            )
                            txn.rollback()
                except CannotRemovePackage as exc:
                    _LOGGER.debug(
                        "Failed to remove package tuple %s: %s", package_tuple, str(exc)
                    )
