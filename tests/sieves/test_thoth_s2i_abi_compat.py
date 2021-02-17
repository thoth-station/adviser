#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020-2021 Kevin Postlethwait
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

"""Test filtering out Python Packages based on required and available ABI symbols."""

from typing import Optional

import flexmock
import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import ThothS2IAbiCompatibilitySieve
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages import GraphDatabase

from ..base import AdviserUnitTestCase

_SYSTEM_SYMBOLS = ["GLIBC_2.0", "GLIBC_2.1", "GLIBC_2.2", "GLIBC_2.3", "GLIBC_2.4", "GLIBC_2.5", "GCC_3.4", "X_2.21"]
_REQUIRED_SYMBOLS_A = ["GLIBC_2.9"]
_REQUIRED_SYMBOLS_B = ["GLIBC_2.4"]


class TestThothS2IAbiCompatibilitySieve(AdviserUnitTestCase):
    """Test filtering out packages based on symbols required."""

    UNIT_TESTED = ThothS2IAbiCompatibilitySieve

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38:v0.23.0"
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize(
        "base_image",
        [
            None,
            "fedora:32",
        ],
    )
    def test_no_should_include(self, base_image: Optional[str], builder_context: PipelineBuilderContext) -> None:
        """Test not including this pipeline unit."""
        builder_context.project.runtime_environment.base_image = base_image
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test including this pipeline unit."""
        builder_context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38:v0.23.0"
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

    def test_no_thoth_s2i_version(self, context: Context) -> None:
        """Test no Thoth S2I version present."""
        context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38"  # No version.

        GraphDatabase.should_receive("get_thoth_s2i_analyzed_image_symbols_all").times(0)

        unit = self.UNIT_TESTED()
        with self.UNIT_TESTED.assigned_context(context):
            unit.pre_run()

        assert not unit.image_symbols

    def test_abi_compat_symbols_present(self, context: Context) -> None:
        """Test if required symbols are correctly identified."""
        source = Source("https://pypi.org/simple")
        package_version = PackageVersion(name="tensorflow", version="==1.9.0", index=source, develop=False)
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_thoth_s2i_analyzed_image_symbols_all").and_return(_SYSTEM_SYMBOLS).once()
        GraphDatabase.should_receive("get_python_package_required_symbols").and_return(_REQUIRED_SYMBOLS_B).once()

        context.project.runtime_environment.operating_system.name = "rhel"
        context.project.runtime_environment.operating_system.version = "8.0"
        context.project.runtime_environment.cuda_version = "4.6"
        context.project.runtime_environment.python_version = "3.6"
        context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38:v0.23.0"

        with self.UNIT_TESTED.assigned_context(context):
            sieve = self.UNIT_TESTED()
            sieve.pre_run()
            assert list(sieve.run((p for p in [package_version]))) == [package_version]

    def test_abi_compat_symbols_not_present(self, context: Context) -> None:
        """Test if required symbols being missing is correctly identified."""
        source = Source("https://pypi.org/simple")
        package_version = PackageVersion(name="tensorflow", version="==1.9.0", index=source, develop=False)
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_thoth_s2i_analyzed_image_symbols_all").and_return(_SYSTEM_SYMBOLS).once()
        GraphDatabase.should_receive("get_python_package_required_symbols").and_return(_REQUIRED_SYMBOLS_A).once()

        context.project.runtime_environment.operating_system.name = "rhel"
        context.project.runtime_environment.operating_system.version = "8.0"
        context.project.runtime_environment.cuda_version = "4.6"
        context.project.runtime_environment.python_version = "3.6"
        context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38:v0.23.0"

        with self.UNIT_TESTED.assigned_context(context):
            sieve = self.UNIT_TESTED()
            sieve.pre_run()
            assert list(sieve.run((p for p in [package_version]))) == []

    def test_super_pre_run(self, context: Context) -> None:
        """Make sure the pre-run method of the base is called."""
        context.graph.should_receive("get_thoth_s2i_analyzed_image_symbols_all").with_args(
            thoth_s2i_image_name="quay.io/thoth-station/s2i-thoth-ubi8-py38",
            thoth_s2i_image_version="0.23.0",
            is_external=False,
        ).and_return(set()).once()

        context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38:v0.23.0"

        unit = self.UNIT_TESTED()
        assert unit.unit_run is False

        with unit.assigned_context(context):
            unit.pre_run()

        assert unit.unit_run is False
