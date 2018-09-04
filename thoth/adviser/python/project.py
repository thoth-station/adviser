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
from ..exceptions import NotFound

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
            _LOGGER.debug('Running pipenv lock')
            result = run_command('pipenv lock')
            _LOGGER.debug("pipenv stdout:\n%s", result.stdout)
            _LOGGER.debug("pipenv stderr:\n%s", result.stderr)
            self.pipfile_lock = PipfileLock.from_file(pipfile=self.pipfile)

    def is_direct_dependency(self, package_version: PackageVersion) -> bool:
        """Check whether the given package is a direct dependency."""
        return package_version.name in self.pipfile.packages

    def get_locked_package_version(self, package_name: str) -> typing.Optional[PackageVersion]:
        """Get locked version of the package."""
        package_version = self.pipfile_lock.dev_packages.get(package_name)

        if not package_version:
            package_version = self.pipfile_lock.packages.get(package_name)

        return package_version

    def get_package_version(self, package_name: str) -> typing.Optional[PackageVersion]:
        """Get locked version of the package."""
        package_version = self.pipfile.dev_packages.get(package_name)

        if not package_version:
            package_version = self.pipfile.packages.get(package_name)

        return package_version

    def exclude_package(self, package_version: PackageVersion) -> None:
        """Exclude the given package from application stack."""
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

    def _check_sources(self, whitelisted_sources: list) -> list:
        """Check sources configuration in the Pipfile and report back any issues."""
        report = []
        for source in self.pipfile.meta.sources.values():
            if whitelisted_sources and source.url not in whitelisted_sources:
                report.append({
                    'severity': 'ERROR',
                    'type': 'NOT-WHITELISTED',
                    'justification': 'Provided index is not stated in the whitelisted package sources listing',
                    'source': source.to_dict(),
                })
            elif not source.verify_ssl:
                report.append({
                    'severity': 'WARNING',
                    'type': 'INSECURE',
                    'justification': 'Source does not use SSL/TLS verification',
                    'source': source.to_dict(),
                })

        return report

    def _index_scan(self) -> typing.Tuple[list, dict]:
        """Generate full report for packages given the sources configured."""
        report = {}
        findings = []
        for package_version in chain(self.pipfile_lock.packages, self.pipfile_lock.dev_packages):
            if package_version.name in report:
                raise InternalError(f"Package {package_version.name} already present in the report")

            index_report = {}
            for source in self.pipfile.meta.sources.values():
                try:
                    index_report[source.name] = source.get_package_hashes(
                        package_version.name,
                        package_version.locked_version
                    )
                except NotFound as exc:
                    _LOGGER.debug(
                        f"Package {package_version.name} in version {package_version.version} not "
                        f"found on index {source.name}: {str(exc)}"
                    )

            findings.extend(self._check_scan(package_version, index_report))
            report[package_version.name] = index_report

        return findings, report

    def _check_scan(self, package_version: PackageVersion, index_report: dict) -> list:
        """Find and report errors found in the index scan."""
        """
            pipfile_lock_sha_entry = f"sha256:{artifact_info['sha256']}"
            artifact_info['used'] = pipfile_lock_sha_entry in package_version.hashes
                    'excluded': bool(package_version.index) and package_version.index != source.name,
        """
        scan_report = []

        # Holds None if the given package is not direct dependency otherwise Pipfile entry.
        package = self.get_package_version(package_version.name)
        if package:
            package = package.to_pipfile()

        # Prepare hashes for inspection.
        hashes = []
        pipenv_style_hashes = []
        for entry in index_report.values():
            hashes.append([item['sha256'] for item in entry])
            pipenv_style_hashes.append([f"sha256:{item['sha256']}" for item in entry])

        if not package_version.index and len(hashes) > 1:
            # There are indexes with different artifacts present - suggest to specify index explicitly.
            if set(chain(*hashes)) != set(hashes[0]):
                scan_report.append({
                    'severity': 'WARNING',
                    'type': 'DIFFERENT-ARTIFACTS-ON-SOURCES',
                    'justification': f'Configured sources have different artifacts '
                                     f'available, specify explicitly source to be '
                                     f'used',
                    'package_locked': package_version.to_pipfile_lock(),
                    'package': package,
                    'sources': index_report
                })
                # TODO: add fixes

        if package_version.index and index_report.get(package_version.index) and len(hashes) > 1:
            # Is installed from different source - which one?
            sources = {}
            for artifact_hash in package_version.hashes:
                artifact_hash = artifact_hash[len('sha256:'):]  # Remove pipenv-specific hash formatting.

                for index_name, index_info in index_report.items():
                    if index_name == package_version.index:
                        # Skip index that is assigned to the package, we are inspecting from the other sources.
                        continue

                    artifact_entry = [
                        (i['name'], i['sha256']) for i in index_info.values()
                        if i['sha256'] == artifact_hash
                    ]

                    assert len(artifact_entry) < 2
                    if artifact_entry and artifact_hash == artifact_entry[1]:
                        if index_name not in sources:
                            sources[index_name] = []

                        sources[index_name].append({
                            'name': artifact_entry[1],
                            'hash': artifact_hash
                        })

            raw_package_version_hashes = [h[len('sha256:'):] for h in package_version.hashes]
            configured_index_hashes = set(h['sha2565'] for h in index_report[package_version.index_name].values())
            if sources and not set(raw_package_version_hashes).issubset(set(configured_index_hashes)):
                # Source is different from the configured one.
                scan_report.append({
                    'severity': 'ERROR',
                    'type': 'ARTIFACT-DIFFERENT-SOURCE',
                    'justification': 'Artifacts are installed from different sources not respecting configuration',
                    'source': self.pipfile.meta.sources[package_version.index_name].to_dict(),
                    'package_locked': package_version.to_pipfile_lock(),
                    'package': package,
                    'sources': sources
                })
            elif sources:
                # Warn about possible installation from another source.
                scan_report.append({
                    'severity': 'WARNING',
                    'type': 'ARTIFACT-DIFFERENT-SOURCE',
                    'justification': 'Artifacts can be installed from different sources not '
                                     'respecting configuration',
                    'source': self.pipfile.meta.sources[package_version.index_name].to_dict(),
                    'package_locked': package_version.to_pipfile_lock(),
                    'package': package,
                    'sources': sources
                })

        if package_version.index and not index_report.get(package_version.index):
            # Configured index does not provide the given package.
            scan_report.append({
                'severity': 'ERROR',
                'type': 'MISSING-PACKAGE',
                'justification': f'Source index {package_version.index} explicitly '
                                 f'assigned to package {package_version.name} but package '
                                 f'was not found on index (was it removed?)',
                'source': self.pipfile.meta.sources[package_version.index].to_dict(),
                'package_locked': package_version.to_pipfile_lock(),
                'package': package,
                'sources': index_report
            })

        return scan_report

        # Changed hashes?
        if set(package_version.hashes):
            ({
                'severity': 'ERROR',
                'type': 'INVALID-ARTIFACT-HASH',
                'justification': 'Package changed its digest',
                'source': self.pipfile.meta.sources[source_name].to_dict(),
                'package_locked': package_version.to_pipfile_lock(),
                'package': self.get_package_version(package_version.name).to_pipfile(),
                'digest': None
            })

        # Removed artifact from index
        ({
            'severity': 'WARNING',
            'type': 'REMOVED-ARTIFACT',
            'justification': 'Artifact was removed from source index',
            'source': self.pipfile.meta.sources[source_name].to_dict(),
            'package_locked': package_version.to_pipfile_lock(),
            'package': self.get_package_version(package_version.name).to_pipfile(),
            'digest': None
        })

        return scan_report

    def check_provenance(self, whitelisted_sources: list = None) -> dict:
        """Check provenance/origin of packages that """
        findings, scan = self._index_scan()
        findings.extend(self._check_sources(whitelisted_sources))
        return {
            'findings': findings,
            'scan': scan
        }
