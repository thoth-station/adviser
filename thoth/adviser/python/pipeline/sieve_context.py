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
from typing import Callable
from functools import cmp_to_key
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

    @staticmethod
    def _construct_packages_dict(package_versions: List[PackageVersion]) -> dict:
        """Construct dict as stored in this sieve context."""
        packages_dict = dict.fromkeys(
            (package_version.name for package_version in package_versions),
            {}
        )

        for package_version in package_versions:
            if not packages_dict[package_version.name]:
                packages_dict[package_version.name] = {}

            packages_dict[package_version.name][package_version.to_tuple()] = package_version

        return packages_dict

    @classmethod
    def from_package_versions(cls, package_versions: List[PackageVersion]) -> "SieveContext":
        """Instantiate from a list of package-versions."""
        return cls(packages=cls._construct_packages_dict(package_versions))

    def remove_package_tuple(self, package_tuple: Tuple[str, str, str]) -> None:
        """Remove the given package tuple."""
        if package_tuple not in self.packages.get(package_tuple[0], {}):
            raise PackageNotFound("Package %r was not found in sieve context", package_tuple)

        if len(self.packages[package_tuple[0]]) <= 1:
            raise CannotRemovePackage(
                f"Cannot remove package {package_tuple!r} - by removing this package all direct "
                f"dependencies of package {package_tuple[0]!r} would be removed",
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

    def sort_packages(
        self,
        comparision_func: Callable[[PackageVersion, PackageVersion], int],
        reverse: bool = True,
    ) -> None:
        """Sort packages based on the comparision function.

        The sorting is stable, meaning, it reflects previous relative order of packages so its completely
        fine to perform multiple sorts in sieves - the more recent sieve will have higher priority.
        """
        # We expect Python 3.6+ where order in dict is preserved.
        packages = []
        for package_name in self.packages:
            for package_version in self.packages[package_name].values():
                packages.append(package_version)

        packages.sort(reverse=reverse, key=cmp_to_key(comparision_func))
        self.packages = self._construct_packages_dict(packages)
