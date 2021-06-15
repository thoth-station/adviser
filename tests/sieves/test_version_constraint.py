#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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

from thoth.adviser.context import Context
from thoth.adviser.sieves import VersionConstraintSieve
from thoth.adviser.exceptions import PipelineUnitConfigurationSchemaError
from thoth.python import Source
from thoth.python import PackageVersion

from ..base import AdviserUnitTestCase


class TestVersionConstrainSieve(AdviserUnitTestCase):
    """Test version constraint sieve."""

    UNIT_TESTED = VersionConstraintSieve

    @pytest.mark.skip(reason="Version constrain sieve is never registered.")
    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""

    def test_configuration_error(self) -> None:
        """Test removing a locked package based on direct dependencies."""
        # Default values should error, no adjustment to values.
        unit = VersionConstraintSieve()
        with pytest.raises(PipelineUnitConfigurationSchemaError):
            unit.update_configuration({})

        unit = VersionConstraintSieve()
        with pytest.raises(PipelineUnitConfigurationSchemaError):
            unit.update_configuration({"package_name": None, "version_specifier": None})

        unit = VersionConstraintSieve()
        with pytest.raises(PipelineUnitConfigurationSchemaError):
            unit.update_configuration(
                {
                    "package_name": "tensorflow",
                    "version_specifier": None,
                }
            )

        unit = VersionConstraintSieve()
        with pytest.raises(PipelineUnitConfigurationSchemaError):
            unit.update_configuration(
                {
                    "package_name": None,
                    "version_specifier": ">2.0",
                }
            )

    def test_default_configuration(self) -> None:
        """Test obtaining default configuration."""
        unit = VersionConstraintSieve()
        assert unit.configuration == {"package_name": None, "version_specifier": None}

    def test_run_filter(self) -> None:
        """Test filtering a package based on version specifier."""
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        unit = VersionConstraintSieve()
        unit.update_configuration(
            {
                "package_name": "tensorflow",
                "version_specifier": "<2.0",
            }
        )
        unit.pre_run()
        assert list(unit.run([package_version])) == []

    def test_run_no_filter(self) -> None:
        """Test not filtering a package based on version specifier."""
        package_version = PackageVersion(
            name="tensorboard",
            version="==2.1.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        unit = VersionConstraintSieve()
        unit.update_configuration(
            {
                "package_name": "tensorboard",
                "version_specifier": ">2.0",
            }
        )
        unit.pre_run()
        assert list(unit.run([package_version])) == [package_version]

    def test_super_pre_run(self, context: Context) -> None:
        """Make sure the pre-run method of the base is called."""
        unit = VersionConstraintSieve()
        unit.update_configuration(
            {
                "package_name": "tensorflow",
                "version_specifier": "==2.3",
            }
        )

        assert unit.unit_run is False
        unit.unit_run = True

        with unit.assigned_context(context):
            unit.pre_run()

        assert (
            unit.unit_run is False
        ), "Unit flag unit_run not reset, is super().pre_run() called in sources when providing pre_run method!?"
