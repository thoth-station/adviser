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

"""Representation of packages in the application stack."""

import logging
from copy import copy

import attr

from thoth.adviser.exceptions import UnsupportedConfiguration
from thoth.adviser.exceptions import PipfileParseError
from thoth.adviser.exceptions import InternalError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PackageVersion:
    """A package version as described in the Pipfile.lock entry."""

    name = attr.ib(type=str)
    version = attr.ib(type=str)
    develop = attr.ib(type=bool)
    index = attr.ib(default=None, type=str)
    hashes = attr.ib(default=attr.Factory(list))
    markers = attr.ib(default=None, type=str)

    def is_locked(self):
        """Check if the given package is locked to a specific version."""
        return self.version.startswith('==')

    def duplicate(self):
        """Duplicate the given package safely when performing changes in resolution."""
        return PackageVersion(
            name=self.name,
            version=copy(self.version),
            develop=self.develop,
            index=self.index,
            hashes=self.hashes,
            markers=self.markers
        )

    def negate_version(self) -> None:
        """Negate version of a locked package version."""
        if not self.is_locked():
            raise InternalError(
                "Negating version on non-locked package {self.name} with version {self.version} is not supported"
            )

        self.version = '!' + self.version[1:]

    @property
    def locked_version(self):
        """Retrieve locked version of the package."""
        if not self.is_locked():
            raise InternalError(
                "Requested locked version for {self.name} but package has no locked version {self.version}"
            )

        return self.version[len('=='):]

    @classmethod
    def from_pipfile_lock_entry(cls, package_name: str, entry: dict, develop: bool):
        """Construct PackageVersion instance from representation as stated in Pipfile.lock."""
        _LOGGER.debug("Parsing entry in Pipfile.lock for package %r: %s", package_name, entry)
        entry = dict(entry)

        if any(not entry.get(conf) for conf in ('version', 'hashes')):
            raise PipfileParseError(
                f"Package {package_name} has missing or empty configuration in the locked entry: {entry}"
            )

        instance = cls(
            name=package_name,
            version=entry.pop('version'),
            index=entry.pop('index', None),
            hashes=entry.pop('hashes'),
            markers=entry.pop('markers', None),
            develop=develop
        )

        if entry:
            _LOGGER.warning(f"Unused entries when parsing Pipfile.lock for package {package_name}: {entry}")

        return instance

    def to_pipfile_lock(self) -> dict:
        """Create an entry as stored in the Pipfile.lock."""
        _LOGGER.debug("Generating Pipfile.lock entry for package %r", self.name)

        if not self.is_locked():
            raise InternalError(f"Trying to generate Pipfile.lock with packages not correctly locked: {self}")

        if not self.hashes:
            raise InternalError(f"Trying to generate Pipfile.lock without assigned hashes for package: {self}")

        result = {
            'version': self.version,
            'hashes': self.hashes,
        }

        if self.markers:
            result['markers'] = self.markers

        if self.index:
            result['index'] = self.index

        return {self.name: result}

    def to_pipfile(self):
        """Generate Pipfile entry for the given package."""
        _LOGGER.debug("Generating Pipfile entry for package %r", self.name)
        result = dict()
        if self.index:
            result['index'] = self.index

        if self.markers:
            result['markers'] = self.markers

        if not result:
            # Only version information is available.
            return {self.name: self.version}

        result['version'] = self.version
        return {self.name: result}

    @classmethod
    def from_pipfile_entry(cls, package_name: str, entry: dict, develop: bool):
        """Construct PackageVersion instance from representation as stated in Pipfile."""
        _LOGGER.debug("Parsing entry in Pipfile for package %r: %s", package_name, entry)
        index = None
        if isinstance(entry, str):
            package_version = entry
        else:
            if any(vcs in entry for vcs in ('git', 'hg', 'bzr', 'svn')):
                raise UnsupportedConfiguration(
                    f"Package {package_name} uses a version control system instead of package index: {entry}"
                )

            package_version = entry.pop('version')
            index = entry.pop('index', None)
            # TODO: raise an error if VCS is in use - we do not do recommendation on these
            if entry:
                _LOGGER.warning("Unparsed part of Pipfile: %s", entry)

        instance = cls(
            name=package_name,
            version=package_version,
            index=index,
            develop=develop
        )

        return instance
