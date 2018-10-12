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

"""Representation of development and default packages as stated in Pipfile and Pipfile.lock."""

import typing
import logging

import attr

from .package_version import PackageVersion
from thoth.adviser.exceptions import InternalError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Packages:
    """Encapsulate logic on package manipulation."""

    develop = attr.ib(type=bool)
    packages = attr.ib(type=dict)

    def is_develop(self):
        """Check if packages provided by this instance are development packages."""
        return self.develop

    def is_default(self):
        """Check if packages provided by this instance are dependencies of application packages."""
        return not self.develop

    def to_pipfile(self) -> dict:
        """Convert packages representation as seen in Pipfile file."""
        _LOGGER.debug("Generating Pipfile entry for packages (develop: %s)", self.develop)
        result = {}
        for package_name, package_version in self.packages.items():
            result.update(package_version.to_pipfile())

        return result

    def to_pipfile_lock(self) -> dict:
        """Convert packages representation as seen in Pipfile.lock file."""
        _LOGGER.debug("Generating Pipfile.lock entry for packages (develop: %s)", self.develop)
        result = {}
        for package_name, package_version in self.packages.items():
            result.update(package_version.to_pipfile_lock())

        return result

    @classmethod
    def from_pipfile(cls, packages, develop, meta):
        """Parse Pipfile entry stating list of packages used."""
        _LOGGER.debug("Parsing Pipfile entry for %s packages", 'develop' if develop else 'default')
        package_version = {}
        for package_name, package_info in packages.items():
            package_version[package_name] = PackageVersion.from_pipfile_entry(
                package_name,
                package_info,
                develop,
                meta
            )

        return cls(develop=develop, packages=package_version)

    @classmethod
    def from_pipfile_lock(cls, packages, develop, meta):
        """Parse Pipfile.lock entry stating list of packages used."""
        _LOGGER.debug("Parsing Pipfile.lock entry for %s packages", 'develop' if develop else 'default')
        package_version = {}
        for package_name, package_info in packages.items():
            package_version[package_name] = PackageVersion.from_pipfile_lock_entry(
                package_name,
                package_info,
                develop,
                meta
            )

        return cls(develop=develop, packages=package_version)

    def __iter__(self):
        """Iterate over packages encapsulated by this wrapper."""
        yield from self.packages.values()

    def get(self, package_name: str) -> typing.Optional[PackageVersion]:
        """Get package by its name."""
        return self.packages.get(package_name)

    def __setitem__(self, package_name: str, package_version: PackageVersion) -> None:
        """Set the given package to a value."""
        self.packages[package_name] = package_version

    def __getitem__(self, item):
        """Get the given package from section."""
        return self.packages[item]

    def add_package_version(self, package_version: PackageVersion):
        """Add the given package version to package list."""
        if (package_version.develop and not self.develop) or (not package_version.develop and self.develop):
            raise InternalError(
                f"Adding package {package_version!r} to package listing without proper develop flag"
            )

        if package_version.name in self.packages:
            raise InternalError(
                f"Adding package {package_version!r} to packages, but this package is already present there"
            )

        self.packages[package_version.name] = package_version
