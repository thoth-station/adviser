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
    def _is_package_version_no_index(package_version: PackageVersion, name: str, version: str):
        """Check if the given package-version entry has given attributes."""
        return package_version.name == name and package_version.version == "==" + version

    @staticmethod
    def create_package_version_record(full_dependencies_map: dict, package_version: PackageVersion) -> None:
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
    def create_package_version_holder(full_dependencies_map: dict, package_tuple: tuple) -> None:
        """Mark the given package as known to Thoth, let it instantiate lazily."""
        package_name, package_version, package_index_url = package_tuple
        if (
            full_dependencies_map.get(package_name, {})
            .get(package_version, {})
            .get(package_index_url)
        ):
            return

        if package_name not in full_dependencies_map:
            full_dependencies_map[package_name] = {}

        it = full_dependencies_map[package_name]
        if package_version not in it:
            it[package_version] = {}

        it = it[package_version]
        if package_index_url not in it:
            # We mark it exists.
            it[package_index_url] = True

    @classmethod
    def _prepare_direct_dependencies(
        cls,
        solver: PythonPackageGraphSolver,
        project: Project,
        *,
        with_devel: bool
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
                cls.create_package_version_record(full_dependencies_map, package_version)
                dependencies_map[package_name].append(package_version)

        # dependencies_map maps package_name to a list of PackageVersion objects
        # full_dependencies_map maps package_name, package_version, index_url to a PackageVersion object;
        # full_dependencies_map is used to discard duplicates
        return dependencies_map, full_dependencies_map

    @classmethod
    def _cut_off_dependencies(
        cls,
        graph: GraphDatabase,
        transitive_paths: typing.List[list],
        core_packages: typing.Dict[str, dict],
        project: Project,
        restrict_indexes: bool
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
            allowed_indexes = set(source.url for source in project.pipfile.meta.sources.values())

        for path in transitive_paths:
            include_path = True
            for package_tuple in path:
                if allowed_indexes and package_tuple[2] not in allowed_indexes:
                    _LOGGER.debug("Excluding path with package %r - index not in allowed indexes", package_tuple)
                    include_path = False
                    break

                if package_tuple[0] in core_packages.keys() and (
                    package_tuple[1] not in core_packages[package_tuple[0]]
                    or package_tuple[2]
                    not in core_packages[package_tuple[0]][package_tuple[1]]
                ):
                    _LOGGER.debug("Excluding the given stack due to core package %r", package_tuple)
                    include_path = False
                    break

                if not project.prereleases_allowed:
                    semantic_version = PackageVersion.parse_semantic_version(
                        package_tuple[1]
                    )
                    if semantic_version.build or semantic_version.prerelease:
                        _LOGGER.debug("Excluding path with package %r as pre-releases were disabled", package_tuple)
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

        _LOGGER.debug("Retrieving package tuples for transitive dependencies (count: %d)", len(unseen_ids))
        package_tuples = graph.get_python_package_tuples(unseen_ids)
        for python_package_id, package_tuple in package_tuples.items():
            ids_map[python_package_id] = package_tuple

    @classmethod
    def from_project(
        cls,
        graph: GraphDatabase,
        project: Project,
        runtime_environment: RuntimeEnvironment,
        *,
        with_devel: bool = False,
        restrict_indexes: bool = True
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
        solver = PythonPackageGraphSolver(graph_db=graph, runtime_environment=runtime_environment)
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

            cls._get_python_package_tuples(
                package_tuples_map, graph, set(chain(chain(*transitive_dependencies)))
            )

            # Fast path - filter out paths that have a version of a direct
            # dependency in it that does not correspond to the direct
            # dependency. This way we can filter out a lot of nodes in the graph and reduce walks.
            transitive_dependencies_to_include = []
            for entry in transitive_dependencies:
                exclude = False
                new_entry = []
                for idx in range(0, len(entry)):
                    item = entry[idx]
                    item = package_tuples_map[item]
                    package, version, index_url = item[0], item[1], item[2]

                    if package in core_packages.keys():
                        if version not in core_packages[package]:
                            core_packages[package][version] = []
                        core_packages[package][version].append(index_url)

                    new_entry.append((package, version, index_url))
                    direct_packages_of_this = [
                        dep
                        for dep in all_direct_dependencies
                        if dep.name == package
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
                        "Excluding a path due to package %s (unreachable based on direct dependencies)",
                        (package, version, index_url),
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

        _LOGGER.info("Cutting off unwanted dependencies")
        all_transitive_dependencies_to_include = cls._cut_off_dependencies(
            graph,
            all_transitive_dependencies_to_include,
            core_packages,
            project,
            restrict_indexes
        )

        for entry in all_transitive_dependencies_to_include:
            for package_tuple in entry:
                cls.create_package_version_holder(full_dependencies_map, package_tuple)

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

    def _construct_direct_dependencies(self, package_versions):
        """Get direct dependencies as they were stated in the original project.

        This is needed as we are recommending cross-index, we need to explicitly adjust the original set of direct
        dependencies and construct it from the new resolved set of dependencies.
        """
        direct_dependencies = []

        for package_version in package_versions:
            if package_version.develop and self.project.pipfile.dev_packages.get(
                package_version.name
            ):
                direct_dependencies.append(package_version)
            elif not package_version.develop and self.project.pipfile.packages.get(
                package_version.name
            ):
                direct_dependencies.append(package_version)

        return direct_dependencies

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
                    if isinstance(package_version, PackageVersion):
                        # Direct dependency.
                        direct_dependencies.append(len(context))
                        package_tuple = package_version.name, package_version.locked_version, package_version.index.url
                    else:
                        # Indirect dependency.
                        package_tuple = package_name, version, index_url

                    reverse_context[package_tuple] = len(context)
                    context.append(package_tuple)
                    if show_packages:
                        _LOGGER.info("\t%r from %s", context[-1][1], context[-1][2])

                    if package_name not in dependency_types_seen:
                        dependency_types_seen[package_name] = len(dependency_types_seen)

                    dependency_types.append(dependency_types_seen[package_name])

        dependencies_list = []
        for entry in self.paths:
            for idx in range(len(entry) - 1):
                source = reverse_context[(entry[idx][0], entry[idx][1], entry[idx][2])]
                destination = reverse_context[(entry[idx + 1][0], entry[idx + 1][1], entry[idx + 1][2])]
                dependencies_list.append((source, destination))

        dependencies_list = list(dict.fromkeys(dependencies_list).keys())
        return context, {
            "direct_dependencies": direct_dependencies,
            "dependencies_list": dependencies_list,
            "dependency_types": dependency_types
        }

    def _reconstruct_stack(self, context: list, stack: list) -> list:
        """Reconstruct the stack based on results from libdependency graph walks."""
        result = []
        for item in stack:
            package_entry = context[item]
            result.append(package_entry)

        return result

    def _create_package_versions(self, stack: typing.List[tuple]) -> typing.List[PackageVersion]:
        """Create package versions out of package tuples.

        We cache constructed objects in the context so we instantiate them only once.
        """
        result = []
        for package_tuple in stack:
            entry = self.full_dependencies_map[package_tuple[0]][package_tuple[1]][package_tuple[2]]
            if not isinstance(entry, PackageVersion):
                entry = PackageVersion(
                    name=package_tuple[0],
                    version="==" + package_tuple[1],
                    index=Source(package_tuple[2]),
                    develop=False
                )
                self.full_dependencies_map[package_tuple[0]][package_tuple[1]][package_tuple[2]] = entry

            result.append(entry)

        return result

    def walk(
        self, decision_function: typing.Callable
    ) -> typing.Generator[tuple, None, None]:
        """Generate software stacks based on traversing the dependency graph.

        @param decision_function: function used to filter out stacks
        @return: a generator, each item yielded value is one option of a resolved software stack
        """
        _LOGGER.info("Computing possible stack candidates, estimated stacks count: %d", self.stacks_estimated)
        context, libdependency_kwargs = self._construct_libdependency_graph_kwargs()

        try:
            libdependency_graph = LibDependencyGraph(**libdependency_kwargs)
            for stack_identifiers in libdependency_graph.walk():
                stack = self._reconstruct_stack(context, stack_identifiers)

                _LOGGER.info("Found a new stack, asking decision function for inclusion")
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
                        packages=self._construct_direct_dependencies(package_versions),
                        packages_locked=package_versions,
                        meta=PipfileMeta.from_dict(pipfile_meta),
                    )
                else:
                    _LOGGER.info("Decision function excluded the computed stack")
                    _LOGGER.debug("Excluded stack %r", stack)
        except PrematureStreamEndError:
            _LOGGER.warning("Stack stream was closed prematurely (OOM?)")
