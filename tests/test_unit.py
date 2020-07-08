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

"""Test core utilities provided by pipeline unit base class."""

import pytest

from thoth.adviser.unit import Unit
from thoth.python import PackageVersion
from thoth.python import Source

from .base import AdviserTestCase


class TestUnit(AdviserTestCase):
    """Test unit base - core utilities provided by base class for all pipeline units.."""

    @pytest.mark.parametrize(
        "package_version, expected",
        [
            (
                PackageVersion(
                    name="tensorflow-serving-api",
                    version="1.12.3",
                    index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple"),
                    develop=False,
                ),
                True,
            ),
            (
                PackageVersion(
                    name="tensorflow",
                    version="2.0.0rc2",
                    index=Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/cuda"),
                    develop=False,
                ),
                True,
            ),
            (
                PackageVersion(
                    name="tensorflow", version="2.0.0rc2", index=Source("https://pypi.org/simple"), develop=False,
                ),
                False,
            ),
        ],
    )
    def test_is_aicoe_release(self, package_version: PackageVersion, expected: bool) -> None:
        """Test checking if the given package is an AICoE package."""
        assert Unit.is_aicoe_release(package_version) is expected

    @pytest.mark.parametrize(
        "package_version, expected",
        [
            (
                PackageVersion(
                    name="tensorflow-serving-api",
                    version="1.12.3",
                    index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple"),
                    develop=False,
                ),
                {"os_name": "fedora", "os_version": "30", "configuration": "jemalloc", "platform_tag": None,},
            ),
            (
                PackageVersion(
                    name="tensorflow",
                    version="1.12.3",
                    index=Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/cuda/simple"),
                    develop=False,
                ),
                {"os_name": None, "os_version": None, "configuration": "cuda", "platform_tag": "manylinux2010",},
            ),
            (
                PackageVersion(
                    name="tensorflow", version="1.11.0", index=Source("https://pypi.org/simple"), develop=False,
                ),
                None,
            ),
        ],
    )
    def test_get_aicoe_configuration(self, package_version, expected) -> None:
        """Check parsing of AICoE specific configuration encoded in the URL."""
        assert Unit.get_aicoe_configuration(package_version) == expected
