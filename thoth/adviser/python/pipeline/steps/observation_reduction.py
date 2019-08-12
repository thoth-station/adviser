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

"""A pipeline step which eliminates sub-graphs that have no observation or observation bellow threshold.

This way we (in most cases) significantly reduce number of traversed nodes in stack producer.
"""

import logging
from typing import List
from math import copysign
from collections import deque
from functools import cmp_to_key
from functools import partial

from thoth.adviser.python.pipeline.units import semver_cmp_package_version
from thoth.adviser.python.dependency_graph.adaptation.elements import Node
from thoth.adviser.python.dependency_graph import CannotRemovePackage
from thoth.adviser.python.dependency_graph import PackageNotFound

from ..step import Step
from ..step_context import StepContext

_LOGGER = logging.getLogger(__name__)


class ObservationReduction(Step):
    """Remove not scored sub-graphs which do not observations or they have observations bellow threshold."""

    PARAMETERS_DEFAULT = {"score_threshold": 0.0}

    @staticmethod
    def _sort_nodes_score_semver(step_context: StepContext, node1: Node, node2: Node) -> int:
        """Sort nodes based on score of packages which they represent and based on semver (secondary sorting key)."""
        score1 = step_context.dependency_graph_adaptation.packages_score[node1.package_tuple]
        score2 = step_context.dependency_graph_adaptation.packages_score[node2.package_tuple]

        if score1 != score2:
            return int(copysign(1, score1 - score2))

        package_version1 = step_context.packages[node1.package_tuple]
        package_version2 = step_context.packages[node2.package_tuple]

        return semver_cmp_package_version(package_version1, package_version2)

    @classmethod
    def _sorted_dependencies(cls, step_context: StepContext, node: Node) -> List[Node]:
        """Return sorted dependencies of the package version stored in the node."""
        dependency_nodes = (edge.target for edge in node.all_outgoing_edges)
        return sorted(
            dependency_nodes,
            key=cmp_to_key(partial(cls._sort_nodes_score_semver, step_context)),
            reverse=True,
        )

    def run(self, step_context: StepContext) -> None:
        """Remove sub-graphs based on score threshold."""
        queue = deque(sorted(
            step_context.dependency_graph_adaptation.direct_dependencies_map.values(),
            key=cmp_to_key(partial(self._sort_nodes_score_semver, step_context)),
            reverse=True,
        ))

        seen = set()
        while queue:
            node = queue.pop()
            package_tuple = node.package_tuple

            if package_tuple in seen or package_tuple not in step_context.packages:
                # Break cycles, skip already removed packages from dependency graph.
                continue

            seen.add(package_tuple)

            try:
                with step_context.remove_package_tuples(package_tuple) as txn:
                    if txn.any_positive_score():
                        # Get all the dependent and append them to the queue to have them processed
                        # in the correct order (top levels first).
                        queue.extend(self._sorted_dependencies(step_context, node))
                        txn.rollback()
                    else:
                        _LOGGER.debug(
                            "Removing sub-graph as no positive observations were found: %r",
                            list(txn.iter_package_tuples())
                        )
                        txn.commit()
            except PackageNotFound as exc:
                _LOGGER.debug(
                    "Package %r was removed by one of the previous sub-graph removals: %s",
                    package_tuple,
                    str(exc)
                )
            except CannotRemovePackage as exc:
                _LOGGER.debug("Cannot remove sub-graph, queing dependencies for sub-graph removals: %s", str(exc))
                queue.extend(self._sorted_dependencies(step_context, node))
