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
from collections import deque
from itertools import chain
from itertools import chain
from itertools import product
import operator

import attr

from .package_version import PackageVersion
from .pipfile import PipfileMeta
from .project import Project
from .solver import PythonPackageGraphSolver


@attr.s(slots=True)
class GraphItem:
    """Extend PackageVersion with a link to resolved dependencies of the given package version."""

    package_version = attr.ib(type=PackageVersion)
    dependencies = attr.ib(default=attr.Factory(dict))


@attr.s(slots=True)
class DependencyGraph:
    """N-ary dependency graph stored in memory."""

    direct_dependencies = attr.ib(type=dict)
    _meta = attr.ib(type=PipfileMeta, default=None)

    @staticmethod
    def _prepare_direct_dependencies(solver: PythonPackageGraphSolver, project: Project,
                                     with_devel: bool) -> typing.List[typing.List[GraphItem]]:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        # TODO: Sort dependencies to have stable generations for same stacks.
        # It's important that solver preserves order in which packages were inserted.
        # This is also a requirement for running under Python3.6+!!!
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
        solver = PythonPackageGraphSolver(graph_db=graph)
        direct_dependencies, dependencies_map = cls._prepare_direct_dependencies(
            solver,
            project,
            with_devel=with_devel
        )

        # Now perform resolution on all the transitive dependencies.
        # TODO: check that the graph query used breaks cyclic dependencies as expected.
        for graph_item in chain(*direct_dependencies.values()):
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
            transitive_dependencies = graph.retrieve_transitive_dependencies_python(
                graph_item.package_version.name,
                graph_item.package_version.locked_version,
                graph_item.package_version.index
            )

            for entry in transitive_dependencies:
                # Name graph-query dependent results.
                source_name, source_version, source_index = \
                    entry[0]['package_name'], entry[0]['version'], entry[0]['index']
                destination_name, destination_version, destination_index = \
                    entry[2]['package_name'], entry[2]['version'], entry[0]['index']

                # If this fails on key error, the returned query from graph
                # does not preserve order of nodes visited (it should).
                source = dependencies_map[source_name][source_version]

                # TODO: same package name on different index?
                destination = dependencies_map.get(destination_name, {}).get(destination_version)

                if not destination:
                    # First time seen.
                    new_package_version = PackageVersion(
                        name=destination_name,
                        version=destination_version,
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

        return cls(direct_dependencies, _meta=project.pipfile.meta)

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

            if expanded[item.package_version.name].locked_version != item.package_version.locked_version:
                # The previous resolution included this package in different
                # version, we cannot include this package to the stack =>
                # invalid software stack.
                return False

        # Nothing suspicious so far :)
        return True

    def walk(self,
             distribution_func: typing.Callable = None) -> typing.Generator[Project, None, None]:
        """Generate software stacks based on traversing the dependency graph.

        @param distribution_func: function used to filter out stacks (0 - omit stack, 1 include stack),
            used for sampling avoiding generating all the possible software stacks
        @return: a generator, each item yielded value is one option of a resolved software stack
        """
        # The implementation is very lazy (using generators where possible), more lazy then the author himself...
        distribution_func = distribution_func or (lambda: True)    # Always generate all, if not stated otherwise.
        stack = deque()

        # Initial configuration picks the latest versions:
        configurations = product(*(range(len(i)) for i in self.direct_dependencies.values()))
        for configuration in configurations:
            filtering_values = (operator.itemgetter(i) for i in configuration)
            extended = map(lambda f, v: f(v), zip(filtering_values, self.direct_dependencies.values()))
            if self._is_valid_state({}, extended):
                stack.append(({}, extended))

        while stack:
            state = stack.pop()

            if self._is_final_state(state):
                if distribution_func():
                    yield Project.from_package_versions(state[0].values(), meta=self._meta)
                continue

            configurations = product(*(range(len(i)) for i in state[1]))
            for configuration in configurations:
                filtering_values = (operator.itemgetter(i) for i in configuration)
                expanded = map(lambda f, v: f(v), zip(filtering_values, state[1]))

                if self._is_valid_state(state[0], expanded):
                    stack.append((
                        dict(state[0]).update({g.package_version.name: g for g in expanded}),
                        chain.from_iterable(g.dependencies.values() for g in expanded)
                    ))
