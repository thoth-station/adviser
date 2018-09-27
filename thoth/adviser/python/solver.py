#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""Definition of package resolution based on precomputed data available in graph.

There are defined primitives required for offline resolution. This off-line
resolution is done based on data aggregated in the graph database so thereis
no need to perform resolving by actually installing Python packages (as this
version resolution is dynamic in case of Python).
"""

import typing

from thoth.storages import GraphDatabase
from thoth.solver.solvers.base import Dependency
from thoth.solver.solvers.base import DependencyParser
from thoth.solver.solvers.base import ReleasesFetcher
from thoth.solver.solvers.base import Solver
from thoth.solver.python import PypiDependencyParser

from .package_version import PackageVersion


class GraphReleasesFetcher(ReleasesFetcher):
    """Fetch releases for packages from the graph database."""

    def __init__(self, **graph_db_kwargs: dict):
        """Initialize graph release fetcher."""
        super().__init__()
        self._graph_db_kwargs = graph_db_kwargs
        self._graph_db = None

    @property
    def graph_db():
        """Get instance of graph database adapter, lazily."""
        if not self._graph_db:
            self._graph_db = GraphDatabase(**self._graph_db_kwargs)

        return self._graph_db

    def fetch_releases(self, package):
        """Fetch releases for the given package name."""
        # TODO: pass index as well
        return self.graph_db.get_all_versions_python_package(package)


class PackageVersionDependencyParser(DependencyParser):
    """Parse an instance of PackageVersion to Dependency object needed by solver."""
    def parse(self, dependencies: typing.List[PackageVersion]):
        """Parse the given list of PackageVersion objects."""
        for package_version in dependencies:
            dependency = PypiDependencyParser.parse_python(dependency.name + dependency.version)[0]
            yield dependency


class PythonGraphSolver(Solver):
    """Solve Python dependencies based on data available in the graph database."""

    def __init__(self, parser_kwargs: dict = None, graph_db_kwargs: dict = None, solver_kwargs: dict = None):
        """Initialize instance."""
        super().__init__(
            PackageVersionDependencyParser(**(parser_kwargs or {})),
            GraphReleasesFetcher(**(graph_db_kwargs or {})),
            **(solver_kwargs or {})
        )
