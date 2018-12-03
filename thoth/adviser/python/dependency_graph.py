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
from thoth.python import PackageVersion
from thoth.python.pipfile import PipfileMeta
from thoth.python import Source
from thoth.python import Project
from thoth.solver.python.base import SolverException

from .solver import PythonPackageGraphSolver
from .exceptions import ConstraintClashError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class GraphItem:
    """Extend PackageVersion with a link to resolved dependencies of the given package version."""

    package_version = attr.ib(type=PackageVersion)
    dependencies = attr.ib(default=attr.Factory(dict))

    def is_package_version_no_index(self, package_name: str, package_version: str):
        """Check if the given package-version entry has given attributes."""
        return self.package_version.name == package_name and \
            self.package_version.version == '==' + package_version

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
    project = attr.ib(type=Project)

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

            if not package_versions:
                # This means that there were found versions in the graph
                # database but none was matching the given version range.
                raise SolverException(
                    f"No matching versions found for package {package_name!r}"
                )

            for package_version in package_versions:
                graph_item = GraphItem(package_version=package_version)

                if package_version.name not in direct_dependencies_map:
                    direct_dependencies_map[package_version.name] = {}

                if package_version.locked_version not in direct_dependencies_map[package_version.name]:
                    direct_dependencies_map[package_version.name][package_version.locked_version] = {}

                if package_version.index.url not in direct_dependencies_map[package_version.name][package_version.locked_version]:
                    # TODO: if devel and default have same packages
                    direct_dependencies_map[package_version.name][package_version.locked_version][package_version.index.url] = graph_item
                    dependencies_map[package_name].append(graph_item)

        # dependencies_map maps package_name to a list of GraphItem objects
        # direct_dependencies_map maps package_name,package_version,index_url to GraphItem object
        return dependencies_map, direct_dependencies_map

    @classmethod
    def from_project(cls, project: Project, with_devel: bool = False):
        """Construct a dependency graph from a project."""
        # Place the import statement here to simplify mocks in the testsuite.
        from thoth.storages.graph.janusgraph import GraphDatabase

        graph = GraphDatabase()
        graph.connect()
        solver = PythonPackageGraphSolver(graph_db=graph)
        _LOGGER.info("Parsing and solving direct dependencies of the requested project")
        direct_dependencies, dependencies_map = cls._prepare_direct_dependencies(
            solver,
            project,
            with_devel=with_devel
        )

        # Now perform resolution on all the transitive dependencies.
        all_direct_dependencies = list(chain(*direct_dependencies.values()))
        all_dependencies = list(all_direct_dependencies)
        # Mapping of source_name -> destination name, destination version, destination index to preserve duplicates.
        source_dependencies = {}
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
            _LOGGER.info(
                "Retrieving transitive dependencies for %r in version %r from %r",
                graph_item.package_version.name,
                graph_item.package_version.locked_version,
                graph_item.package_version.index.url
            )
            transitive_dependencies = graph.retrieve_transitive_dependencies_python(
                graph_item.package_version.name,
                graph_item.package_version.locked_version,
                graph_item.package_version.index.url
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
                        dep for dep in all_direct_dependencies if dep.package_version.name == item['package']
                    ]

                    if not direct_packages_of_this:
                        continue

                    is_direct = (dep.is_package_version_no_index(item['package'], item['version']) for dep in direct_packages_of_this)
                    if any(is_direct):
                        continue

                    # Otherwise do not include it - cut off the un-reachable dependency graph.
                    _LOGGER.info(
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
                source_name, source_version, source_index = \
                    entry[0]['package'], entry[0]['version'], entry[0]['index_url']
                destination_name, destination_version, destination_index = \
                    entry[2]['package'], entry[2]['version'], entry[2]['index_url']

                # If this fails on key error, the returned query from graph
                # does not preserve order of nodes visited (it should).
                source = dependencies_map[source_name][source_version][source_index]

                # TODO: same package name on different index?
                destination = dependencies_map.get(destination_name, {}).get(destination_version, {}).get(destination_index)

                if not destination:
                    # First time seen.
                    new_package_version = PackageVersion(
                        name=destination_name,
                        version='==' + destination_version,
                        index=Source(destination_index),
                        hashes=[],
                        develop=source.package_version.develop
                    )

                    destination = GraphItem(package_version=new_package_version)

                    if destination_name not in dependencies_map:
                        dependencies_map[destination_name] = {}

                    if destination_version not in dependencies_map[destination_name]:
                        dependencies_map[destination_name][destination_version] = {}

                    dependencies_map[destination_name][destination_version][destination_index] = destination
                    all_dependencies.append(destination)

                if source_name not in source_dependencies:
                    source_dependencies[source_name] = {}

                if source_version not in source_dependencies[source_name]:
                    source_dependencies[source_name][source_version] = {}

                if destination_name not in source_dependencies[source_name]:
                    source_dependencies[source_name][source_version][destination_name] = {}

                if destination_version not in source_dependencies[source_name][source_version][destination_name]:
                    source_dependencies[source_name][source_version][destination_name][destination_version] = {}

                if destination_index not in source_dependencies[source_name][source_version][destination_name][destination_version]:
                    source_dependencies[source_name][source_version][destination_name][destination_version][destination_index] = destination

        for package in all_dependencies:
            if package.package_version.name in source_dependencies and package.package_version.locked_version in source_dependencies[name]:
                for dependency_name, dependency_versions in source_dependencies[package.package_version.name][package.package_version.locked_version].items():
                    for dependency_version, dependency_urls in dependency_versions.items():
                        for dependency_url in dependency_urls:
                            if dependency_name not in package.dependencies:
                                package.dependencies[dependency_name] = []

                            dependency = dependencies_map[dependency_name][dependency_version][dependency_url]
                            package.dependencies[dependency_name].append(dependency)

        _LOGGER.info("Creating dependency graph")
        return cls(
            direct_dependencies,
            project=project,
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

            if item.package_version.locked_version != expanded[item.package_version.name].package_version.locked_version:
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
                    != item.package_version.locked_version or \
                    expanded[item.package_version.name].package_version.index != item.package_version.index:
                # The previous resolution included this package in different
                # version, we cannot include this package to the stack =>
                # invalid software stack.
                return False

        # Nothing suspicious so far :)
        return True

    def walk(self, decision_function: typing.Callable = None) -> typing.Generator[tuple, None, None]:
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

        # Initial configuration picks the latest versions first (they are last on the stack):
        _LOGGER.info("Creating initial configurations for stack expansion")
        configurations = product(*(range(len(i)) for i in self.direct_dependencies.values()))
        for configuration in configurations:
            filtering_values = (operator.itemgetter(i) for i in configuration)
            to_expand = tuple(map(lambda i: i[0](i[1]), zip(filtering_values, self.direct_dependencies.values())))
            if self._is_valid_state({}, to_expand):
                stack.append(({}, to_expand))

        _LOGGER.info("Computing possible stack candidates")
        while stack:
            state = stack.pop()

            if self._is_final_state(state):
                _LOGGER.info("Found a new stack, asking decision function for inclusion")
                decision_function_result = decision_function((graph_item.package_version for graph_item in state[0]))
                if decision_function_result:
                    _LOGGER.info(
                        "Decision function included the computed stack - result was %r", decision_function_result
                    )
                    _LOGGER.debug("Included stack %r", state[0])
                    package_versions = tuple(g.package_version for g in state[0].values())
                    _LOGGER.debug("Yielding newly created project from state: %r", state[0])
                    yield decision_function_result, Project.from_package_versions(
                        packages=list(self.project.iter_dependencies(with_devel=True)),
                        packages_locked=package_versions,
                        meta=self.meta
                    )
                else:
                    _LOGGER.info("Decision function excluded the computed stack")
                    _LOGGER.debug("Excluded stack %r", state[0])
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
            
