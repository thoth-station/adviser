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

"""Adaptation of dependency graph based on scoring and package removals."""

import attr
from typing import List
from typing import Tuple
from typing import Dict
from typing import Union
from typing import Generator
from typing import Callable
from typing import Optional
import logging
from itertools import chain
from functools import cmp_to_key
from collections import deque
from collections import OrderedDict
from contextlib import contextmanager

from .elements import Edge
from .elements import Node
from .exceptions import CannotRemovePackage
from .exceptions import PackageNotFound
from .transaction import DependencyGraphTransaction


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class DependencyGraph:
    """A constructed dependency graph based on paths."""

    packages_map = attr.ib(
        type=Dict[Tuple[str, str, str], Node], default=attr.Factory(dict)
    )
    edges_map = attr.ib(
        type=Dict[Tuple[Optional[Tuple[str, str, str]], Tuple[str, str, str]], Edge],
        default=attr.Factory(OrderedDict),
    )
    direct_dependencies_map = attr.ib(
        type=Dict[Tuple[str, str, str], Node], default=attr.Factory(dict)
    )
    packages_score = attr.ib(
        type=Dict[Tuple[str, str, str], float], default=attr.Factory(dict)
    )

    @classmethod
    def from_paths(
        cls,
        direct_dependencies: List[Tuple[str, str, str]],
        paths: List[Tuple[Tuple[str, str, str], Tuple[str, str, str]]]
    ) -> "DependencyGraph":
        """Construct dependency graph from paths."""
        packages_map = {}
        edges_map = {}
        direct_dependency_map = {}

        if not direct_dependencies:
            raise ValueError("No direct dependencies specified")

        for direct_dependency in direct_dependencies:
            direct_dependency_node = packages_map.get(direct_dependency)
            if direct_dependency_node is None:
                direct_dependency_node = Node(direct_dependency)
                packages_map[direct_dependency_node.package_tuple] = direct_dependency_node

            if direct_dependency_node.package_tuple not in direct_dependency_map:
                direct_dependency_map[
                    direct_dependency_node.package_tuple
                ] = direct_dependency_node

            edge = edges_map.get((None, direct_dependency_node.package_tuple))
            if not edge:
                edge = Edge(source=None, target=direct_dependency_node)
                edges_map[edge.get_edge_key()] = edge
                direct_dependency_node.incoming_edges[None] = {}
                direct_dependency_node.incoming_edges[None][None] = edge

        for path in paths or []:
            if len(path) != 2:
                raise ValueError("Path does not carry source and destination")

            package_node1 = packages_map.get(path[0])
            if not package_node1:
                package_node1 = Node(path[0])
                packages_map[package_node1.package_tuple] = package_node1

            package_node2 = packages_map.get(path[1])
            if not package_node2:
                package_node2 = Node(path[1])
                packages_map[package_node2.package_tuple] = package_node2

            edge = edges_map.get(
                (package_node1.package_tuple, package_node2.package_tuple)
            )
            if edge is None:
                edge = Edge(source=package_node1, target=package_node2)
                edges_map[edge.get_edge_key()] = edge

            if package_node2.package_tuple[0] not in package_node1.outgoing_edges:
                package_node1.outgoing_edges[package_node2.package_tuple[0]] = {}

            if (
                package_node2.package_tuple
                not in package_node1.outgoing_edges[package_node2.package_tuple[0]]
            ):
                package_node1.outgoing_edges[package_node2.package_tuple[0]][
                        package_node2.package_tuple
                    ] = edge

            if package_node1.package_tuple[0] not in package_node2.incoming_edges:
                package_node2.incoming_edges[package_node1.package_tuple[0]] = {}

            if package_node1.package_tuple not in package_node2.incoming_edges[package_node1.package_tuple[0]]:
                package_node2.incoming_edges[package_node1.package_tuple[0]][package_node1.package_tuple] = edge

        return cls(
            packages_map=packages_map,
            edges_map=edges_map,
            direct_dependencies_map=direct_dependency_map,
            packages_score=dict.fromkeys(packages_map.keys(), 0.0),
        )

    def score_package_tuple(
        self, package_tuple: Tuple[str, str, str], score_adjustment: float
    ) -> None:
        """Adjust score of a package tuple in dependency graph to modify its precedence."""
        if package_tuple not in self.packages_map:
            raise PackageNotFound(
                f"No record for package {package_tuple} found in dependency graph"
            )

        for edges_dict in chain(
            self.packages_map[package_tuple].incoming_edges.values()
        ):
            for edge in edges_dict.values():
                edge.score += score_adjustment

    def to_scored_package_tuple_pairs(
        self
    ) -> List[
        Tuple[float, Tuple[Union[Tuple[str, str, str], None], Tuple[str, str, str]]]
    ]:
        """Construct pairs respecting package dependencies with corresponding score of these dependencies."""
        result = []

        for edge in self.edges_map.values():
            source_package_tuple = (
                edge.source.package_tuple if edge.source is not None else None
            )
            result.append(
                (edge.score, (source_package_tuple, edge.target.package_tuple))
            )

        return result

    @contextmanager
    def remove_package_tuples(
        self, *package_tuples: Tuple[str, str, str]
    ) -> DependencyGraphTransaction:
        """Remove a package from dependency graph, ensure the given package can be removed.

        This methods acts as a transaction - if any package from package tuples cannot be
        removed, it raises an exception and leaves the dependency graph untouched.
        """
        stack = deque()
        for package_tuple in package_tuples:
            package_node = self.packages_map.get(package_tuple)
            if package_node is None:
                raise PackageNotFound(
                    f"No record for package {package_tuple} found in dependency graph"
                )

            stack.append((package_node, package_node))

        all_to_remove_edges = {}
        all_to_remove_nodes = {}
        while stack:
            to_remove_node, requested_remove_node = stack.pop()

            if to_remove_node.package_tuple in all_to_remove_nodes:
                # Break cyclic dependencies.
                continue

            all_to_remove_nodes[to_remove_node.package_tuple] = to_remove_node

            for edge in to_remove_node.all_incoming_edges:
                all_to_remove_edges[edge.get_edge_key()] = edge

            for edge in to_remove_node.all_outgoing_edges:
                all_to_remove_edges[edge.get_edge_key()] = edge

            # Now check each parent has an alternative for the given package.
            direct_dependency_node = self.direct_dependencies_map.get(
                to_remove_node.package_tuple
            )
            if direct_dependency_node:
                # It's a direct dependency. Removing a direct dependency which has no
                # alternative causes invalidation of dependency graph for the given set of requirements.
                for direct_dependency_tuple in set(
                    self.direct_dependencies_map.keys()
                ) - set(all_to_remove_nodes.keys()):
                    if direct_dependency_tuple[0] == to_remove_node.package_tuple[0]:
                        # We have an alternative package - it's OK to remove the given package.
                        break
                else:
                    raise CannotRemovePackage(
                        f"Cannot remove package {requested_remove_node.package_tuple}, removing this package "
                        f"would cause invalidity in dependency graph as all direct dependencies of "
                        f"type {to_remove_node.package_tuple[0]!r} would be removed"
                    )
            else:
                for edge in to_remove_node.all_incoming_edges:
                    edges_considered = set(
                        e.get_edge_key()
                        for e in edge.source.outgoing_edges[
                            to_remove_node.package_tuple[0]
                        ].values()
                    )

                    if not edges_considered - set(all_to_remove_edges.keys()):
                        # We don't have any alternative for the removed package.
                        stack.append((edge.source, requested_remove_node))

        # Discard nodes and edges as one would traverse down the graph that are not
        # reachable anymore based on computed removals.
        change = True
        while change:
            change = False
            all_to_remove_package_tuples = set(all_to_remove_nodes.keys())

            for package_node in self.packages_map.values():
                if package_node.package_tuple in all_to_remove_nodes:
                    continue

                if package_node.package_tuple in self.direct_dependencies_map:
                    continue

                all_dependencies = set(package_node.all_dependency_package_tuples)
                if (
                    all_dependencies
                    and not all_dependencies - all_to_remove_package_tuples
                ):
                    all_to_remove_nodes[package_node.package_tuple] = package_node

                    for edge in package_node.all_outgoing_edges:
                        all_to_remove_edges[edge.get_edge_key()] = edge

                    for edge in package_node.all_incoming_edges:
                        all_to_remove_edges[edge.get_edge_key()] = edge

                    change = True
                    break

                for edge in package_node.all_outgoing_edges:
                    if edge.target.package_tuple in all_to_remove_edges:
                        all_to_remove_edges[edge.edge.get_edge_key()] = edge

            del all_to_remove_package_tuples

        yield DependencyGraphTransaction(
            self,
            to_remove_nodes=list(all_to_remove_nodes.values()),
            to_remove_edges=list(all_to_remove_edges.values()),
        )

    def perform_transaction(
        self, to_remove_nodes: List[Node], to_remove_edges: List[Edge]
    ) -> None:
        """Perform the actual transaction."""
        for package_tuple in set(node.package_tuple for node in to_remove_nodes):
            self.packages_map.pop(package_tuple)
            self.packages_score.pop(package_tuple)
            self.direct_dependencies_map.pop(package_tuple, None)

        for edge_key in set(e.get_edge_key() for e in to_remove_edges):
            edge = self.edges_map.pop(edge_key)

            # Unregister from source and target.
            if edge.source:
                source_name = edge.source.package_tuple[0]
                source_tuple = edge.source.package_tuple

                edge.source.outgoing_edges[edge.target.package_tuple[0]].pop(edge.target.package_tuple)
                if not edge.source.outgoing_edges[edge.target.package_tuple[0]]:
                    edge.source.outgoing_edges.pop(edge.target.package_tuple[0])
            else:
                source_name, source_tuple = None, None

            edge.target.incoming_edges[source_name].pop(source_tuple)
            if not edge.target.incoming_edges[source_name]:
                edge.target.incoming_edges.pop(source_name)

    def iter_transitive_dependencies_tuple(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Get all transitive dependencies found in dependency graph."""
        # Iterate over all edges and find those who have no starting node - these are packages
        # which came are present due to its dependency.
        package_tuples_seen = set()
        # Create list so that we can adjust dependency graph
        for edge in list(self.edges_map.values()):
            if (
                edge.source is not None
                and edge.target.package_tuple not in package_tuples_seen
            ):
                package_tuples_seen.add(edge.target.package_tuple)
                yield edge.target.package_tuple

    def iter_direct_dependencies_tuple(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over all direct dependencies."""
        yield from self.direct_dependencies_map.keys()

    def sort_paths(
        self,
        comparision_func: Callable[[Tuple[str, str, str], Tuple[str, str, str]], int],
        reverse: bool = True,
    ) -> None:
        """Sort paths in the dependency graph."""
        self.edges_map = OrderedDict(
            (e.get_edge_key(), e)
            for e in sorted(
                self.edges_map.values(),
                key=cmp_to_key(comparision_func),
                reverse=reverse,
            )
        )
