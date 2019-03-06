#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019 Fridolin Pokorny
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

This implementation is talking to the LibDependencyGraph (which talks to C/C++
implementation). The aim of this implementation is to prepare arguments for
C/C++ implementation and call the scoring routines.
"""

import os
import pickle
import typing
import logging
from functools import reduce
from functools import cmp_to_key
from itertools import chain
import operator

import attr
from thoth.python import PackageVersion
from thoth.python.pipfile import PipfileMeta
from thoth.python import Project
from thoth.python import Source
from thoth.solver.python.base import SolverException
from thoth.storages import GraphDatabase
from thoth.common import RuntimeEnvironment

from .solver import PythonPackageGraphSolver
from .exceptions import ConstraintClashError
from .bin import LibDependencyGraph
from .bin import PrematureStreamEndError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class DependencyGraph:
    """N-ary dependency graph stored in memory."""

    dependencies_map = attr.ib(type=dict)
    meta = attr.ib(type=PipfileMeta)
    full_dependencies_map = attr.ib(type=dict)
    project = attr.ib(type=Project)
    # A list of package tuples (package name, package version, index url) forming paths based on versions.
    paths = attr.ib(type=list)
    direct_dependencies = attr.ib(type=typing.List[PackageVersion])

    @property
    def stacks_estimated(self) -> int:
        """Estimate number of sofware stacks we could end up with (the upper boundary)."""
        # We could estimate based on traversing the tree, it would give us better, but still rough estimate.
        dependencies = {}
        for dependency_name, dependency_versions in self.full_dependencies_map.items():
            dependencies_total = 0
            for dependency_urls in dependency_versions.values():
                dependencies_total += len(dependency_urls)
            dependencies[dependency_name] = dependencies_total

        return reduce(lambda a, b: a * b, dependencies.values())

    @staticmethod
    def _is_package_version_no_index(
        package_version: PackageVersion, name: str, version: str
    ):
        """Check if the given package-version entry has given attributes."""
        return (
            package_version.name == name and package_version.version == "==" + version
        )

    @staticmethod
    def create_package_version_record(
        full_dependencies_map: dict, package_version: PackageVersion
    ) -> None:
        """Create a record of a Python package in dependencies map."""
        version = package_version.locked_version
        if (
            full_dependencies_map.get(package_version.name, {})
            .get(version, {})
            .get(package_version.index.url)
        ):
            return

        if package_version.name not in full_dependencies_map:
            full_dependencies_map[package_version.name] = {}

        it = full_dependencies_map[package_version.name]
        if version not in it:
            it[version] = {}

        it = it[version]
        if package_version.index.url not in it:
            it[package_version.index.url] = package_version

    @staticmethod
    def create_package_version_record_from_tuple(
        full_dependencies_map: dict, package_tuple: tuple, is_develop: bool = False
    ) -> None:
        """Create a record of a Python package in dependencies map."""
        package_name, package_version, index_url = package_tuple
        if (
            full_dependencies_map.get(package_name, {})
            .get(package_version, {})
            .get(index_url)
        ):
            return

        if package_name not in full_dependencies_map:
            full_dependencies_map[package_name] = {}

        it = full_dependencies_map[package_name]
        if package_version not in it:
            it[package_version] = {}

        it = it[package_version]
        if index_url not in it:
            entry = PackageVersion(
                name=package_name,
                version="==" + package_version,
                index=Source(index_url),
                develop=is_develop,
            )
            it[index_url] = entry

    @classmethod
    def _prepare_direct_dependencies(
        cls, solver: PythonPackageGraphSolver, project: Project, *, with_devel: bool
    ) -> tuple:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        # It's important that solver preserves order in which packages were inserted.
        # This is also a requirement for running under Python3.6+!!!
        _LOGGER.debug("Resolving direct dependencies")
        resolved_direct_dependencies = solver.solve(
            list(project.iter_dependencies(with_devel=with_devel)),
            graceful=False,
            all_versions=True,
        )

        full_dependencies_map = {}
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
                cls.create_package_version_record(
                    full_dependencies_map, package_version
                )
                dependencies_map[package_name].append(package_version)

        # dependencies_map maps package_name to a list of PackageVersion objects
        # full_dependencies_map maps package_name, package_version, index_url to a PackageVersion object;
        # full_dependencies_map is used to discard duplicates
        return dependencies_map, full_dependencies_map

    @classmethod
    def _cut_off_dependencies(
        cls,
        graph: GraphDatabase,
        dependencies_map: dict,
        transitive_paths: typing.List[list],
        core_packages: typing.Dict[str, dict],
        project: Project,
        restrict_indexes: bool,
    ) -> typing.List[dict]:
        """Cut off paths that have not relevant dependencies - dependencies we don't want to include in the stack."""
        result = []
        for core_package_name, versions in core_packages.items():
            if not versions:
                continue

            versions = [
                (PackageVersion.parse_semantic_version(version), version)
                for version in versions.keys()
            ]
            # Always pick the latest for now, later ask for observations.
            version = sorted(versions, key=operator.itemgetter(0), reverse=True)[0]
            index_url = core_packages[core_package_name][version[1]]
            core_packages[core_package_name] = {version[1]: index_url}

        allowed_indexes = None
        if restrict_indexes and project.pipfile.meta.sources:
            allowed_indexes = set(
                source.url for source in project.pipfile.meta.sources.values()
            )

        for path in transitive_paths:
            include_path = True
            for package_tuple in path:
                if allowed_indexes and package_tuple[2] not in allowed_indexes:
                    _LOGGER.debug(
                        "Excluding path with package %r - index not in allowed indexes",
                        package_tuple,
                    )
                    include_path = False
                    break

                if package_tuple[0] in core_packages.keys() and (
                    package_tuple[1] not in core_packages[package_tuple[0]]
                    or package_tuple[2]
                    not in core_packages[package_tuple[0]][package_tuple[1]]
                ):
                    _LOGGER.debug(
                        "Excluding the given stack due to core package %r",
                        package_tuple,
                    )
                    include_path = False
                    break

                if not project.prereleases_allowed:
                    package_version = dependencies_map[package_tuple[0]][
                        package_tuple[1]
                    ][package_tuple[2]]
                    if (
                        package_version.semantic_version.build
                        or package_version.semantic_version.prerelease
                    ):
                        _LOGGER.debug(
                            "Excluding path with package %r as pre-releases were disabled",
                            package_tuple,
                        )
                        include_path = False
                        break

            if include_path:
                result.append(path)

        return result

    @staticmethod
    def _get_python_package_tuples(
        ids_map: typing.Dict[int, tuple],
        graph: GraphDatabase,
        python_package_ids: typing.Set[int],
    ) -> None:
        """Retrieve tuples representing package name, package version and index url for the given set of ids."""
        seen_ids = set(ids_map.keys())
        unseen_ids = python_package_ids - seen_ids

        _LOGGER.debug(
            "Retrieving package tuples for transitive dependencies (count: %d)",
            len(unseen_ids),
        )
        package_tuples = graph.get_python_package_tuples(unseen_ids)
        for python_package_id, package_tuple in package_tuples.items():
            ids_map[python_package_id] = package_tuple

    @staticmethod
    def _sort_paths(full_dependencies_map: dict, paths: tuple) -> list:
        """Perform sorting of paths to makes sure preserve order of generated stacks.

        To have stacks sorted from latest down to oldest, ideally we should take into account package release
        date. We are approximating the sorting based on semver of packages. This means that a stack which is made
        of packages in the following versions:

        A: 1.0.0, 1.1.0
        B: 2.0.0, 2.1.0

        Will produce stacks:

        [
          [A-1.1.0, B-2.1.0],
          [A-1.1.0, B-2.0.0],
          [A-1.0.0, B-2.1.0],
          [A-1.0.0, B-2.0.0],
        ]

        That means we will sort paths horizontally, where each item in all transitive dependencies will be
        checked for its semver version and rows in paths can be swapped accordingly.
        """

        def dereference_package_version(package_tuple: tuple):
            """Get package version from the dependencies map based on tuple provided."""
            return full_dependencies_map[package_tuple[0]][package_tuple[1]][
                package_tuple[2]
            ]

        def cmp_function(path1: list, path2: list):
            """Compare two paths and report which should take precedence.

            This is the core function which makes sure stacks coming from dependency graph are sorted and
            have deterministic ordering. This function should be used as a key with functools.cmp_to_key.

            The ordering produced by dependency graph is iterating on indirect dependencies on higher frequencies in
            comparision to direct dependencies. This way we are trying to keep direct deps as fresh as possible and
            making sure just transitive ones could be older.
            """
            for idx in range(len(path1)):
                if idx >= len(path2):
                    return -1

                package_name1 = path1[idx][0]
                package_name2 = path2[idx][0]
                package_version1 = path1[idx][1]
                package_version2 = path2[idx][1]
                index_url1 = path1[idx][2]
                index_url2 = path2[idx][2]

                if package_name1 != package_name2:
                    # We call this function with reverse set to true, to have packages sorted alphabetically we
                    # inverse logic here so package names are *really* sorted alphabetically.
                    return -int(package_name1 > package_name2) or 1
                elif package_version1 != package_version2:
                    semver1 = dereference_package_version(path1[idx]).semantic_version
                    semver2 = dereference_package_version(path2[idx]).semantic_version
                    result = semver1.__cmp__(semver2)

                    if result is NotImplemented:
                        # Based on semver, this can happen if at least one has build
                        # metadata - there is no ordering specified.
                        if semver1.build:
                            return -1
                        return 1

                    return result
                elif index_url1 != index_url2:
                    return -int(index_url1 < index_url2) or 1

            # Same paths?! This should be probably unreachable but this can happen if did not take into
            # account os or python version when querying graph database. We taken this into account earlier.
            return 0

        # The implementation sorts "horizontally" transitive dependencies, we do not do it in-place
        # as we need to cast it to list (done implicitly).
        return sorted(paths, key=cmp_to_key(cmp_function), reverse=False)

    @classmethod
    def from_project(
        cls,
        graph: GraphDatabase,
        project: Project,
        runtime_environment: RuntimeEnvironment,
        *,
        with_devel: bool = False,
        restrict_indexes: bool = True,
    ):
        """Construct a dependency graph from a project.

        The restrict indexes flag states whether there should be used indexes only as configured from project metadata.
        """
        # Load from a dump if user requested it.
        if os.getenv("THOTH_ADVISER_FILEDUMP") and os.path.isfile(
            os.getenv("THOTH_ADVISER_FILEDUMP")
        ):
            _LOGGER.warning(
                "Loading file dump %r as per user request",
                os.getenv("THOTH_ADVISER_FILEDUMP"),
            )
            with open(os.getenv("THOTH_ADVISER_FILEDUMP"), "rb") as file_dump:
                return pickle.load(file_dump)

        # Place the import statement here to simplify mocks in the testsuite.
        solver = PythonPackageGraphSolver(
            graph_db=graph, runtime_environment=runtime_environment
        )
        _LOGGER.info("Parsing and solving direct dependencies of the requested project")
        dependencies_map, full_dependencies_map = cls._prepare_direct_dependencies(
            solver, project, with_devel=with_devel
        )

        # Map id of packages to their tuple representation.
        package_tuples_map = dict()
        # All the direct dependencies (a list of PackageVersion).
        all_direct_dependencies = list(chain(*dependencies_map.values()))
        # All paths that should be included for computed stacks.
        all_transitive_dependencies_to_include = []
        # Core python packages as pip, setuptools, six - we need to reduce the amount of software stacks
        # generated, pick the most suitable ones when cutting off. These packages are also pre-analyzed by our init-job.
        core_packages = dict.fromkeys(("pip", "setuptools", "six"), {})

        _LOGGER.info("Retrieving transitive dependencies of direct dependencies")
        for package_version in all_direct_dependencies:
            _LOGGER.debug(
                "Retrieving transitive dependencies for %r in version %r from %r",
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
            )
            transitive_dependencies = graph.retrieve_transitive_dependencies_python(
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
            )
            # We need to explicitly iterate over these results as gremlin-python wraps result into Path object
            # which does not support advanced indexing like 0::2.
            ids = set()
            for entry in transitive_dependencies:
                for idx in range(0, len(entry), 2):
                    ids.add(entry[idx])
            cls._get_python_package_tuples(package_tuples_map, graph, ids)

            # Fast path - filter out paths that have a version of a direct
            # dependency in it that does not correspond to the direct
            # dependency. This way we can filter out a lot of nodes in the graph and reduce walks.
            transitive_dependencies_to_include = []
            for entry in transitive_dependencies:
                exclude = False
                new_entry = []
                for idx in range(0, len(entry), 2):
                    item = entry[idx]
                    solver_error = False  # Can be leaf dependency in dependency graph.
                    if len(entry) > idx + 1:
                        solver_error = entry[idx + 1]

                    item = package_tuples_map[item]
                    package, version, index_url = item[0], item[1], item[2]

                    if solver_error:
                        item = package_tuples_map[entry[idx + 2]]
                        _LOGGER.info(
                            "Excluding a path due to package %s: unable to install in the given environment",
                            item,
                        )
                        exclude = True
                        break

                    if package in core_packages.keys():
                        if version not in core_packages[package]:
                            core_packages[package][version] = []
                        core_packages[package][version].append(index_url)

                    new_entry.append((package, version, index_url))
                    direct_packages_of_this = [
                        dep for dep in all_direct_dependencies if dep.name == package
                    ]

                    if not direct_packages_of_this:
                        continue

                    is_direct = (
                        cls._is_package_version_no_index(dep, package, version)
                        for dep in direct_packages_of_this
                    )
                    if any(is_direct):
                        continue

                    # Otherwise do not include it - cut off the un-reachable dependency graph.
                    _LOGGER.debug(
                        "Excluding a path due to package %s: unreachable based on direct dependencies",
                        item,
                    )
                    exclude = True
                    break

                if not exclude:
                    transitive_dependencies_to_include.append(new_entry)

            # There are transitive dependencies, but we were not able to construct dependency graph
            # with given constraints (e.g. there is always dependency on protobuf, but we asked to remove protobuf).
            if transitive_dependencies and not transitive_dependencies_to_include:
                raise ConstraintClashError(
                    "Unable to create a dependency graph for the given set of constraints"
                )

            all_transitive_dependencies_to_include.extend(
                transitive_dependencies_to_include
            )

        # Remove possible duplicates. They can occur when if we did not specify os, python version, ... in query
        # so multiple edges could be traversed at the same time. We just cast all the lists into tuples so that
        # they are hashable.
        _LOGGER.debug("Sorting dependencies based on their semver...")
        all_transitive_dependencies_to_include = tuple(
            set(tuple(tuple(i) for i in all_transitive_dependencies_to_include))
        )

        # Make sure we have all the versions parsed with semver in a PackageVersion instance.
        for entry in all_transitive_dependencies_to_include:
            for package_tuple in entry:
                cls.create_package_version_record_from_tuple(
                    full_dependencies_map, package_tuple
                )

        _LOGGER.warning("Sorting dependencies to preserve order of generated stacks")
        all_transitive_dependencies_to_include = cls._sort_paths(
            full_dependencies_map, all_transitive_dependencies_to_include
        )

        _LOGGER.info("Cutting off unwanted dependencies")
        all_transitive_dependencies_to_include = cls._cut_off_dependencies(
            graph,
            full_dependencies_map,
            all_transitive_dependencies_to_include,
            core_packages,
            project,
            restrict_indexes,
        )

        _LOGGER.info("Creating dependency graph")
        instance = cls(
            dependencies_map,
            project=project,
            meta=project.pipfile.meta,
            full_dependencies_map=full_dependencies_map,
            paths=all_transitive_dependencies_to_include,
            direct_dependencies=all_direct_dependencies,
        )

        # Store in a dump if user requested it.
        if os.getenv("THOTH_ADVISER_FILEDUMP"):
            _LOGGER.warning("Storing file dump as per user request")
            with open(os.getenv("THOTH_ADVISER_FILEDUMP"), "wb") as file_dump:
                pickle.dump(instance, file_dump)

        return instance

    def _construct_libdependency_graph_kwargs(self):
        """Construct keyword arguments to be passed to the libdependency graph implementation."""
        direct_dependencies = []
        dependency_types = []
        dependency_types_seen = {}
        context = []
        reverse_context = {}
        show_packages = bool(int(os.getenv("THOTH_ADVISER_SHOW_PACKAGES", 0)))
        for package_name, package_versions in self.full_dependencies_map.items():
            if show_packages:
                count = sum(len(s.values()) for s in package_versions.values())
                _LOGGER.info("Package %r: %d", package_name, count)

            for version, package_indexes in package_versions.items():
                for index_url, package_version in package_indexes.items():
                    package_tuple = (
                        package_version.name,
                        package_version.locked_version,
                        package_version.index.url,
                    )
                    reverse_context[package_tuple] = len(context)
                    context.append(package_tuple)
                    if show_packages:
                        _LOGGER.info("\t%r from %s", context[-1][1], context[-1][2])

                    if package_name not in dependency_types_seen:
                        dependency_types_seen[package_name] = len(dependency_types_seen)

                    dependency_types.append(dependency_types_seen[package_name])

        # Map direct dependencies to their corresponding numbers based on mapping.
        for package_version in self.direct_dependencies:
            package_tuple = (
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
            )
            direct_dependencies.append(reverse_context[package_tuple])

        dependencies_list = []
        for entry in self.paths:
            for idx in range(len(entry) - 1):
                source = reverse_context[(entry[idx][0], entry[idx][1], entry[idx][2])]
                destination = reverse_context[
                    (entry[idx + 1][0], entry[idx + 1][1], entry[idx + 1][2])
                ]
                dependencies_list.append((source, destination))

        dependencies_list = list(dict.fromkeys(dependencies_list).keys())
        return (
            context,
            {
                "direct_dependencies": direct_dependencies,
                "dependencies_list": dependencies_list,
                "dependency_types": dependency_types,
            },
        )

    @staticmethod
    def _reconstruct_stack(context: list, stack: list) -> list:
        """Reconstruct the stack based on results from libdependency graph walks."""
        result = []
        for item in stack:
            package_entry = context[item]
            result.append(package_entry)

        return result

    def _create_package_versions(
        self, stack: typing.List[tuple]
    ) -> typing.List[PackageVersion]:
        """Create package versions out of package tuples.

        We cache constructed objects in the context so we instantiate them only once.
        """
        result = []
        for package_tuple in stack:
            entry = self.full_dependencies_map[package_tuple[0]][package_tuple[1]][
                package_tuple[2]
            ]
            if not isinstance(entry, PackageVersion):
                entry = PackageVersion(
                    name=package_tuple[0],
                    version="==" + package_tuple[1],
                    index=Source(package_tuple[2]),
                    develop=False,
                )
                self.full_dependencies_map[package_tuple[0]][package_tuple[1]][
                    package_tuple[2]
                ] = entry

            result.append(entry)

        return result

    def walk(
        self, decision_function: typing.Callable
    ) -> typing.Generator[tuple, None, None]:
        """Generate software stacks based on traversing the dependency graph.

        @param decision_function: function used to filter out stacks
        @return: a generator, each item yielded value is one option of a resolved software stack
        """
        _LOGGER.info(
            "Computing possible stack candidates, estimated stacks count: %d",
            self.stacks_estimated,
        )
        context, libdependency_kwargs = self._construct_libdependency_graph_kwargs()

        direct_dependencies = list(self.project.iter_dependencies(with_devel=True))
        try:
            libdependency_graph = LibDependencyGraph(**libdependency_kwargs)
            for stack_identifiers in libdependency_graph.walk():
                stack = self._reconstruct_stack(context, stack_identifiers)

                _LOGGER.info(
                    "Found a new stack, asking decision function for inclusion"
                )
                decision_function_result = decision_function(stack)
                if decision_function_result[0] is not False:
                    _LOGGER.info(
                        "Decision function included the computed stack - result was %r",
                        decision_function_result[0],
                    )
                    package_versions = self._create_package_versions(stack)
                    _LOGGER.debug("Included stack, yielding it: %r", stack)
                    # Discard original sources so they are filled correctly from packages.
                    pipfile_meta = self.meta.to_dict()
                    pipfile_meta["sources"] = {}
                    yield decision_function_result, Project.from_package_versions(
                        packages=direct_dependencies,
                        packages_locked=package_versions,
                        meta=PipfileMeta.from_dict(pipfile_meta),
                    )
                else:
                    _LOGGER.info("Decision function excluded the computed stack")
                    _LOGGER.debug("Excluded stack %r", stack)
        except PrematureStreamEndError:
            _LOGGER.warning("Stack stream was closed prematurely (OOM?)")
