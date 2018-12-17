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

import os
import pickle
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
from thoth.storages import GraphDatabase

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
                if direct_dependencies_map.get(package_version.name, {}).get(package_version.locked_version, {}).get(package_version.index.url):
                    continue

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
    def _cut_off_dependencies(cls, graph: GraphDatabase, transitive_paths: typing.List[dict]) -> typing.List[dict]:
        """Cut off paths that have not relevant dependencies - dependencies we don't want to include in the stack."""
        _LOGGER.debug("Cutting off not relevant paths")
        return transitive_paths

    @staticmethod
    def _get_python_package_tuples(ids_map: typing.Dict[int, tuple], graph: GraphDatabase, python_package_ids: typing.Set[int]) -> None:
        """Retrieve tuples representing package name, package version and index url for the given set of ids."""
        seen_ids = set(ids_map.keys())
        unseen_ids = python_package_ids - seen_ids

        _LOGGER.info("Retrieving package tuples for transitive dependencies (count: %d)", len(unseen_ids))
        package_tuples = graph.get_python_package_tuples(unseen_ids)
        for python_package_id, package_tuple in package_tuples.items():
            ids_map[python_package_id] = package_tuple

    @classmethod
    def from_project(cls, graph: GraphDatabase, project: Project, with_devel: bool = False):
        """Construct a dependency graph from a project."""
        # Load from a dump if user requested it.
        if os.getenv('THOTH_ADVISER_FILEDUMP') and os.path.isfile(os.getenv('THOTH_ADVISER_FILEDUMP')):
            _LOGGER.warning("Loading file dump %r as per user request", os.getenv('THOTH_ADVISER_FILEDUMP'))
            with open(os.getenv('THOTH_ADVISER_FILEDUMP'), 'rb') as file_dump:
                return pickle.load(file_dump)

        # Place the import statement here to simplify mocks in the testsuite.
        solver = PythonPackageGraphSolver(graph_db=graph)
        _LOGGER.info("Parsing and solving direct dependencies of the requested project")
        direct_dependencies, dependencies_map = cls._prepare_direct_dependencies(
            solver,
            project,
            with_devel=with_devel
        )

        # Map id of packages to their tuple representation.
        package_tuples_map = dict()
        # Now perform resolution on all the transitive dependencies.
        all_direct_dependencies = list(chain(*direct_dependencies.values()))
        all_dependencies = list(all_direct_dependencies)
        # Mapping of source_name -> destination name, destination version, destination index to preserve duplicates.
        source_dependencies = {}
        # All paths that should be included for computed stacks.
        all_transitive_dependencies_to_include = []

        for graph_item in all_direct_dependencies:
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

            cls._get_python_package_tuples(package_tuples_map, graph, set(chain(chain(*transitive_dependencies))))

            # Fast path - filter out paths that have a version of a direct
            # dependency in it that does not correspond to the direct
            # dependency. This way we can filter out a lot of nodes in the graph and reduce walks.
            transitive_dependencies_to_include = []
            for entry in transitive_dependencies:
                exclude = False
                new_entry = []
                for idx in range(0, len(entry), 2):
                    item = entry[idx]
                    item = package_tuples_map[item]
                    package, version, index_url = item[0], item[1], item[2]
                    new_entry.append((package, version, index_url))
                    direct_packages_of_this = [
                        dep for dep in all_direct_dependencies if dep.package_version.name == package
                    ]

                    if not direct_packages_of_this:
                        continue

                    is_direct = (dep.is_package_version_no_index(package, version) for dep in direct_packages_of_this)
                    if any(is_direct):
                        continue

                    # Otherwise do not include it - cut off the un-reachable dependency graph.
                    _LOGGER.debug(
                        "Excluding a path due to package %s (unreachable based on direct dependencies)", (package, version, index_url)
                    )
                    exclude = True
                    break

                if not exclude:
                    transitive_dependencies_to_include.append(new_entry)

            # There are transitive dependencies, but we were not able to construct dependency graph
            # with given constraints (e.g. there is always dependency on protobuf, but we asked to remove protobuf).
            if transitive_dependencies and not transitive_dependencies_to_include:
                raise ConstraintClashError("Unable to create a dependency graph for the given set of constraints")
            
            all_transitive_dependencies_to_include.extend(transitive_dependencies_to_include)

        all_transitive_dependencies_to_include = cls._cut_off_dependencies(graph, all_transitive_dependencies_to_include)

        for entry in all_transitive_dependencies_to_include:
            # Name graph-query dependent results.
            for idx in range(0, len(entry) - 1):
                # The idx corresponds to "depends_on" that is in the middle of source and target package.
                if len(entry) == 1:
                    # Dependency is a direct dependency without any own dependencies. 
                    continue

                source_idx = idx
                dest_idx = idx + 1

                source_name, source_version, source_index = \
                    entry[source_idx][0], entry[source_idx][1], entry[source_idx][2]
                destination_name, destination_version, destination_index = \
                    entry[dest_idx][0], entry[dest_idx][1], entry[dest_idx][2]

                # If this fails on key error, the returned query from graph
                # does not preserve order of nodes visited (it should).
                source = dependencies_map[source_name][source_version][source_index]
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

                it = source_dependencies[source_name]
                if source_version not in it:
                    it[source_version] = {}

                it = it[source_version]
                if destination_name not in it:
                    it[destination_name] = {}

                it = it[destination_name]
                if destination_version not in it:
                    it[destination_version] = {}

                it = it[destination_version]
                if destination_index not in it:
                    it[destination_index] = destination

        for package in all_dependencies:
            if package.package_version.name not in source_dependencies or \
                    package.package_version.locked_version not in source_dependencies[package.package_version.name]:
                continue

            package_deps = source_dependencies[package.package_version.name][package.package_version.locked_version]
            for dependency_name, dependency_versions in package_deps.items():
                for dependency_version, dependency_urls in dependency_versions.items():
                    for dependency_url in dependency_urls:
                        if dependency_name not in package.dependencies:
                            package.dependencies[dependency_name] = []

                        dependency = dependencies_map[dependency_name][dependency_version][dependency_url]
                        package.dependencies[dependency_name].append(dependency)

        _LOGGER.info("Creating dependency graph")
        instance = cls(
            direct_dependencies,
            project=project,
            meta=project.pipfile.meta,
            dependencies_map=dependencies_map
        )

        # Store in a dump if user requested it.
        if os.getenv('THOTH_ADVISER_FILEDUMP'):
            _LOGGER.warning("Storing file dump as per user request")
            with open(os.getenv('THOTH_ADVISER_FILEDUMP'), 'wb') as file_dump:
                return pickle.dump(instance, file_dump)

        return instance

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

    def walk(self, decision_function: typing.Callable) -> typing.Generator[tuple, None, None]:
        """Generate software stacks based on traversing the dependency graph.

        @param decision_function: function used to filter out stacks
        @return: a generator, each item yielded value is one option of a resolved software stack
        """
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
                decision_function_result = decision_function((graph_item.package_version for graph_item in state[0].values()))
                if decision_function_result[0]:
                    _LOGGER.info(
                        "Decision function included the computed stack - result was %r", decision_function_result[0]
                    )
                    _LOGGER.debug("Included stack %r", state[0])
                    package_versions = tuple(g.package_version for g in state[0].values())
                    _LOGGER.debug("Yielding newly created project from state: %r", state[0])
                    # Discard original sources so they are filled correctly from packages.
                    pipfile_meta = self.meta.to_dict()
                    pipfile_meta['sources'] = {}
                    yield decision_function_result, Project.from_package_versions(
                        packages=list(self.project.iter_dependencies(with_devel=True)),
                        packages_locked=package_versions,
                        meta=PipfileMeta.from_dict(pipfile_meta)
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
