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

_LOGGER = logging.getLogger(__name__)


class SemverSort(Step):
    """Sort paths based on semver."""

    @classmethod
    def _semver_cmp_function_path(
        cls, step_context: StepContext, path1: list, path2: list
    ) -> int:
        """Compare two paths and report which should take precedence.

        To have stacks sorted from latest down to oldest, ideally we should take into account package release
        date. We are approximating the sorting based on semver of packages. This means that a stack which is made
        of packages in the following versions:
        """
        # Be interested in paths, omit scores.
        path1 = path1[1]
        path2 = path2[1]
        for idx in range(len(path1)):
            if idx >= len(path2):
                return -1

            package_version1 = step_context.get_package_version_tuple(path1[idx])
            package_version2 = step_context.get_package_version_tuple(path2[idx])
            cmp_result = cls._semver_cmp_function(package_version1, package_version2)
            if cmp_result != 0:
                return cmp_result

        # Same paths?! This should be probably unreachable but this can happen if we did not take into
        # account os or python version when querying graph database. We take this into account earlier.
        return 0

    @staticmethod
    def _semver_cmp_function(
        package_version1: PackageVersion, package_version2: PackageVersion
    ) -> int:
        """Compare two packages based on semver."""
        if package_version1.name != package_version2.name:
            # We call this function with reverse set to true, to have packages sorted alphabetically we
            # inverse logic here so package names are *really* sorted alphabetically.
            return -int(package_version1.name > package_version2.name) or 1
        elif package_version1 != package_version2:
            result = package_version1.semantic_version.__cmp__(
                package_version2.semantic_version
            )

            if result is NotImplemented:
                # Based on semver, this can happen if at least one has build
                # metadata - there is no ordering specified.
                if package_version1.semantic_version.build:
                    return -1
                return 1

            return result
        elif package_version1.index.url != package_version2.index.url:
            return -int(package_version1.index_url < package_version2.index.url) or 1

        return 0

    def run(self, step_context: StepContext):
        """Sort paths in context based on semver of packages."""
        step_context.sort_paths(
            partial(self._semver_cmp_function_path, step_context), reverse=False
        )
        step_context.sort_direct_dependencies(self._semver_cmp_function, reverse=False)
