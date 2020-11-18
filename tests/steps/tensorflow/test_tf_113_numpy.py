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

"""Test a step for TensorFlow 1.13.1 and its compatibility with NumPy>=1.16.0."""

from itertools import product

import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.steps import TensorFlow113NumPyStep
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlow113NumPyStep(AdviserUnitTestCase):
    """TensorFlow 1.13.1 is compatible with NumPy>=1.16.0, not with >=1.13.3 as stated in setup.py."""

    UNIT_TESTED = TensorFlow113NumPyStep

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize(
        "recommendation_type",
        [
            RecommendationType.STABLE,
            RecommendationType.TESTING,
            RecommendationType.PERFORMANCE,
            RecommendationType.STABLE,
        ],
    )
    def test_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        assert builder_context.is_adviser_pipeline()
        assert TensorFlow113NumPyStep.should_include(builder_context) == {}

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
        assert TensorFlow113NumPyStep.should_include(builder_context) is None

    @pytest.mark.parametrize(
        "tf_name,np_version",
        list(product(["tensorflow", "tensorflow-cpu", "tensorflow-gpu"], ["1.13.3", "1.14.0", "1.15.0", "1.15.5"])),
    )
    def test_run_not_acceptable(self, context: Context, tf_name: str, np_version: str) -> None:
        """Test wrong resolutions are not acceptable."""
        package_version = PackageVersion(
            name="numpy",
            version=f"=={np_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        state.add_resolved_dependency((tf_name, "1.13.1", "https://pypi.org/simple"))

        unit = TensorFlow113NumPyStep()
        unit.pre_run()

        assert not context.stack_info

        with unit.assigned_context(context):
            with pytest.raises(NotAcceptable):
                assert unit._message_logged is False
                unit.run(state, package_version)

        assert unit._message_logged is True
        assert context.stack_info
        assert self.verify_justification_schema(context.stack_info) is True

    @pytest.mark.parametrize(
        "tf_name,np_version",
        list(product(["tensorflow", "tensorflow-cpu", "tensorflow-gpu"], ["1.16.0", "1.17.0", "1.19.0"])),
    )
    def test_run_noop(self, tf_name: str, np_version: str) -> None:
        """Test wrong resolutions are not acceptable."""
        package_version = PackageVersion(
            name="numpy",
            version=f"=={np_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        state.add_resolved_dependency((tf_name, "1.13.1", "https://pypi.org/simple"))

        unit = TensorFlow113NumPyStep()

        assert unit._message_logged is False
        assert unit.run(state, package_version) is None
        assert unit._message_logged is False
