#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
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
from typing import Set
from typing import Union

from itertools import chain
from collections import deque


class DependencyGraphAdaptationException(Exception):
    """A top-class exception in dependency graph hierarchy."""


class CannotRemovePackage(DependencyGraphAdaptationException):
    """Raised if the given package cannot be removed."""


class PackageNotFound(DependencyGraphAdaptationException):
    """Raised if the given package cannot be removed."""


@attr.s(slots=True)
class _Node:
    """A node in constructed dependency graph."""

    package_tuple = attr.ib(type=Tuple[str, str, str])
    # A key to first dictionary is package name or None if an "edge" to direct dependency,
    # the subsequent key to next dictionary is a package tuple (package name, package version,
    # index url) which points to the edge.
    incoming_edges = attr.ib(
        type=Dict[Union[Tuple[str, str, str], None], Dict[Union[Tuple, None], "_Edge"]],
        default=attr.Factory(dict)
    )
    outgoing_edges = attr.ib(
        type=Dict[Union[Tuple[str, str, str], None], Dict[Union[Tuple, None], "_Edge"]],
        default=attr.Factory(dict)
    )


@attr.s(slots=True)
class _Edge:
    """An edge in dependency graph which is weighted (weight is score)."""

    source = attr.ib(type=Union[_Node, None])
    target = attr.ib(type=_Node)
    score = attr.ib(type=float, default=0.0)

    def get_edge_key(self) -> Tuple[Union[Tuple[str, str, str], None], Tuple[str, str, str]]:
        """Get key which identifies edge."""
        return self.source.package_tuple if self.source is not None else None, self.target.package_tuple


