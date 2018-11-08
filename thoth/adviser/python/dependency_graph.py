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

"""In-memory N-ary dependency graph used for traversing software stacks.

As number of possible software stacks can be really huge, let's construct
N-ary dependency graph in-memory and traverse it to generate software stacks.
These software stacks are used in dependency-monkey (see seed randomly
selecting possible software stacks) as well as in recommendations where this
dependency graph is traversed to generate possible software stacks that are
subsequently scored.

A node in this graph is PackageVersion. The graph can be seen as N-ary tree,
but as there can be cyclic deps in the Python ecosystem, we need to consider
cycles (see caching).
"""

import typing
import logging
from collections import deque
from functools import reduce
from itertools import chain
from itertools import chain
from itertools import product
import operator

import attr

from .package_version import PackageVersion
from .pipfile import PipfileMeta
from .project import Project
from .solver import PythonPackageGraphSolver
from ..exceptions import ConstraintClashError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class GraphItem:
    """Extend PackageVersion with a link to resolved dependencies of the given package version."""

    package_version = attr.ib(type=PackageVersion)
    dependencies = attr.ib(default=attr.Factory(dict))

    def is_package_version(self, package_name: str, package_version: str, index: str):
        """Check if the given package-version entry has given attributes."""
        return self.package_version.name == package_name and 
            self.package_version.version == '==' + package_version and \
            self.package_version.index == index

    def is_different_version(self, package_name: str, package_version: str, index: str):
        """Check if same package but under a different version."""
        return self.package_version.name == package_name and \
            self.package_version.version != '==' + package_version and \
            self.package_version.index == index


