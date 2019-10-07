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

"""Test filtering out buildtime errors."""

import pytest

from base import AdviserTestCase

from thoth.adviser.python.pipeline.sieves import OperatingSystemSieve
from thoth.adviser.python.pipeline.exceptions import CannotRemovePackage
from thoth.adviser.python.pipeline.sieve_context import SieveContext
from thoth.python import Project
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.common import RuntimeEnvironment


class TestOperatingSystemSieve(AdviserTestCase):
    """Test sieve on operating systems which are specific to AICoE releases."""

    _PIPFILE_CONTENT_NO_AICOE = """
[[source]]
url = "https://pypi.python.org/simple"
verify_ssl = true
name = "pypi"

[packages]
thoth-python = "*"
thoth-adviser = "*"

[dev-packages]
pytest = "*"
"""

    _PIPFILE_CONTENT_AICOE = """
[[source]]
url = "https://pypi.python.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"

[dev-packages]
pytest = "*"
"""

    @staticmethod
    def _get_packages_no_aicoe():
        """Get packages which are not specific to AICoE."""
        source = Source("https://pypi.org/simple")
        return [
            PackageVersion(
                name="thoth-python",
                version="==1.0.0",
                index=source,
                develop=False,
            ),
            PackageVersion(
                name="thoth-adviser",
                version="==1.0.0",
                index=source,
                develop=False,
            ),
            PackageVersion(
                name="pytest",
                version="==3.0.0",
                index=source,
                develop=True,
            ),
        ]

    @staticmethod
    def _get_packages_aicoe():
        """Get packages which are specific to AICoE."""
        pypi_source = Source("https://pypi.org/simple")
        return [
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=pypi_source,
                develop=False,
            ),
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/jemalloc/simple/"),
                develop=False,
            ),
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
                develop=False,
            ),
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/rhel/7.6/jemalloc/simple/"),
                develop=False,
            ),
            PackageVersion(
                name="pytest",
                version="==3.0.0",
                index=pypi_source,
                develop=True,
            ),
        ]

    def test_noop_no_os(self):
        """Test no changes are made if no specific operating system is configured."""
        package_versions = self._get_packages_no_aicoe()
        sieve_context = SieveContext.from_package_versions(package_versions)

        # Do not assign runtime environment intentionally - it will default to no environment.
        project = Project.from_strings(pipfile_str=self._PIPFILE_CONTENT_NO_AICOE)
        os_sieve = OperatingSystemSieve(graph=None, project=project)
        os_sieve.run(sieve_context)

        assert {pv.to_tuple() for pv in package_versions} == set(sieve_context.iter_direct_dependencies_tuple())

    def test_noop_no_aicoe(self):
        """Test no changes are made if no AICoE releases are found."""
        package_versions = self._get_packages_no_aicoe()
        sieve_context = SieveContext.from_package_versions(package_versions)

        # Do not assign runtime environment intentionally - it will default to no environment.
        project = Project.from_strings(pipfile_str=self._PIPFILE_CONTENT_NO_AICOE)
        os_sieve = OperatingSystemSieve(graph=None, project=project)
        os_sieve.run(sieve_context)

        assert {pv.to_tuple() for pv in package_versions} == set(sieve_context.iter_direct_dependencies_tuple())

    def test_os_sieve(self):
        """Test removal of packages based on AICoE package source index configuration.

        We keep only TensorFlow release which is from PyPI and manylinux2010 build as there is no match on OS release.
        """
        package_versions = self._get_packages_aicoe()
        sieve_context = SieveContext.from_package_versions(package_versions)

        # Do not assign runtime environment intentionally - it will default to no environment.
        project = Project.from_strings(
            pipfile_str=self._PIPFILE_CONTENT_AICOE,
            runtime_environment=RuntimeEnvironment.from_dict({
                "operating_system": {
                    "name": "rhel",
                    "version": "7.5"
                }
            })
        )
        os_sieve = OperatingSystemSieve(graph=None, project=project)
        os_sieve.run(sieve_context)

        expected = {
            ("pytest", "3.0.0", "https://pypi.org/simple"),
            ("tensorflow", "1.9.0", "https://pypi.org/simple"),
            # Filtering out this entry is left on another sieve which ensures runtime environment compatibility.
            ("tensorflow", "1.9.0", "https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/jemalloc/simple/"),
            # These are filtered out:
            # ("tensorflow", "1.9.0", "https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            # ("tensorflow", "1.9.0", "https://tensorflow.pypi.thoth-station.ninja/index/os/rhel/7.6/jemalloc/simple/")
        }

        assert set(sieve_context.iter_direct_dependencies_tuple()) == expected

    def test_os_sieve_no_remove(self):
        """Test the TensorFlow package is not removed as it has no other candidate."""
        package_versions = [
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://tensorflow.pypi.thoth-station.ninja/index/fedora/30/jemalloc/simple/"),
                develop=False,
            ),
            PackageVersion(
                name="pytest",
                version="==3.0.0",
                index=Source("https://pypi.org/simple"),
                develop=True,
            ),
        ]
        sieve_context = SieveContext.from_package_versions(package_versions)

        # Do not assign runtime environment intentionally - it will default to no environment.
        project = Project.from_strings(
            pipfile_str=self._PIPFILE_CONTENT_AICOE,
            runtime_environment=RuntimeEnvironment.from_dict({
                "operating_system": {
                    "name": "rhel",
                    "version": "7.5"
                }
            })
        )
        os_sieve = OperatingSystemSieve(graph=None, project=project)
        os_sieve.run(sieve_context)

        expected = {
            ("pytest", "3.0.0", "https://pypi.org/simple"),
            ("tensorflow", "1.9.0", "https://tensorflow.pypi.thoth-station.ninja/index/fedora/30/jemalloc/simple/"),
        }

        assert set(sieve_context.iter_direct_dependencies_tuple()) == expected

    def test_os_sieve_no_error(self):
        """Test no error raised if no packages satisfy OS specific requirements."""
        package_versions = [
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://tensorflow.pypi.thoth-station.ninja/index/fedora/30/jemalloc/simple/"),
                develop=False,
            )
        ]

        sieve_context = SieveContext.from_package_versions(package_versions)
        project = Project.from_strings(
           pipfile_str=self._PIPFILE_CONTENT_AICOE,
           runtime_environment=RuntimeEnvironment.from_dict({
               "operating_system": {
                   "name": "ubi",
                   "version": "9"
               }
           })
        )
        os_sieve = OperatingSystemSieve(graph=None, project=project)
        os_sieve.run(sieve_context)

        assert set(sieve_context.iter_direct_dependencies_tuple()) == {
            ("tensorflow", "1.9.0", "https://tensorflow.pypi.thoth-station.ninja/index/fedora/30/jemalloc/simple/"),
        }
