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

"""Test TensorFlow AVX2 step."""

from typing import Optional

import flexmock
import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.steps import TensorFlowAVX2Step
from thoth.python import PackageVersion
from thoth.python import Source

from ..base import AdviserTestCase


class TestTensorFlowAVX2Step(AdviserTestCase):
    """Test TensorFlow AVX2 step recommending AICoE TensorFlow builds."""

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.STABLE, RecommendationType.TESTING])
    def test_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        # A Haswell CPU with AVX2 support.
        builder_context.project.runtime_environment.hardware.cpu_family = 0x6
        builder_context.project.runtime_environment.hardware.cpu_model = 0xF
        assert builder_context.is_adviser_pipeline()
        assert TensorFlowAVX2Step.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,cpu_family,cpu_model",
        [
            (RecommendationType.STABLE, None, None, None),  # No CPU info.
            (RecommendationType.TESTING, None, -1, -1),  # No AVX2 support in CPU.
            (None, DecisionType.RANDOM, 0x6, 0xF),  # A Dependency Monkey run.
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
        # A Haswell CPU with AVX2 support.
        builder_context.project.runtime_environment.hardware.cpu_family = cpu_family
        builder_context.project.runtime_environment.hardware.cpu_model = cpu_model
        assert TensorFlowAVX2Step.should_include(builder_context) is None

    def test_tf_avx2(self) -> None:
        """Test recommending TensorFlow with AVX2 support."""
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.2.0",
            develop=False,
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple"),
        )

        # State and context are unused in the actual pipeline run.
        state, context = flexmock(), flexmock()
        with TensorFlowAVX2Step.assigned_context(context):
            unit = TensorFlowAVX2Step()
            assert unit.run(state, package_version) == (
                0.2,
                [
                    {
                        "message": "AICoE TensorFlow builds are optimized for AVX2 instruction "
                        "sets supported in the CPU identified",
                        "type": "INFO",
                    }
                ],
            )

    def test_no_tf_avx2(self) -> None:
        """Test not recommending TensorFlow without AVX2 support."""
        package_version = PackageVersion(
            name="tensorflow", version="==2.2.0", develop=False, index=Source("https://pypi.org/simple"),
        )

        # State and context are unused in the actual pipeline run.
        state, context = flexmock(), flexmock()
        with TensorFlowAVX2Step.assigned_context(context):
            unit = TensorFlowAVX2Step()
            assert unit.run(state, package_version) is None