@attr.s(slots=True)
class DependencyGraph:
    """N-ary dependency graph stored in memory."""

    direct_dependencies = attr.ib(type=dict)
    meta = attr.ib(type=PipfileMeta)
    dependencies_map = attr.ib(type=dict)

    @property
    def stacks_estimated(self) -> int:
        """Estimate number of sofware stacks we could end up with (the upper boundary)."""
        # We could estimate based on traversing the tree, it would give us better, but still rough estimate.
        return reduce(lambda a, b: a * b, (len(v) for v in self.dependencies_map.values()))

    @staticmethod
    def _prepare_direct_dependencies(solver: PythonPackageGraphSolver, project: Project,
                                     with_devel: bool) -> typing.List[typing.List[GraphItem]]:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        # TODO: Sort dependencies to have stable generations for same stacks.
        # It's important that solver preserves order in which packages were inserted.
        # This is also a requirement for running under Python3.6+!!!
        _LOGGER.debug("Resolving direct dependencies")
        resolved_direct_dependencies = solver.solve(
            list(project.iter_dependencies(with_devel=with_devel)),
            graceful=False,
            all_versions=True
        )

        direct_dependencies_map = {}
        dependencies_map = {}
        for package_name, package_versions in resolved_direct_dependencies.items():
            dependencies_map[package_name] = []
            for package_version in package_versions:
                graph_item = GraphItem(package_version=package_version)

                if package_version.name not in direct_dependencies_map:
                    direct_dependencies_map[package_version.name] = {}

                direct_dependencies_map[package_version.name][package_version.locked_version] = graph_item
                dependencies_map[package_name].append(graph_item)

        # dependencies_map maps package_name to a list of GraphItem objects
        # direct_dependencies_map maps package_name,package_version to GraphItem object
        return dependencies_map, direct_dependencies_map

    @classmethod
    def from_project(cls, project: Project, with_devel: bool = False):
        """Construct a dependency graph from a project."""
        # Place the import statement here to simplify mocks in the testsuite.
        from thoth.storages.graph.janusgraph import GraphDatabase

        graph = GraphDatabase()
        graph.connect()
        solver = PythonPackageGraphSolver(graph_db=graph)
        direct_dependencies, dependencies_map = cls._prepare_direct_dependencies(
            solver,
            project,
            with_devel=with_devel
        )

        # Now perform resolution on all the transitive dependencies.
        all_direct_dependencies = list(chain(*direct_dependencies.values()))
        for graph_item in all_direct_dependencies:
            # Example response:
            # [
            #   # Example entry:
            #   [
            #     {'package': 'tensorflow', 'version': '1.1.0', index='..'},
            #     {'depends_on': '>=1.11.0'},
            #     {'package': 'numpy', 'version': '1.14.2', index='..'}
            #   ],
            #    ...
            # ]
            _LOGGER.debug(
                "Retrieving transitive dependencies for %r in version %r from %r",
                graph_item.package_version.name, graph_item.package_version.locked_version,
                graph_item.package_version.index
            )
            transitive_dependencies = graph.retrieve_transitive_dependencies_python(
                graph_item.package_version.name,
                graph_item.package_version.locked_version,
                graph_item.package_version.index
            )

            # Fast path - filter out paths that have a version of a direct
            # dependency in it that does not correspond to the direct
            # dependency. This way we can filter out a lot of nodes in the graph and reduce walks.
            transitive_dependencies_to_include = []
            for entry in transitive_dependencies:
                exclude = False
                for idx in range(0, len(entry), 2):
                    item = entry[idx]
                    direct_packages_of_this = [
                        dep for dep in all_direct_dependencies if dep.package_version.name == item['package'] and \
                        dep.package_version.index is None
                    ]

                    if not direct_packages_of_this:
                        continue

                    if any(dep.is_package_version(item['package'], item['version'], None)
                           for dep in direct_packages_of_this):
                        continue

                    # Otherwise do not include it - cut off the un-reachable dependency graph.
                    _LOGGER.debug(
                        "Excluding a path due to package %s (unreachable based on direct dependencies)", item
                    )
                    exclude = True
                    break

                if not exclude:
                    transitive_dependencies_to_include.append(entry)

            # There are transitive dependencies, but we were not able to construct dependency graph
            # with given constraints (e.g. there is always dependency on protobuf, but we asked to remove protobuf).
            if transitive_dependencies and not transitive_dependencies_to_include:
                raise ConstraintClashError("Unable to create a dependency graph for the given set of constraints")

            for entry in transitive_dependencies_to_include:
                # TODO: we have captured only one layer.
                #
                # Name graph-query dependent results.
                # TODO: add index
                source_name, source_version, source_index = \
                    entry[0]['package'], entry[0]['version'], None
                destination_name, destination_version, destination_index = \
                    entry[2]['package'], entry[2]['version'], None

                # If this fails on key error, the returned query from graph
                # does not preserve order of nodes visited (it should).
                source = dependencies_map[source_name][source_version]

                # TODO: same package name on different index?
                destination = dependencies_map.get(destination_name, {}).get(destination_version)

                if not destination:
                    # First time seen.
                    new_package_version = PackageVersion(
                        name=destination_name,
                        version='==' + destination_version,
                        index=destination_index,
                        hashes=[],
                        develop=source.package_version.develop
                    )

                    destination = GraphItem(package_version=new_package_version)

                    if destination_name not in dependencies_map:
                        dependencies_map[destination_name] = {}

                    dependencies_map[destination_name][destination_version] = destination

                if destination_name not in source.dependencies:
                    source.dependencies[destination_name] = []

                source.dependencies[destination_name].append(destination)

        return cls(
            direct_dependencies,
            meta=project.pipfile.meta,
            dependencies_map=dependencies_map
        )

    @staticmethod
    def _is_final_state(state: tuple) -> bool:
        """Check if the given configuration in the traversal is final - meaning all dependencies were satisfied."""
        expanded, to_expand = state[0], state[1]

        for item in to_expand:
            if item.package_version.name not in expanded:
                return False

            if item.package_version.locked_version != expanded[item.package_version.name].locked_version:
                # It's not final state and it is not a valid state as well -
                # this can occur in case of cyclic deps.
                return False

        return True

    @staticmethod
    def _is_valid_state(expanded: typing.Dict[str, GraphItem], new_expanded: typing.List[GraphItem]) -> bool:
        """Check if the given configuration is valid (not necessary final); meaning itrespects resolution."""
        for item in new_expanded:
            if item.package_version.name not in expanded:
                # This package was not seen in the application stack =>
                # whatever version it will be installed in is OK as other
                # packages do not depend on it.
                continue

            if expanded[item.package_version.name].package_version.locked_version  \
                    != item.package_version.locked_version:
                # The previous resolution included this package in different
                # version, we cannot include this package to the stack =>
                # invalid software stack.
                return False

        # Nothing suspicious so far :)
        return True

    def walk(self, decision_function: typing.Callable = None) -> typing.Generator[Project, None, None]:
        """Generate software stacks based on traversing the dependency graph.

        @param decision_function: function used to filter out stacks (False - omit stack, True include stack),
            used for sampling avoiding generating all the possible software stacks
        @return: a generator, each item yielded value is one option of a resolved software stack
        """
        # The implementation is very lazy (using generators where possible), more lazy then the author himself...
        def always_true_decision_function(_):
            # Always generate all, if not stated otherwise.
            return True

        decision_function = decision_function or always_true_decision_function
        stack = deque()

        _LOGGER.info("Estimated number of software stacks: %d (the upper boundary)", self.stacks_estimated)

        # Initial configuration picks the latest versions first (they are last on the stack):
        configurations = product(*(range(len(i)) for i in self.direct_dependencies.values()))
        for configuration in configurations:
            filtering_values = (operator.itemgetter(i) for i in configuration)
            to_expand = tuple(map(lambda i: i[0](i[1]), zip(filtering_values, self.direct_dependencies.values())))
            if self._is_valid_state({}, to_expand):
                stack.append(({}, to_expand))

        while stack:
            state = stack.pop()

            if self._is_final_state(state):
                if decision_function((graph_item.package_version for graph_item in state[0])):
                    package_versions = tuple(g.package_version for g in state[0].values())
                    _LOGGER.debug("Yielding newly created project from state: %r", state[0])
                    yield Project.from_package_versions(
                        packages=package_versions,
                        packages_locked=package_versions,
                        meta=self.meta
                    )
                else:
                    _LOGGER.debug("Decision function excluded stack %r", state[0])

                continue

            # Construct a list of dictionaries containing mapping for each dependency (a list of transitive deps):
            #   { package_name: List[GraphItem] }
            _LOGGER.debug("Expanding transitive dependencies for a stack candidate: %r", state)
            transitive_dependencies = []
            for dependency in state[1]:
                transitive_dependencies.append(dependency.dependencies)

            all_transitive_dependencies = tuple(chain.from_iterable(td.values() for td in transitive_dependencies))

            configurations = product(*(range(len(i)) for i in all_transitive_dependencies))
            for configuration in configurations:
                filtering_values = (operator.itemgetter(i) for i in configuration)
                to_expand = tuple(map(lambda i: i[0](i[1]), zip(filtering_values, all_transitive_dependencies)))

                new_expanded = dict(state[0])
                new_expanded.update({g.package_version.name: g for g in state[1]})

                if self._is_valid_state(new_expanded, to_expand):
                    _LOGGER.debug("A valid state to be expanded (%r, %r)", new_expanded, to_expand)
                    stack.append((
                        new_expanded,
                        to_expand
                    ))
                else:
                    _LOGGER.debug("Not a valid state (%r, %r)", new_expanded, to_expand)
