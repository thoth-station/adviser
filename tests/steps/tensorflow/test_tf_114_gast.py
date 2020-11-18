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

"""Test a step suggesting not to use gast>0.2.2 with TensorFlow<=1.14."""

from itertools import product

import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.context import Context
from thoth.adviser.steps import TensorFlow114GastStep
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlow114GastStep(AdviserUnitTestCase):
    """Test a step suggesting not to use gast>0.2.2 with TensorFlow<=1.14."""

    UNIT_TESTED = TensorFlow114GastStep

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
        assert TensorFlow114GastStep.should_include(builder_context) == {}

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
        assert TensorFlow114GastStep.should_include(builder_context) is None

    @pytest.mark.parametrize(
        "tf_name,tf_version,gast_version",
        list(
            product(
                ["tensorflow", "tensorflow-cpu", "tensorflow-gpu"],
                ["1.13.3", "1.14.0", "1.14.1", "1.5.1"],
                ["0.3.0", "0.3.1", "0.2.3"],
            )
        ),
    )
    def test_run_not_acceptable(self, context: Context, tf_name: str, tf_version: str, gast_version: str) -> None:
        """Test not acceptable TensorFlow<=1.14 with gast>0.2.2."""
        gast_package_version = PackageVersion(
            name="gast",
            version=f"=={gast_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )
        tf_package_version = PackageVersion(
            name=tf_name,
            version=f"=={tf_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        state.add_resolved_dependency(tf_package_version.to_tuple())
        context.register_package_version(tf_package_version)

        unit = TensorFlow114GastStep()

        with unit.assigned_context(context):
            assert unit._message_logged is False
            with pytest.raises(NotAcceptable):
                unit.run(state, gast_package_version)

        assert unit._message_logged is True

    @pytest.mark.parametrize(
        "tf_name,tf_version,gast_version",
        [
            ("tensorflow", "1.13.0", "0.2.2"),
            ("tensorflow-cpu", "2.0.0", "0.3.0"),
            ("tensorflow-gpu", "1.14.0", "0.2.0"),
        ],
    )
    def test_run_noop(self, context: Context, tf_name: str, tf_version: str, gast_version: str) -> None:
        """Test no operation performed when not invalid combination is seen."""
        gast_package_version = PackageVersion(
            name="gast",
            version=f"=={gast_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )
        tf_package_version = PackageVersion(
            name=tf_name,
            version=f"=={tf_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        state.add_resolved_dependency(tf_package_version.to_tuple())
        context.register_package_version(tf_package_version)

        unit = TensorFlow114GastStep()

        with unit.assigned_context(context):
            assert unit._message_logged is False
            assert unit.run(state, gast_package_version) is None
            assert unit._message_logged is False
