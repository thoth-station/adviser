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

"""Test removing direct dependencies based on latest version limitation."""

import pytest

from base import AdviserTestCase

from thoth.adviser.python.pipeline.sieves import LimitLatestVersionsSieve
from thoth.adviser.python.pipeline.sieve_context import SieveContext
from thoth.python import Source
from thoth.python import PackageVersion


class TestLimitLatestVersionsSieve(AdviserTestCase):
    """Test removing direct dependencies based on latest version limitation."""

    def test_remove_latest_versions_noop(self):
        """Test removing direct dependencies not hitting limit causes a noop."""
        tf_1_1_0 = PackageVersion(
            name="tensorflow",
            version="==1.1.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            develop=False,
        )
        tf_1_9_0 = PackageVersion(
            name="tensorflow",
            version="==1.9.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        tf_2_0_0 = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/jemalloc/simple/"),
            develop=False,
        )

        sieve = LimitLatestVersionsSieve(graph=None, project=None)
        sieve.update_parameters(dict([("limit_latest_versions", 3)]))

        sieve_context = SieveContext.from_package_versions([tf_1_1_0, tf_1_9_0, tf_2_0_0])

        sieve.run(sieve_context)

        assert list(sieve_context.iter_direct_dependencies()) == [tf_1_1_0, tf_1_9_0, tf_2_0_0]

    def test_remove_latest_versions(self):
        """Test removing direct dependencies based on latest version limitation."""
        tf_1_1_0 = PackageVersion(
            name="tensorflow",
            version="==1.1.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            develop=False,
        )
        tf_1_9_0 = PackageVersion(
            name="tensorflow",
            version="==1.9.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        tf_2_0_0 = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/jemalloc/simple/"),
            develop=False,
        )

        sieve = LimitLatestVersionsSieve(graph=None, project=None)
        sieve.update_parameters(dict([("limit_latest_versions", 1)]))

        sieve_context = SieveContext.from_package_versions([tf_1_1_0, tf_1_9_0, tf_2_0_0])

        sieve.run(sieve_context)

        result = list(sieve_context.iter_direct_dependencies())
        assert result == [tf_2_0_0]
