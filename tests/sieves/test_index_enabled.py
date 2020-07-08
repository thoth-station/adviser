#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Test filtering out packages based on enabled or disabled Python package index."""

import flexmock

from thoth.adviser.sieves import PackageIndexSieve
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages import GraphDatabase
from thoth.storages.exceptions import NotFoundError

from ..base import AdviserTestCase


class TestPackageIndexSieve(AdviserTestCase):
    """Test filtering out packages based on enabled or disabled Python package index."""

    def test_sieve_index_enabled(self) -> None:
        """Test no-op when the given Python package index used to obtain package is enabled."""
        source = Source("https://pypi.org/simple")
        package_version = PackageVersion(name="tensorflow", version="==1.9.0", index=source, develop=False)
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("is_python_package_index_enabled").with_args(source.url).and_return(True).once()

        context = flexmock(graph=GraphDatabase())
        with PackageIndexSieve.assigned_context(context):
            sieve = PackageIndexSieve()
            assert list(sieve.run((p for p in [package_version]))) == [package_version]

    def test_sieve_index_disabled(self) -> None:
        """Test removals of Python package if Python package index used is disabled."""
        source = Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/jemalloc/simple/")
        package_version = PackageVersion(name="tensorflow", version="==1.9.0", index=source, develop=False)
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("is_python_package_index_enabled").with_args(source.url).and_return(False).once()

        context = flexmock(graph=GraphDatabase())
        with PackageIndexSieve.assigned_context(context):
            sieve = PackageIndexSieve()
            assert list(sieve.run(p for p in [package_version])) == []

    def test_sieve_index_not_found(self) -> None:
        """Test removals of Python package if Python package index used is unknown."""
        source = Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/jemalloc/simple/")
        package_version = PackageVersion(name="tensorflow", version="==1.9.0", index=source, develop=False)
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("is_python_package_index_enabled").with_args(source.url).and_raise(
            NotFoundError
        ).once()

        context = flexmock(graph=GraphDatabase())
        with PackageIndexSieve.assigned_context(context):
            sieve = PackageIndexSieve()
            assert list(sieve.run((p for p in [package_version]))) == []
