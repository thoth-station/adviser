#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""Test sieve for filtering packages coming from a specific index."""


from thoth.adviser.sieves import FilterIndexSieve
from thoth.python import Source
from thoth.python import PackageVersion

from ..base import AdviserTestCase


class TestFilterIndexSieve(AdviserTestCase):
    """Test package index sieve."""

    def test_default_configuration(self) -> None:
        """Test obtaining default configuration."""
        unit = FilterIndexSieve()
        assert unit.configuration == {"package_name": None, "index_url": None}

    def test_run_filter(self) -> None:
        """Test filtering a package based on source index used."""
        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://pypi.org/simple"), develop=False,
        )
        unit = FilterIndexSieve()
        unit.update_configuration(
            {
                "package_name": "tensorflow",
                "index_url": ["https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple/"],
            }
        )
        unit.pre_run()
        assert list(unit.run([package_version])) == []

    def test_run_no_filter(self) -> None:
        """Test not filtering a package based on source index used."""
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.1.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple/"),
            develop=False,
        )
        unit = FilterIndexSieve()
        unit.update_configuration(
            {
                "package_name": "tensorflow",
                "index_url": ["https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple/"],
            }
        )
        unit.pre_run()
        assert list(unit.run([package_version])) == [package_version]

    def test_run_no_filter_multiple(self) -> None:
        """Test not filtering a package based on source index used."""
        package_version = PackageVersion(
            name="tensorboard", version="==2.1.0", index=Source("https://pypi.org/simple"), develop=False,
        )
        unit = FilterIndexSieve()
        unit.update_configuration(
            {
                "package_name": "tensorboard",
                "index_url": [
                    "https://pypi.org/simple",
                    "https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple/",
                ],
            }
        )
        unit.pre_run()
        assert list(unit.run([package_version])) == [package_version]
