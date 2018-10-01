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
import semantic_version as semver

from thoth.adviser.exceptions import UnsupportedConfiguration
from thoth.adviser.exceptions import PipfileParseError
from thoth.adviser.exceptions import InternalError
from thoth.storages.graph import PythonPackageVersion as PackageVersionModel

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
    _semantic_version = attr.ib(default=None, type=semver.Version)
    _version_spec = attr.ib(default=None, type=semver.Spec)

    def __eq__(self, other):
        """Check for package-version equality."""
        return self.name == other.name and self.version == other.version and self.hashes == other.hashes

    def __lt__(self, other):
        """Compare same packages based on their semantic version."""
        if self.name != other.name:
            raise ValueError(f"Comparing package versions of different package - {self.name} and {other.name}")

        return self.semantic_version < other.semantic_version

    def __gt__(self, other):
        """Compare same packages based on their semantic version."""
        if self.name != other.name:
            raise ValueError(f"Comparing package versions of different package - {self.name} and {other.name}")

        return self.semantic_version > other.semantic_version

    @classmethod
    def from_model(model: PackageVersionModel, *, develop: bool = False):
        """Convert database model representation to object representation."""
        # TODO: add markers to the graph database
        # TODO: add hashes to the graph database
        return cls(
            name=model.package_name,
            version=model.package_version,
            develop=develop,
            index=model.index
        )

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
                f"Negating version on non-locked package {self.name} with version {self.version} is not supported"
            )

        self.version = '!' + self.version[1:]

    @property
    def locked_version(self) -> str:
        """Retrieve locked version of the package."""
        if not self.is_locked():
            raise InternalError(
                f"Requested locked version for {self.name} but package has no locked version {self.version}"
            )

        return self.version[len('=='):]

    @property
    def semantic_version(self) -> semver.Version:
        """Get semantic version respecting version specified - package has to be locked to a specific version."""
        if not self._semantic_version:
            if not self.is_locked():
                raise InternalError(
                    f"Cannot get semantic version for not-locked package {self.name} in version {self.version}"
                )

            try:
                self._semantic_version = semver.Version(self.locked_version)
            except Exception as exc:
                self._semantic_version = semver.Version.coerce(self.locked_version)
                _LOGGER.warning(
                    f"Cannot determine semantic version for package {self.name} in version {self.locked_version}, "
                    f"approximated version is {self._semantic_version}: {str(exc)})"
                )

        return self._semantic_version

    @property
    def version_specification(self) -> semver.Spec:
        """Retrieve version specification based on specified version."""
        if not self._version_spec:
            self._version_spec = semver.Spec(self.version)

        return self._version_spec

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
