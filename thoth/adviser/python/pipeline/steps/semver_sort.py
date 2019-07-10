#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

"""Sort paths according to semver to preserve generation of packages - latest first."""

import logging
from functools import partial

from thoth.python import PackageVersion

from ..step import Step
from ..step_context import StepContext
from thoth.adviser.python.dependency_graph.adaptation import Edge
from thoth.adviser.python.pipeline.units import semver_cmp_package_version

_LOGGER = logging.getLogger(__name__)


class SemverSort(Step):
    """Sort paths based on semver."""

    @classmethod
    def _semver_cmp_function_path(
        cls, step_context: StepContext, edge1: Edge, edge2: Edge
    ) -> int:
        """Compare two edges and report which should take precedence.

        To have stacks sorted from latest down to oldest, ideally we should take into account package release
        date. We are approximating the sorting based on semver of packages. This means that a stack which is made
        of packages in the following versions:

        Basically, we sort serialized dependency graph (edges) based on target package tuples which makes sure
        all the nodes in dependency graph are sorted based on semver (root nodes have source None) down to leaf nodes.
        """
        if edge1.source is None and edge2.source is not None:
            return 1

        if edge2.source is None and edge1.source is not None:
            return -1

        if edge1.source is not None and edge2.source is not None:
            package_version1: PackageVersion = step_context.packages[
                edge1.source.package_tuple
            ]
            package_version2: PackageVersion = step_context.packages[
                edge2.source.package_tuple
            ]

            result = semver_cmp_package_version(package_version1, package_version2)
            if result != 0:
                return result

        package_version1: PackageVersion = step_context.packages[
            edge1.target.package_tuple
        ]
        package_version2: PackageVersion = step_context.packages[
            edge2.target.package_tuple
        ]

        return semver_cmp_package_version(package_version1, package_version2)

    def run(self, step_context: StepContext):
        """Sort paths in context based on semver of packages."""
        step_context.sort_paths(
            partial(self._semver_cmp_function_path, step_context), reverse=False
        )