@attr.s(slots=True)
class DependencyGraph:
    """A constructed dependency graph based on paths."""

    packages_map = attr.ib(
        type=Dict[Tuple[str, str, str], _Node],
        default=attr.Factory(dict)
    )
    edges_map = attr.ib(
        type=Dict[Union[Tuple[Tuple[str, str, str], None], Tuple[str, str, str]], _Edge],
        default=attr.Factory(Dict),
    )
    direct_dependencies_map = attr.ib(
        type=Dict[Tuple[str, str, str], _Node],
        default=attr.Factory(dict),
    )

    @classmethod
    def from_paths(cls, paths: List[List[Tuple[str, str, str]]]) -> "DependencyGraph":
        """Construct dependency graph from paths."""
        packages_map = {}
        edges_map = {}
        direct_dependency_map = {}

        for path in paths:
            if not path:
                raise ValueError("Empty path supplied")

            direct_dependency = packages_map.get(path[0])
            if direct_dependency is None:
                direct_dependency = _Node(path[0])
                packages_map[direct_dependency.package_tuple] = direct_dependency

            if direct_dependency.package_tuple not in direct_dependency_map:
                direct_dependency_map[direct_dependency.package_tuple] = direct_dependency

            previous = None
            for package_tuple in path:
                package_node = packages_map.get(package_tuple)

                if not package_node:
                    package_node = _Node(package_tuple)
                    packages_map[package_tuple] = package_node

                previous_package_tuple = previous.package_tuple if previous is not None else None
                previous_package_name = previous_package_tuple[0] if previous_package_tuple else None

                edge = edges_map.get((previous_package_tuple, package_node.package_tuple))
                if edge is None:
                    edge = _Edge(source=previous, target=package_node)
                    edges_map[edge.get_edge_key()] = edge

                if previous:
                    if package_node.package_tuple[0] not in previous.outgoing_edges:
                        previous.outgoing_edges[package_node.package_tuple[0]] = {}

                    if package_node.package_tuple not in previous.outgoing_edges[package_node.package_tuple[0]]:
                        previous.outgoing_edges[package_node.package_tuple[0]][package_node.package_tuple] = edge

                if previous_package_name not in package_node.incoming_edges:
                    package_node.incoming_edges[previous_package_name] = []

                if edge.get_edge_key() not in package_node.incoming_edges[previous_package_name]:
                    package_node.incoming_edges[previous_package_name].append(edge.get_edge_key())

                previous = package_node

        return cls(
            packages_map=packages_map,
            edges_map=edges_map,
            direct_dependencies_map=direct_dependency_map,
        )

    def score_package_tuple(
            self,
            package_tuple: Tuple[str, str, str],
            score_adjustment: float
    ) -> None:
        """Adjust score of a package tuple in dependency graph to modify its precedence."""
        if package_tuple not in self.packages_map:
            raise PackageNotFound(
                f"No record for package {package_tuple} found in dependency graph"
            )

        for edge_tuples in chain(self.packages_map[package_tuple].incoming_edges.values()):
            for edge_tuple in edge_tuples:
                self.edges_map[edge_tuple].score += score_adjustment

    def to_scored_package_tuple_pairs(
            self
    ) -> List[Tuple[float, Tuple[Union[Tuple[str, str, str], None], Tuple[str, str, str]]]]:
        """Construct pairs respecting package dependencies with corresponding score of these dependencies."""
        result = []

        for edge in self.edges_map.values():
            source_package_tuple = edge.source.package_tuple if edge.source is not None else None
            result.append((edge.score, (source_package_tuple, edge.target.package_tuple)))

        return result

    def remove_package_tuple(self, package_tuple: Tuple[str, str, str]) -> None:
        """Remove a single package tuple from dependency graph."""
        # This is just sugar, syntax sugar...
        return self.remove_package_tuples({package_tuple})

    def remove_package_tuples(
            self
            ,
            package_tuples: Set[Tuple[str, str, str]]
    ) -> None:
        """Remove a package from dependency graph, ensure the given package can be removed.

        This methods acts as a transaction - if any package from package tuples cannot be
        removed, it raises an exception and leaves the dependency graph untouched.
        """
        stack = deque()
        for package_tuple in package_tuples:
            package_node = self.packages_map.get(package_tuple)
            if package_node is None:
                raise PackageNotFound(f"No record for package {package_tuple} found in dependency graph")

            stack.append((package_node, package_node))

        all_to_remove_edges = {}
        all_to_remove_nodes = {}
        while stack:
            to_remove_node, requested_remove_node = stack.pop()

            if to_remove_node.package_tuple in all_to_remove_nodes:
                # Break cyclic dependencies.
                continue

            all_to_remove_nodes[to_remove_node.package_tuple] = to_remove_node

            for edge_keys in chain(to_remove_node.incoming_edges.values()):
                for edge_key in edge_keys:
                    all_to_remove_edges[edge_key] = self.edges_map[edge_key]

            # Now check each parent has an alternative for the given package.
            direct_dependency_node = self.direct_dependencies_map.get(to_remove_node.package_tuple)
            if direct_dependency_node:
                # It's a direct dependency. Removing a direct dependency which has no
                # alternative causes invalidation of dependency graph for the given set of requirements.
                for direct_dependency_tuple in set(self.direct_dependencies_map.keys()) - set(all_to_remove_nodes.keys()):
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
                for incoming_edges in to_remove_node.incoming_edges.values():
                    for edge_tuple in incoming_edges:
                        edge = self.edges_map[edge_tuple]
                        edges_considered = set(e.get_edge_key() for e in edge.source.outgoing_edges[to_remove_node.package_tuple[0]].values())
                        if not edges_considered - set(all_to_remove_edges.keys()):
                            # We don't have any alternative for the removed package.
                            for edge_tuple in incoming_edges:
                                edge = self.edges_map[edge_tuple]
                                stack.append((edge.source, requested_remove_node))

        for package_tuple in all_to_remove_nodes:
            self.packages_map.pop(package_tuple)
            if package_tuple in self.direct_dependencies_map:
                self.direct_dependencies_map.pop(package_tuple)

        for edge in all_to_remove_edges.values():
            if edge.source is not None:
                edge.source.outgoing_edges[edge.target.package_tuple[0]].pop(edge.target.package_tuple)
                if not edge.source.outgoing_edges[edge.target.package_tuple[0]]:
                    edge.source.outgoing_edges.pop(edge.target.package_tuple[0])

                # edge.target.incoming_edges[edge.source.package_tuple[0]].remove(edge)
                # if not edge.target.incoming_edges[edge.source.package_tuple[0]]:
                #     edge.target.incoming_edges.pop(edge.source.package_tuple[0])
            else:
                pass
                # edge.target.incoming_edges.pop(None)

            self.edges_map.pop(edge.get_edge_key())

        # FIXME: we could optimize this and check if can get removed dependencies up the dependency tree
        stack = deque(self.direct_dependencies_map.values())
        package_tuple_visited = set()
        while stack:
            package_node = stack.pop()
            package_tuple_visited.add(package_node.package_tuple)

            for outgoing_edge_dict in package_node.outgoing_edges.values():
                for outgoing_edge in outgoing_edge_dict.values():
                    if outgoing_edge.target.package_tuple not in package_tuple_visited:
                        stack.append(outgoing_edge.target)

        to_remove = []
        for edge in self.edges_map.values():
            if edge.source and edge.source.package_tuple not in package_tuple_visited:
                to_remove.append(edge.get_edge_key())

        for edge_to_remove in to_remove:
            self.edges_map.pop(edge_to_remove)
