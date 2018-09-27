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

import attr

from .dependency_graph import DependencyGraph
from .package_version import PackageVersion
from .project import Project
from .solver import PythonGraphSolver


@attr.s(slots=True)
class GraphItem(PackageVersion):
    """Extend PackageVersion with a link to resolved dependencies of the given package version."""

    dependencies = attr.ib(default=attr.Factory(list))


@attr.s(slots=True)
class DependencyGraph:
    """N-ary dependency graph stored in memory."""

    direct_dependencies = attr.ib(type=typing.List[typing.List[GraphItem]])

    @staticmethod
    def _prepare_direct_dependencies(solver: PythonGraphSolver, project: Project,
                                     with_devel: bool) -> typing.List[typing.List[GraphItem]]:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        direct_dependencies_map = {pv.name: pv for pv in project.iter_dependencies(with_devel=with_devel)}

        resolved_direct_dependencies = solver.solve(
            direct_dependencies_map.values(),
            graceful=False,
            all_versions=True
        )

        direct_dependencies = []
        for dependency_name, versions in resolved_direct_dependencies.items():
            direct_dependency_versions = []
            for version in versions:
                direct_dependency_versions.append(
                    GraphItem(
                        name=dependency_name,
                        version='==' + version,
                        index=direct_dependencies_map[dependency_name].index
                    )
                )
            direct_dependencies.append(direct_dependency_versions)

        return direct_dependency_versions, direct_dependencies_map

    @classmethod
    def from_project(cls, project: Project, with_devel: bool = False):
        """Construct a dependency graph from a project."""
        # Graph should be a parameter - we want only one instance.
        solver = PythonGraphSolver()
        direct_dependencies, dependencies_map = cls._prepare_direct_dependencies(
            solver,
            project,
            with_devel=with_devel
        )

        # Now resolve all the transitive dependencies.
        to_resolve = deque(chain(*direct_dependencies))
        for package_version in to_resolve:
            transitive_dependencies = graph.retrieve_dependencies(
                package_version.name,
                package_version.version,
                package_version.index
            )

            for transitive_dependency_name, transitive_dependency_versions in transitive_dependencies.items():
                # Tackle cyclic dependencies - create cycle in the graph.
                for version in transitive_dependency_versions:
                    if transitive_dependency_name in dependencies_map:
                        package_version.dependencies.append(dependenies_map[transitive_dependency_name])
                        continue

                    item = GraphItem(
                        name=transitive_dependency_name,
                        version='==' + version,
                        # TODO: we should propagate index here from the graph query
                        index=None
                    )
                    package_version.dependencies.append(item)
                    dependencies_map[transitive_dependency_name] = item

        # sort each layer in the constructed graph so walking of graph gives same stacks in the same order
        # for the same data
        for package in dependencies_map.items():
            # TODO: there can be raised an exception if versions could not be sorted based on semver
            package.dependencies = sorted(package.dependencies, reverse=True)

        return cls(direct_dependencies)

    def walk(self):
        pass
