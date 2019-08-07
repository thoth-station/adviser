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

"""Implementation of sieve context base class."""

from typing import List
from typing import Tuple
from typing import Generator
import logging
from thoth.python import PackageVersion

import attr

from .context_base import ContextBase
from .exceptions import CannotRemovePackage
from .exceptions import PackageNotFound

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SieveContext(ContextBase):
    """A wrapper for sieves encapsulating common logic for operations performed by sieves."""

    packages = attr.ib(type=dict, default=attr.Factory(dict))

    @classmethod
    def from_package_versions(cls, package_versions: List[PackageVersion]) -> "SieveContext":
        """Instantiate from a list of package-versions."""
        packages_dict = dict.fromkeys(
            (package_version.name for package_version in package_versions),
            {}
        )

        for package_version in package_versions:
            if not packages_dict[package_version.name]:
                packages_dict[package_version.name] = {}

            packages_dict[package_version.name][package_version.to_tuple()] = package_version

        return cls(packages=packages_dict)

    def remove_package_tuple(self, package_tuple: Tuple[str, str, str]) -> None:
        """Remove the given package tuple."""
        if package_tuple not in self.packages.get(package_tuple[0], {}):
            raise PackageNotFound("Package %r was not found in sieve context", package_tuple)

        if len(self.packages[package_tuple[0]]) <= 1:
            raise CannotRemovePackage(
                "Cannot remove package %r - by removing this package all direct "
                "dependencies of package %r would be removed",
                package_tuple,
                package_tuple[0]
            )

        self.packages[package_tuple[0]].pop(package_tuple)

    def remove_package(self, package_version: PackageVersion) -> None:
        """Remove package-versions - a syntax sugar for remove_package_tuple."""
        self.remove_package_tuple(package_version.to_tuple())

    def iter_direct_dependencies(self, develop: bool = None) -> Generator[PackageVersion, None, None]:
        """Iterate over direct dependencies, respect their ordering."""
        for package_tuple in self.iter_direct_dependencies_tuple():
            package_version = self.packages[package_tuple[0]][package_tuple]
            if develop is not None:
                if package_version.develop == develop:
                    yield package_version
            else:
                yield package_version

    def iter_direct_dependencies_tuple(
        self,
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over direct dependencies, respect their ordering and return a package tuple."""
        for entry in self.packages.values():
            for package_tuple in entry.keys():
                yield package_tuple
