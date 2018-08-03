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

"""Project abstraction and operations on project dependencies."""

import logging
import typing
from itertools import chain
from copy import copy
import tempfile

import attr
from thoth.common import cwd
from thoth.analyzer import run_command
from thoth.storages import GraphDatabase

from .pipfile import Pipfile, PipfileLock
from .package_version import PackageVersion
from ..enums import RecommendationType
from ..exceptions import InternalError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Project:
    """A representation of a Python project."""

    pipfile = attr.ib(type=Pipfile)
    pipfile_lock = attr.ib(type=PipfileLock)
    _graph_db = attr.ib(default=None)
    _workdir = attr.ib(default=None)

    @property
    def graph_db(self) -> GraphDatabase:
        """Access connected graph adapter."""
        if self._graph_db:
            return self._graph_db

        self._graph_db = GraphDatabase()
        self._graph_db.connect()
        return self._graph_db

    @property
    def workdir(self) -> str:
        """Access working directory of project."""
        if self._workdir:
            return self._workdir

        self._workdir = tempfile.mkdtemp()
        return self._workdir

    def pipenv_lock(self):
        """Perform pipenv lock on the current state of project."""
        with cwd(self.workdir):
            self.pipfile.to_file()
            print(self.pipfile.to_dict())
            _LOGGER.debug('Running pipenv lock')
            result = run_command('pipenv lock')
            _LOGGER.debug("pipenv stdout:\n%s", result.stdout)
            _LOGGER.debug("pipenv stderr:\n%s", result.stderr)
            self.pipfile_lock = PipfileLock.from_file(pipfile=self.pipfile)
            print(self.pipfile_lock.to_dict())

    def is_direct_dependency(self, package_version: PackageVersion) -> bool:
        """Check whether the given package is a direct dependency."""
        return package_version.name in self.pipfile.packages

    def exclude_package(self, package_version: PackageVersion) -> None:
        """Exclude the given package from application stack.

        @raises
        """
        if not package_version.is_locked():
            raise InternalError("Cannot exclude package not pinned down to specific version: %r", package_version)

        section = self.pipfile.dev_packages if package_version.develop else self.pipfile.packages

        to_exclude_package = section.get(package_version.name)
        if to_exclude_package:
            package_version.negate_version()
            _LOGGER.debug(f"Excluding package %r with package specified %r", to_exclude_package, package_version)

            if package_version.index != to_exclude_package.index:
                _LOGGER.warning(
                    f"Excluding package {to_exclude_package} with {package_version} but package has "
                    f"different index configuration"
                )

            if package_version.markers != to_exclude_package:
                _LOGGER.warning(
                    f"Excluding package {to_exclude_package} with {package_version} but package has "
                    f"different markers configured"
                )

            # We do operations on the package we passed via parameters so the original package is
            # not adjusted if referenced elsewhere.
            if to_exclude_package.version != '*':
                package_version.version = f"{package_version.version},{to_exclude_package.version}"
            _LOGGER.debug("Package with excluded version %r", package_version)
            section[package_version.name] = package_version
        else:
            # Adding a new requirement.
            package_version.negate_version()
            section[package_version.name] = package_version
            _LOGGER.debug("Added excluded package to pipfile configuration: %r", package_version)

        self.pipenv_lock()

    def is_bad_package(self, package_version: PackageVersion,
                       recommendation_type: RecommendationType) -> typing.Optional[dict]:
        """Exclude the given package from application stack."""
        # Always exclude packages that have CVEs regardless of recommendation type.
        if not package_version.is_locked():
            raise InternalError("Trying to inspect package quality without specifying proper package version")

        cves = self.graph_db.get_python_cve_records(package_version.name, package_version.locked_version)
        if cves:
            vulnerabilities = list(map(lambda x: x.to_dict(), cves))
            _LOGGER.info("Excluding package %r due to CVEs found: %r", package_version, vulnerabilities)
            return {
                'type': 'CVE',
                'package_name': package_version.name,
                'package_version': package_version.locked_version,
                'justification': 'Package was removed due to found CVE',
                'value': vulnerabilities
            }

        if recommendation_type == recommendation_type.STABLE:
            if not self.graph_db.python_package_version_exists(package_version.name, package_version.locked_version):
                return {
                    'type': 'UNANALYZED',
                    'package_name': package_version.name,
                    'package_version': package_version.locked_version,
                    'justification': 'No record for the given package found'
                }
            # Check for packages we have in the graph database - we have records about them.
            # If the given package was bad - was it removed?
            return None
        elif recommendation_type in (recommendation_type.TESTING, recommendation_type.LATEST):
            # We do not have any bad records for this package, meaning we can continue with it in case
            # of testing and latest.
            return None

        raise NotImplementedError  # Unreachable.

    def advise(self, runtime_environment: str, recommendation_type: RecommendationType) -> list:
        """Compute recommendations for the given runtime environment."""
        _LOGGER.debug(
            "Computing recommendations for runtime environment %s (type: %s)",
            runtime_environment, recommendation_type.name
        )

        if recommendation_type == RecommendationType.LATEST:
            self.pipenv_lock()
            return [{
                'type': 'LATEST',
                'justification': 'All packages were locked to their latest version'
            }]

        # User did not provided Pipfile.lock on input - let's start with the latest one.
        if not self.pipfile_lock:
            self.pipenv_lock()

        report = []
        change = True
        pipfile_copy = copy(self.pipfile)
        while change:
            change = False

            for package_version in chain(self.pipfile_lock.packages, self.pipfile_lock.dev_packages):
                bad_package_report = self.is_bad_package(package_version, recommendation_type)
                if bad_package_report:
                    # Perform copy() to avoid changes on packages the Pipfile.lock.
                    self.exclude_package(package_version.duplicate())
                    report.append(bad_package_report)
                    change = True
                    break

        # Do not touch pipfile that was provided by user. If there is any change in observations we have,
        # the algorithm above respects these changes. Otherwise it always results with the same stack given
        # the observations we have and user's input.
        self.pipfile = pipfile_copy
        return report
