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

"""Test wrap recommending intel-tensorflow for specific CPU."""

from typing import Optional

import pytest
from flexmock import flexmock

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import IntelTensorFlowWrap

from ..base import AdviserTestCase


class TestIntelTensorflowWrap(AdviserTestCase):
    """Test recommending Intel TensorFlow build optimized for specific CPU architectures."""

    @pytest.mark.parametrize(
        "cpu_model,cpu_family,recommendation_type", [(13, 6, rt) for rt in RecommendationType],
    )
    def test_include(
        self,
        builder_context: PipelineBuilderContext,
        cpu_model: int,
        cpu_family: str,
        recommendation_type: RecommendationType,
    ) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.hardware.cpu_family = cpu_family
        builder_context.project.runtime_environment.hardware.cpu_model = cpu_model
        builder_context.project.runtime_environment.platform = "linux-x86_64"
        assert builder_context.is_adviser_pipeline()
        assert not builder_context.is_dependency_monkey_pipeline()
        assert IntelTensorFlowWrap.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "decision_type,recommendation_type,cpu_model,cpu_family,platform",
        [
            (None, RecommendationType.LATEST, 666, 6, "linux-x86_64"),  # Wrong CPU model
            (None, RecommendationType.STABLE, 13, 666, "linux-x86_64"),  # Wrong CPU family
            (None, RecommendationType.LATEST, 13, 6, "win-amd64"),  # Wrong platform
            (DecisionType.RANDOM, None, 13, 6, "linux-x86_64"),  # A dependency monkey run
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        decision_type: DecisionType,
        recommendation_type: RecommendationType,
        cpu_model: int,
        cpu_family: int,
        platform: Optional[str],
    ) -> None:
        """Test not including this pipeline unit."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.hardware.cpu_model = cpu_model
        builder_context.project.runtime_environment.hardware.cpu_family = cpu_family
        builder_context.project.runtime_environment.platform = platform

        assert builder_context.is_adviser_pipeline() or builder_context.is_dependency_monkey_pipeline()
        assert IntelTensorFlowWrap.should_include(builder_context) is None

    def test_run(self, state: State) -> None:
        """Test running this wrap."""
        state = State()
        assert not state.justification

        state.resolved_dependencies["tensorflow"] = flexmock()
        unit = IntelTensorFlowWrap()
        unit.run(state)

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message"}
        assert state.justification[0]["type"] == "INFO"
        assert (
            state.justification[0]["message"]
            == "Consider using intel-tensorflow which is optimized for CPU detected in your environment"
        )
