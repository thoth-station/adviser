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

"""Test version constraint sieve."""

import pytest

from thoth.adviser.sieves import VersionConstraintSieve
from thoth.adviser.exceptions import SieveError
from thoth.python import Source
from thoth.python import PackageVersion

from ..base import AdviserTestCase


class TestVersionConstrainSieve(AdviserTestCase):
    """Test version constraint sieve."""

    def test_configuration_error(self) -> None:
        """Test removing a locked package based on direct dependencies."""
        # Default values should error, no adjustment to values.
        with pytest.raises(SieveError):
            VersionConstraintSieve().pre_run()

        unit = VersionConstraintSieve()
        unit.update_configuration({"package_name": None, "version_specifier": None})
        with pytest.raises(SieveError):
            unit.pre_run()

        unit = VersionConstraintSieve()
        unit.update_configuration(
            {"package_name": "tensorflow", "version_specifier": None,}
        )
        with pytest.raises(SieveError):
            unit.pre_run()

        unit = VersionConstraintSieve()
        unit.update_configuration(
            {"package_name": None, "version_specifier": ">2.0",}
        )
        with pytest.raises(SieveError):
            unit.pre_run()

    def test_default_configuration(self) -> None:
        """Test obtaining default configuration."""
        unit = VersionConstraintSieve()
        assert unit.configuration == {"package_name": None, "version_specifier": None}

    def test_run_filter(self) -> None:
        """Test filtering a package based on version specifier."""
        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://pypi.org/simple"), develop=False,
        )
        unit = VersionConstraintSieve()
        unit.update_configuration(
            {"package_name": "tensorflow", "version_specifier": "<2.0",}
        )
        unit.pre_run()
        assert list(unit.run([package_version])) == []

    def test_run_no_filter(self) -> None:
        """Test not filtering a package based on version specifier."""
        package_version = PackageVersion(
            name="tensorboard", version="==2.1.0", index=Source("https://pypi.org/simple"), develop=False,
        )
        unit = VersionConstraintSieve()
        unit.update_configuration(
            {"package_name": "tensorboard", "version_specifier": ">2.0",}
        )
        unit.pre_run()
        assert list(unit.run([package_version])) == [package_version]
