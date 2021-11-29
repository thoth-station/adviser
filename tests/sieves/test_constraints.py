#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""Test removing packages based on constraints supplied."""

import pytest

from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import ConstraintsSieve
from thoth.python import Constraints
from thoth.python import PackageVersion
from thoth.python import Source

from ..base import AdviserUnitTestCase


class TestConstraintsSieve(AdviserUnitTestCase):
    """Test removing packages not coming from a specific Python package index.."""

    UNIT_TESTED = ConstraintsSieve

    @pytest.mark.skip(reason="The pipeline unit configuration is specific to constraint configuration supplied")
    def test_default_configuration(self, builder_context: PipelineBuilderContext) -> None:
        """Test the default configuration of unit tested."""

    def test_default_environment_marker(self, builder_context: "PipelineBuilderContext") -> None:
        """Test checking the default environment marker configuration."""
        builder_context.project.runtime_environment.python_version = "3.9"
        assert self.UNIT_TESTED.default_environment(builder_context) == {
            "implementation_name": "cpython",
            "implementation_version": "3.9.0",
            "os_name": "posix",
            "platform_machine": "x86_64",
            "platform_python_implementation": "CPython",
            "platform_system": "Linux",
            "python_version": builder_context.project.runtime_environment.python_version,
            "sys_platform": "linux",
            "python_full_version": "3.9.0",
            "platform_version": "",
            "platform_release": "",
        }

    def test_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test including this pipeline unit."""
        builder_context.project.runtime_environment.python_version = "3.9"
        builder_context.project.constraints = Constraints.from_file(
            str(self.data_dir / "constraints" / "constraints_0.txt")
        )
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [
            {"package_name": "numpy", "specifier": "~=2.0"}
        ]

    def test_not_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including this pipeline unit."""
        builder_context.project.runtime_environment.python_version = "1.9"
        builder_context.project.constraints = Constraints.from_file(
            str(self.data_dir / "constraints" / "constraints_0.txt")
        )
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_include_version(self, builder_context: PipelineBuilderContext, context: "Context") -> None:
        """Test not including and running this pipeline unit if version is not provided in constraints."""
        builder_context.project.runtime_environment.python_version = "3.9"
        builder_context.project.constraints = Constraints.from_file(
            str(self.data_dir / "constraints" / "constraints_1.txt")
        )
        config = list(self.UNIT_TESTED.should_include(builder_context))

        assert len(config) == 1
        assert config == [{"package_name": "numpy", "specifier": "*"}]

        unit = self.UNIT_TESTED()
        unit.update_configuration(config[0])

        package_version_1 = PackageVersion(
            name="numpy", version="==0.0.1", index=Source("https://pypi.org/simple"), develop=True
        )

        with unit.assigned_context(context):
            unit.pre_run()
            assert list(unit.run((pv for pv in (package_version_1,)))) == [package_version_1]

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.project.constraints = Constraints.from_file(
            str(self.data_dir / "constraints" / "constraints_0.txt")
        )
        builder_context.project.runtime_environment.python_version = "3.9"
        self.verify_multiple_should_include(builder_context)

    def test_sieve(self, context: "Context") -> None:
        """Test filtering out packages based on constraints configured."""
        package_version_1 = PackageVersion(
            name="pandas", version="==0.0.1", index=Source("https://pypi.org/simple"), develop=True
        )
        package_version_2 = PackageVersion(
            name="pandas", version="==0.0.2", index=Source("https://pypi.org/simple"), develop=True
        )

        unit = self.UNIT_TESTED()
        unit.update_configuration({"package_name": "pandas", "specifier": ">=1.0"})

        with unit.assigned_context(context):
            unit.pre_run()
            assert list(unit.run((pv for pv in (package_version_1, package_version_2)))) == []

    def test_no_sieve(self, context: "Context") -> None:
        """Test not filtering out packages based on constraints configured."""
        package_version = PackageVersion(
            name="pandas", version="==2.0.0", index=Source("https://pypi.org/simple"), develop=True
        )

        unit = self.UNIT_TESTED()
        unit.update_configuration({"package_name": "pandas", "specifier": ">=1.0,<=2.0"})

        with unit.assigned_context(context):
            unit.pre_run()
            assert list(unit.run((pv for pv in (package_version,)))) == [package_version]

    def test_no_sieve_prereleases(self, context: "Context") -> None:
        """Test not filtering pre-releases.

        As Python's packaging handles pre-releases separately, let's check correct handling.
        """
        package_version = PackageVersion(
            name="pandas", version="==2.0.0rc0", index=Source("https://pypi.org/simple"), develop=True
        )

        unit = self.UNIT_TESTED()
        unit.update_configuration({"package_name": "pandas", "specifier": "<=2.0"})

        with unit.assigned_context(context):
            unit.pre_run()
            assert list(unit.run((pv for pv in (package_version,)))) == [package_version]
