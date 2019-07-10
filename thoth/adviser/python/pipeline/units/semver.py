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

from thoth.python import PackageVersion


def semver_cmp_package_version(
    package_version1: PackageVersion, package_version2: PackageVersion
) -> int:
    """Compare two packages based on semver."""
    if package_version1.name != package_version2.name:
        # We call this function with reverse set to true, to have packages sorted alphabetically we
        # inverse logic here so package names are *really* sorted alphabetically.
        return -int(package_version1.name > package_version2.name) or 1
    elif package_version1.locked_version != package_version2.locked_version:
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
        return -int(package_version1.index.url < package_version2.index.url) or 1

    return 0
