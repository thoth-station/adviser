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
from copy import deepcopy
import tempfile

import attr
import semantic_version as semver
from thoth.common import cwd
from thoth.analyzer import run_command
from thoth.analyzer import CommandError
from thoth.storages import GraphDatabase

from .pipfile import Pipfile, PipfileLock
from .source import Source
from .package_version import PackageVersion
from .exceptions import UnableLock
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

    @classmethod
    def from_files(cls, pipfile_path: str = None, pipfile_lock_path: str = None):
        """Create project from Pipfile and Pipfile.lock files."""
        with open(pipfile_path or 'Pipfile', 'r') as pipfile_file:
            pipfile = Pipfile.from_string(pipfile_file.read())

        with open(pipfile_lock_path or 'Pipfile.lock', 'r') as pipfile_lock_file:
            pipfile_lock = PipfileLock.from_string(pipfile_lock_file.read(), pipfile)

        return cls(pipfile, pipfile_lock)

    def to_dict(self):
        """Create a dictionary representation of this project."""
        return {
            'requirements': self.pipfile.to_dict(),
            'requirements_locked': self.pipfile_lock.to_dict() if self.pipfile_lock else None
        }

    def get_outdated_package_versions(self, devel: bool = True) -> dict:
        """Get outdated packages in the lock file.

        This function will check indexes configured and look for version of
        each package. If the given package package is not latest, it will add
        it to the resulting list with the newer version identifier found on
        package index.
        """
        if not self.pipfile_lock:
            raise InternalError("Cannot check outdated packages on not-locked application stack")

        result = {}
        for package_version in self.iter_dependencies_locked(with_devel=devel):
            if package_version.index:
                latest = package_version.index.get_latest_package_version(package_version.name)
                if package_version.semantic_version != latest:
                    result[package_version.name] = (package_version, latest)
            else:
                found = False
                for index in self.pipfile_lock.meta.sources.values():
                    try:
                        latest = index.get_latest_package_version(package_version.name)
                        found = True
                    except NotFound:
                        continue

                    if package_version.semantic_version != latest:
                        result[package_version.name] = (package_version, latest)

                if not found:
                    raise NotFound(
                        f"Package {package_version!r} was not found on any package index"
                        f"configured: {self.pipfile_lock.meta.to_dict()}"
                    )

        return result

    def pipenv_lock(self):
        """Perform pipenv lock on the current state of project."""
        with cwd(self.workdir):
            self.pipfile.to_file()
            _LOGGER.debug('Running pipenv lock')

            try:
                result = run_command('pipenv lock', env={'PIPENV_IGNORE_VIRTUALENVS': '1'})
            except CommandError as exc:
                _LOGGER.exception(
                    "Unable to lock application stack (return code: %d):\n%s\n",
                    exc.return_code, exc.stdout, exc.stderr
                )
                raise UnableLock("Failed to perform lock") from exc

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

    def iter_dependencies_locked(self, with_devel: bool = True):
        """Iterate through locked dependencies of this project."""
        if not self.pipfile_lock:
            raise InternalError("Unable to chain locked dependencies - no Pipfile.lock provided")
        if with_devel:
            yield from chain(self.pipfile_lock.packages, self.pipfile_lock.dev_packages)
        else:
            yield from self.pipfile_lock.packages

    def iter_dependencies(self, with_devel: bool = True):
        """Iterate through direct dependencies of this project (not locked dependencies)."""
        if with_devel:
            yield from chain(self.pipfile.packages, self.pipfile.packages.dev_packages)
        else:
            yield from self.pipfile.packages

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
        pipfile_copy = deepcopy(self.pipfile)
        try:
            while change:
                change = False

                for package_version in chain(self.pipfile_lock.packages, self.pipfile_lock.dev_packages):
                    bad_package_report = self.is_bad_package(package_version, recommendation_type)
                    if bad_package_report:
                        self.exclude_package(package_version.duplicate())
                        report.append(bad_package_report)
                        change = True
                        break
        except UnableLock:
            report.append({
                'type': 'ERROR',
                'justification': f'Unable to create advise - not sufficient information or faulty package found for '
                                 f'recommendation type {recommendation_type.name!r} for runtime '
                                 f'environment {runtime_environment!r}'
            })
        finally:
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
                    'type': 'ERROR',
                    'id': 'SOURCE-NOT-WHITELISTED',
                    'justification': f'Provided index {source.name!r} is not stated in the '
                                     f'whitelisted package sources listing',
                    'source': source.to_dict(),
                })
            elif not source.verify_ssl:
                report.append({
                    'type': 'WARNING',
                    'id': 'INSECURE-SOURCE',
                    'justification': f'Source {source.name!r} does not use SSL/TLS verification',
                    'source': source.to_dict(),
                })

        return report

    def _index_scan(self) -> typing.Tuple[list, dict]:
        """Generate full report for packages given the sources configured."""
        report = {}
        findings = []
        for package_version in chain(self.pipfile_lock.packages, self.pipfile_lock.dev_packages):
            if package_version.name in report:
                # TODO: can we have the same package in dev packages and packages?
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
        scan_report = []

        # Prepare hashes for inspection.
        hashes = []
        pipenv_style_hashes = []
        for entry in index_report.values():
            hashes.append([item['sha256'] for item in entry])
            pipenv_style_hashes.append([f"sha256:{item['sha256']}" for item in entry])

        if not package_version.index and len(index_report.keys()) > 1:
            # Are there indexes with different artifacts present? - suggest to specify index explicitly.
            if set(chain(*hashes)) != set(hashes[0]):
                sources_reported = ", ".join(index_report.keys())
                scan_report.append({
                    'type': 'WARNING',
                    'id': 'DIFFERENT-ARTIFACTS-ON-SOURCES',
                    'justification': f'Configured sources ({sources_reported}) have different artifacts '
                                     f'available, specify explicitly source to be used',
                    'indexes': list(index_report.keys()),
                    'package_locked': package_version.to_pipfile_lock(),
                    'package_name': package_version.name,
                    'package_version': package_version.version,
                    'sources': index_report
                })

        # Source for reports.
        source = None
        if package_version.index:
            source = package_version.index.to_dict()

        if package_version.index and index_report.get(package_version.index.name) and len(hashes) > 1:
            # Is installed from different source - which one?
            used_package_version_hashes = set(h[len('sha256:'):] for h in package_version.hashes)
            configured_index_hashes = set(h['sha256'] for h in index_report[package_version.index.name])

            # Find other sources from which artifacts can be installed.
            other_sources = {}
            for artifact_hash in package_version.hashes:
                artifact_hash = artifact_hash[len('sha256:'):]  # Remove pipenv-specific hash formatting.

                for index_name, index_info in index_report.items():
                    if index_name == package_version.index.name:
                        # Skip index that is assigned to the package, we are inspecting from the other sources.
                        continue

                    artifact_entry = [
                        (i['name'], i['sha256']) for i in index_info
                        if i['sha256'] == artifact_hash
                    ]

                    if not artifact_entry:
                        continue

                    if index_name not in other_sources:
                        other_sources[index_name] = []

                    other_sources[index_name].extend(artifact_entry)

            if not set(used_package_version_hashes).issubset(set(configured_index_hashes)):
                # Source is different from the configured one.
                scan_report.append({
                    'type': 'ERROR',
                    'id': 'ARTIFACT-DIFFERENT-SOURCE',
                    'justification': f'Artifacts are installed from different '
                                     f'sources ({",".join(other_sources.keys())}) not respecting configuration',
                    'source': source,
                    'package_locked': package_version.to_pipfile_lock(),
                    'package_name': package_version.name,
                    'package_version': package_version.version,
                    'indexes': list(other_sources.keys()),
                    'sources': other_sources
                })
            elif other_sources:
                # Warn about possible installation from another source.
                scan_report.append({
                    'type': 'INFO',
                    'id': 'ARTIFACT-POSSIBLE-DIFFERENT-SOURCE',
                    'justification': f'Artifacts can be installed from different sources '
                                     f'({",".join(other_sources.keys())}) not respecting configuration '
                                     f'that expects {package_version.index.name!r}',
                    'source': source,
                    'package_locked': package_version.to_pipfile_lock(),
                    'package_name': package_version.name,
                    'package_version': package_version.version,
                    'indexes': list(other_sources.keys()),
                    'sources': other_sources
                })

        if package_version.index and not index_report.get(package_version.index.name):
            # Configured index does not provide the given package.
            scan_report.append({
                'type': 'ERROR',
                'id': 'MISSING-PACKAGE',
                'justification': f'Source index {package_version.index.name!r} explicitly '
                                 f'assigned to package {package_version.name!r} but package '
                                 f'was not found on the given index - was it removed?',
                'source': source,
                'package_locked': package_version.to_pipfile_lock(),
                'package_name': package_version.name,
                'package_version': package_version.version,
                'sources': index_report
            })

        # Changed hashes?
        for digest in package_version.hashes:
            digest = digest[len('sha256:'):]
            for index_name, index_info in index_report.items():
                if any(item['sha256'] == digest for item in index_info):
                    break
            else:
                scan_report.append({
                    'type': 'ERROR',
                    'id': 'INVALID-ARTIFACT-HASH',
                    'justification': 'Artifact stated in lock was not found on index - was it removed?',
                    'source': source,
                    'package_locked': package_version.to_pipfile_lock(),
                    'package_name': package_version.name,
                    'package_version': package_version.version,
                    'digest': digest
                })

        return scan_report

    def check_provenance(self, whitelisted_sources: list = None) -> dict:
        """Check provenance/origin of packages that are stated in the project."""
        findings, _ = self._index_scan()
        findings.extend(self._check_sources(whitelisted_sources))
        return findings

    def add_source(self, url: str, verify_ssl: bool = True, name: str = None,
                   warehouse: bool = False, warehouse_api_url: str = None) -> Source:
        """Add a package source (index) to the project."""
        if name:
            source = Source(name=name, url=url, verify_ssl=verify_ssl,
                            warehouse=warehouse, warehouse_api_url=warehouse_api_url)
        else:
            # Do not provide source index name so that attrs correctly compute default based on URL.
            source = Source(url=url, verify_ssl=verify_ssl,
                            warehouse=warehouse, warehouse_api_url=warehouse_api_url)

        self.pipfile.meta.add_source(source)
        if self.pipfile_lock:
            self.pipfile_lock.meta.add_source(source)

        return source

    def add_package(self, package_name: str, package_version: str = None, *,
                    source: Source = None, develop: bool = False):
        """Add the given package to project.

        This method will add packages only to Pipfile, locking has to be explicitly done once package is added.
        """
        if source and source.name not in self.pipfile.meta.sources:
            raise InternalError(
                f"Adding package {package_name} to project without having source index "
                f"{source.name} registered in the project"
            )

        package_version = PackageVersion(
            name=package_name, version=package_version, develop=develop, index=source.name if source else None
        )
        self.pipfile.add_package_version(package_version)
