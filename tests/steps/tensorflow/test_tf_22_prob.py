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

"""Test suggesting not to use TensorFlow 2.2 with tensorflow-probability."""

import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.steps import TensorFlow22ProbabilityStep
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlow22ProbabilityStep(AdviserUnitTestCase):
    """Test suggesting not to use TensorFlow 2.2 with tensorflow-probability."""

    UNIT_TESTED = TensorFlow22ProbabilityStep

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.STABLE, RecommendationType.TESTING])
    def test_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        assert builder_context.is_adviser_pipeline()
        assert TensorFlow22ProbabilityStep.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "recommendation_type,decision_type",
        [
            (RecommendationType.LATEST, None),
            (None, DecisionType.RANDOM),
        ],  # A Dependency Monkey run.
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type,
        decision_type: DecisionType,
    ) -> None:
        """Test not including this pipeline unit step."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        assert TensorFlow22ProbabilityStep.should_include(builder_context) is None

    @pytest.mark.parametrize("package_name", ["tensorflow", "tensorflow-cpu", "tensorflow-gpu"])
    def test_run(self, context: Context, package_name: str) -> None:
        """Test recommending not to use TensorFlow 2.2 with tensorflow-probability."""
        package_version = PackageVersion(
            name="tensorflow-probability",
            version="==0.11.0",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        state.add_resolved_dependency((package_name, "2.2.0", "https://pypi.org/simple"))

        unit = TensorFlow22ProbabilityStep()
        unit.pre_run()

        assert not context.stack_info

        with unit.assigned_context(context):
            with pytest.raises(NotAcceptable):
                assert unit._message_logged is False
                unit.run(state, package_version)
                assert unit._message_logged is True

        assert context.stack_info
        assert self.verify_justification_schema(context.stack_info) is True

    def test_run_acceptable_tf(self) -> None:
        """Test noop for this pipeline unit."""
        package_version_1 = PackageVersion(
            name="tensorflow-probability",
            version="==0.11.0",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        package_version_2 = PackageVersion(
            name="flask",
            version="==0.12",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        unit = TensorFlow22ProbabilityStep()

        assert unit.run(state, package_version_1) is None
        assert unit.run(state, package_version_2) is None

        state.add_resolved_dependency(("tensorflow", "2.3.0", "https://pypi.org/simple"))
        assert unit.run(state, package_version_1) is None
        assert unit.run(state, package_version_2) is None
