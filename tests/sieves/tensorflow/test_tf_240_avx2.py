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

"""Test a sieve that filters out TensorFlow==2.4.0 build as it requires AVX2 instruction set."""

from typing import Optional

import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import TensorFlow240AVX2IllegalInstructionSieve
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlowAVX2Step(AdviserUnitTestCase):
    """Test a sieve that filters out TensorFlow==2.4.0 build as it requires AVX2 instruction set."""

    UNIT_TESTED = TensorFlow240AVX2IllegalInstructionSieve

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        # Not None and not in AVX2 CPUs listing.
        builder_context.project.runtime_environment.hardware.cpu_family = 0x0
        builder_context.project.runtime_environment.hardware.cpu_model = 0x0
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.STABLE, RecommendationType.TESTING])
    def test_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        # Not None and not in AVX2 CPUs listing.
        builder_context.project.runtime_environment.hardware.cpu_family = 0x0
        builder_context.project.runtime_environment.hardware.cpu_model = 0x0
        assert builder_context.is_adviser_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,cpu_family,cpu_model",
        [
            (RecommendationType.STABLE, None, None, None),  # No CPU info.
            (RecommendationType.TESTING, None, 0x6, 0xF),  # AVX2 support in CPU.
            (None, DecisionType.RANDOM, 0x0, 0x0),  # A Dependency Monkey run.
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type,
        decision_type: DecisionType,
        cpu_family: Optional[int],
        cpu_model: Optional[int],
    ) -> None:
        """Test not including this pipeline unit step."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.hardware.cpu_family = cpu_family
        builder_context.project.runtime_environment.hardware.cpu_model = cpu_model
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_tf_avx2(self, context: Context) -> None:
        """Test recommending TensorFlow with AVX2 support."""
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.4.0",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        assert not context.stack_info

        with self.UNIT_TESTED.assigned_context(context):
            unit = self.UNIT_TESTED()
            result = list(unit.run((pv for pv in [package_version])))
            assert len(result) == 0

        assert len(context.stack_info) == 1

        justification = context.stack_info[0]
        assert set(justification.keys()) == {"type", "message", "link"}
        assert justification["type"] == "WARNING"
        assert justification["link"]
        assert justification["message"]

    def test_no_tf_avx2(self, context: Context) -> None:
        """Test not recommending TensorFlow without AVX2 support."""
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.4.0",
            develop=False,
            index=Source("https://thoth-station.ninja/simple"),
        )

        assert not context.stack_info

        with self.UNIT_TESTED.assigned_context(context):
            unit = self.UNIT_TESTED()
            result = list(unit.run((pv for pv in [package_version])))
            assert len(result) == 1
            assert result[0] is package_version

        assert not context.stack_info
