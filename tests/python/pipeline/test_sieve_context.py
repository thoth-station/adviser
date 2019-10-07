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

import pytest

from base import AdviserTestCase

from thoth.python import PackageVersion
from thoth.python import Source

from thoth.adviser.python.pipeline.sieve_context import SieveContext
from thoth.adviser.python.pipeline.exceptions import CannotRemovePackage
from thoth.adviser.python.pipeline.exceptions import PackageNotFound


class TestSieveContext(AdviserTestCase):
    """Test handling of sieve context."""

    @staticmethod
    def _get_package_versions():
        """Get a list of package versions for the test case."""
        source = Source("https://pypi.org/simple")
        return [
            PackageVersion(
                name="a",
                version="==1.0.0",
                index=source,
                develop=False,
            ),
            PackageVersion(
                name="b",
                version="==1.0.0",
                index=source,
                develop=False,
            ),
            PackageVersion(
                name="b",
                version="==2.0.0",
                index=source,
                develop=False,
            ),
            PackageVersion(
                name="c",
                version="==1.0.0",
                index=source,
                develop=False,
            ),
            PackageVersion(
                name="c",
                version="==2.0.0",
                index=source,
                develop=False,
            )
        ]

    def test_noop(self):
        """Test no operation performed on top of sieve context."""
        package_versions = self._get_package_versions()
        sieve_context = SieveContext.from_package_versions(package_versions)
        assert set(dep.to_tuple() for dep in package_versions) == set(dep.to_tuple() for dep in sieve_context.iter_direct_dependencies())
        assert set(dep.to_tuple() for dep in package_versions) == set(sieve_context.iter_direct_dependencies_tuple())

    def test_remove_single(self):
        """Test removal of a single dependency."""
        package_versions = self._get_package_versions()

        sieve_context = SieveContext.from_package_versions(package_versions)

        to_remove = package_versions.pop(-1)
        sieve_context.remove_package(to_remove)
        assert set(dep.to_tuple() for dep in package_versions) == set(sieve_context.iter_direct_dependencies_tuple())

    def test_remove_error(self):
        """Test removal of a package which has no other candidate - an exception should be raised."""
        package_versions = self._get_package_versions()

        sieve_context = SieveContext.from_package_versions(package_versions)

        to_remove = package_versions.pop(0)
        with pytest.raises(CannotRemovePackage):
            sieve_context.remove_package(to_remove)

    def test_remove_multiple(self):
        """Test removal of multiple packages."""
        package_versions = self._get_package_versions()

        sieve_context = SieveContext.from_package_versions(package_versions)

        # Remove b==1.0.0 and c==2.0.0 which have alternatives.
        to_remove = package_versions.pop(1)
        sieve_context.remove_package(to_remove)
        to_remove = package_versions.pop(-1)
        sieve_context.remove_package(to_remove)

        assert set(dep.to_tuple() for dep in package_versions) == set(sieve_context.iter_direct_dependencies_tuple())

    def test_remove_multiple_error(self):
        """Test removal of multiple packages which causes error."""
        package_versions = self._get_package_versions()

        sieve_context = SieveContext.from_package_versions(package_versions)

        to_remove = package_versions.pop(-1)
        sieve_context.remove_package(to_remove)
        to_remove = package_versions.pop(-1)
        with pytest.raises(CannotRemovePackage):
            sieve_context.remove_package(to_remove)

    def test_remove_not_listed(self):
        """Test removal of a not listed package."""
        package_versions = self._get_package_versions()

        sieve_context = SieveContext.from_package_versions(package_versions)

        to_remove = PackageVersion(
            name="thispackageisnotlistedinthepackageversionslisting",
            version="==2.0.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        with pytest.raises(PackageNotFound):
            sieve_context.remove_package(to_remove)

    def test_sort_packages(self):
        a_pkg = PackageVersion(
            name="a",
            version="==1.0.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        b_pkg = PackageVersion(
            name="b",
            version="==2.0.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/simple"),
            develop=False,
        )
        c_pkg = PackageVersion(
            name="c",
            version="==1.0.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        packages = [a_pkg, c_pkg, b_pkg]

        sieve_context = SieveContext.from_package_versions(packages)
        # (a.name > b.name) - (a.name < b.name) is idiom for C-style like strcmp()
        sieve_context.sort_packages(lambda a, b: (a.name > b.name) - (a.name < b.name), reverse=True)
        assert list(sieve_context.iter_direct_dependencies()) == [c_pkg, b_pkg, a_pkg]

        sieve_context.sort_packages(lambda a, b: (a.name > b.name) - (a.name < b.name), reverse=False)
        result = list(sieve_context.iter_direct_dependencies())
        assert result == [a_pkg, b_pkg, c_pkg]

        # Now we sort based on version - as sorting is stable, we should preserve relative order of a and c.
        sieve_context.sort_packages(
            lambda a, b: (a.semantic_version > b.semantic_version) - (a.semantic_version < b.semantic_version),
            reverse=False,
        )
        result = list(sieve_context.iter_direct_dependencies())
        assert result == [a_pkg, c_pkg, b_pkg], "Sorting of packages is not stable"

        sieve_context.sort_packages(
            lambda a, b: (a.semantic_version > b.semantic_version) - (a.semantic_version < b.semantic_version),
            reverse=True,
        )
        result = list(sieve_context.iter_direct_dependencies())
        assert result == [b_pkg, a_pkg, c_pkg], "Sorting of packages is not stable"

