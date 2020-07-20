#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019, 2020 Fridolin Pokorny
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

"""Definition of package resolution based on precomputed data available in graph.

There are defined primitives required for offline resolution. This off-line
resolution is done based on data aggregated in the graph database so thereis
no need to perform resolving by actually installing Python packages (as this
version resolution is dynamic in case of Python).
"""

from typing import List
from typing import Dict
from typing import Generator
from typing import Tuple
from typing import Set

import attr
from packaging.requirements import Requirement
from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages import GraphDatabase
from thoth.solver.python.base import DependencyParser
from thoth.solver.python.base import ReleasesFetcher
from thoth.solver.python.base import Solver
from thoth.solver.python import PythonDependencyParser


@attr.s(slots=True)
class GraphReleasesFetcher(ReleasesFetcher):  # type: ignore
    """Fetch releases for packages from the graph database."""

    graph = attr.ib(type=GraphDatabase, kw_only=True)
    runtime_environment = attr.ib(
        type=RuntimeEnvironment, default=attr.Factory(RuntimeEnvironment.from_dict), kw_only=True,
    )

    def fetch_releases(self, package_name: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Fetch releases for the given package name."""
        # Make sure we have normalized names in the graph database according to PEP:
        #   https://www.python.org/dev/peps/pep-0503/#normalized-names
        package_name = Source.normalize_package_name(package_name)

        start_offset = 0
        result: Set[Tuple[str, str, str]] = set()
        while True:
            query_result = self.graph.get_solved_python_package_versions_all(
                package_name=package_name,
                os_name=self.runtime_environment.operating_system.name,
                os_version=self.runtime_environment.operating_system.version,
                python_version=self.runtime_environment.python_version,
                start_offset=start_offset,
                count=self.graph.DEFAULT_COUNT,
                distinct=True,
                is_missing=False,
            )

            start_offset += 1
            result.update(query_result)

            # We have reached end of pagination or no versions were found.
            if len(query_result) < self.graph.DEFAULT_COUNT:
                break

        return package_name, [(version, index_url) for _, version, index_url in result]


@attr.s(slots=True)
class PackageVersionDependencyParser(DependencyParser):  # type: ignore
    """Parse an instance of PackageVersion to Dependency object needed by solver."""

    def parse(self, dependencies: List[PackageVersion]) -> Generator[Requirement, None, None]:
        """Parse the given list of PackageVersion objects."""
        for package_version in dependencies:
            version = package_version.version if package_version.version != "*" else ""
            dependency = PythonDependencyParser.parse_python(package_version.name + version)
            yield dependency


@attr.s(slots=True)
class PythonGraphSolver(Solver):  # type: ignore
    """Solve Python dependencies based on data available in the graph database."""

    dependency_parser = attr.ib(type=PackageVersionDependencyParser, kw_only=True)
    releases_fetcher = attr.ib(type=GraphReleasesFetcher, kw_only=True)


@attr.s(slots=True)
class PythonPackageGraphSolver:
    """A wrapper to manipulate with Python packages using pure PackageVersion object interface."""

    graph = attr.ib(type=GraphDatabase, kw_only=True)
    runtime_environment = attr.ib(
        type=RuntimeEnvironment, kw_only=True, default=attr.Factory(RuntimeEnvironment.from_dict),
    )
    # Do not instantiate multiple objects for same python package tuple to optimize memory usage.
    _package_versions = attr.ib(
        type=Dict[Tuple[str, str, str], PackageVersion], default=attr.Factory(dict), kw_only=True,
    )
    # Have just one instance of Source object per python package source index url.
    _sources = attr.ib(type=Dict[str, Source], default=attr.Factory(dict), kw_only=True)
    _solver = attr.ib(type=PythonGraphSolver, default=None, kw_only=True)

    @property
    def solver(self) -> PythonGraphSolver:
        """Retrieve solver instance resolving using graph database."""
        if not self._solver:
            self._solver = PythonGraphSolver(
                dependency_parser=PackageVersionDependencyParser(),
                releases_fetcher=GraphReleasesFetcher(graph=self.graph, runtime_environment=self.runtime_environment),
            )

        return self._solver

    def solve(self, dependencies: List[PackageVersion], graceful: bool = True) -> Dict[str, List[PackageVersion]]:
        """Solve the given dependencies and return object representation of packages."""
        result = {}
        # First, construct the map for checking packages.
        dependencies_map = {dependency.name: dependency for dependency in dependencies}

        resolved = self.solver.solve(dependencies, graceful=graceful)
        if not resolved:
            return {}

        for package_name, versions in resolved.items():
            # If this pop fails, it means that the package name has changed over the resolution.
            original_package = dependencies_map.pop(package_name)
            result_versions = []
            for version, index_url in versions:
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
