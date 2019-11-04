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
# TODO: enable typing once we release libs with typing
# type: ignore

"""Definition of package resolution based on precomputed data available in graph.

There are defined primitives required for offline resolution. This off-line
resolution is done based on data aggregated in the graph database so thereis
no need to perform resolving by actually installing Python packages (as this
version resolution is dynamic in case of Python).
"""

from typing import List
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.solver.python.base import DependencyParser
from thoth.solver.python.base import ReleasesFetcher
from thoth.solver.python.base import Solver
from thoth.solver.python.base import SolverException
from thoth.solver.python import PythonDependencyParser


if TYPE_CHECKING:
    from thoth.storages import GraphDatabase


class GraphReleasesFetcher(ReleasesFetcher):
    """Fetch releases for packages from the graph database."""

    def __init__(
        self,
        *,
        runtime_environment: Optional[RuntimeEnvironment] = None,
        graph_db: Optional["GraphDatabase"] = None,
    ) -> None:
        """Initialize graph release fetcher."""
        super().__init__()
        self._graph_db = graph_db
        self.runtime_environment = runtime_environment or RuntimeEnvironment.from_dict(
            {}
        )

    @property
    def graph_db(self) -> "GraphDatabase":
        """Get instance of graph database adapter, lazily."""
        # Place the import statement here to simplify mocks in the testsuite.
        from thoth.storages import GraphDatabase

        if not self._graph_db:
            self._graph_db = GraphDatabase()
            self._graph_db.connect()

        return self._graph_db

    def fetch_releases(self, package_name: str):
        """Fetch releases for the given package name."""
        # Make sure we have normalized names in the graph database according to PEP:
        #   https://www.python.org/dev/peps/pep-0503/#normalized-names
        package_name = Source.normalize_package_name(package_name)

        start_offset = 0
        result = set()
        while True:
            query_result = self.graph_db.get_solved_python_package_versions_all(
                package_name=package_name,
                os_name=self.runtime_environment.operating_system.name,
                os_version=self.runtime_environment.operating_system.version,
                python_version=self.runtime_environment.python_version,
                start_offset=start_offset,
                count=self.graph_db.DEFAULT_COUNT,
                distinct=True,
            )

            start_offset += 1
            result.update(query_result)

            # We have reached end of pagination or no versions were found.
            if len(query_result) < self.graph_db.DEFAULT_COUNT:
                break

        return package_name, [(version, index_url) for _, version, index_url in result]


class PackageVersionDependencyParser(DependencyParser):
    """Parse an instance of PackageVersion to Dependency object needed by solver."""

    def parse(self, dependencies: List[PackageVersion]):
        """Parse the given list of PackageVersion objects."""
        for package_version in dependencies:
            version = package_version.version if package_version.version != "*" else ""
            dependency = PythonDependencyParser.parse_python(
                package_version.name + version
            )
            yield dependency


class PythonGraphSolver(Solver):
    """Solve Python dependencies based on data available in the graph database."""

    def __init__(
        self,
        *,
        parser_kwargs: dict = None,
        graph_db=None,
        runtime_environment=None,
        solver_kwargs: dict = None,
    ):
        """Initialize instance."""
        super().__init__(
            PackageVersionDependencyParser(**(parser_kwargs or {})),
            GraphReleasesFetcher(
                graph_db=graph_db, runtime_environment=runtime_environment
            ),
            **(solver_kwargs or {}),
        )


class PythonPackageGraphSolver:
    """A wrapper to manipulate with Python packages using pure PackageVersion object interface."""

    def __init__(
        self,
        *,
        parser_kwargs: dict = None,
        graph_db: dict = None,
        solver_kwargs: dict = None,
        runtime_environment: RuntimeEnvironment = None,
    ):
        """Get instance of the graph solver."""
        self._solver = PythonGraphSolver(
            parser_kwargs=parser_kwargs,
            graph_db=graph_db,
            solver_kwargs=solver_kwargs,
            runtime_environment=runtime_environment,
        )
        # Do not instantiate multiple objects for same python package tuple to optimize memory usage.
        self._package_versions = {}
        # Have just one instance of Source object per python package source index url.
        self._sources = {}

    def solve(
        self,
        dependencies: List[PackageVersion],
        graceful: bool = True,
        all_versions: bool = False,
    ) -> Dict[str, List[PackageVersion]]:
        """Solve the given dependencies and return object representation of packages."""
        # A fast path - if there is only one package we can directly rely on solving.
        # If there are multiple packages to be solved, construct a dictionary to optimize to
        # O(1) for PackageVersion construction.
        #
        # Note changes in interface of solver - if there is all_versions passed, the
        # resulting values is a list, otherwise string directly.
        result = {}
        if len(dependencies) <= 1:
            resolved = self._solver.solve(
                dependencies, graceful=graceful, all_versions=all_versions
            )

            if not resolved:
                return resolved

            if len(resolved) != 1:
                # It's ok, len(resolved) == 0 should be handled in the if above.
                raise SolverException(
                    f"Multiple packages resolved for one dependency {dependencies[0]!r}: {resolved!r}"
                )

            if all_versions:
                result[dependencies[0].name] = []

            for version, index_url in (
                list(resolved.values())[0] if all_versions else resolved.values()
            ):
                # We only change version attribute that will be the resolved one.
                package_tuple = (dependencies[0].name, version, index_url)
                package_version = self._package_versions.get(package_tuple)
                if not package_version:
                    source = self._sources.get(index_url)
                    if not source:
                        source = Source(index_url)
                        self._sources[index_url] = source

                    package_version = PackageVersion(
                        name=dependencies[0].name,
                        version="==" + version,
                        index=source,
                        develop=dependencies[0].develop,
                    )
                    self._package_versions[package_tuple] = package_version

                if all_versions:
                    result[package_version.name].append(package_version)
                else:
                    result[package_version.name] = [package_version]
        else:
            # First, construct the map for checking packages.
            dependencies_map = {
                dependency.name: dependency for dependency in dependencies
            }

            resolved = self._solver.solve(
                dependencies, graceful=graceful, all_versions=all_versions
            )
            if not resolved:
                return resolved

            for package_name, versions in resolved.items():
                # If this pop fails, it means that the package name has changed over the resolution.
                original_package = dependencies_map.pop(package_name)
                result_versions = []
                for version, index_url in versions if all_versions else [versions]:
                    package_tuple = (original_package.name, version, index_url)
                    package_version = self._package_versions.get(package_tuple)
                    if not package_version:
                        source = self._sources.get(index_url)
                        if not source:
                            source = Source(index_url)
                            self._sources[index_url] = source

                        package_version = PackageVersion(
                            name=original_package.name,
                            version="==" + version,
                            index=source,
                            develop=original_package.develop,
                        )

                    result_versions.append(package_version)

                result[original_package.name] = result_versions

        return result
