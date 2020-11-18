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

"""Test removing SciPy from a TensorFlow>=2.1<2.3 stack."""

from itertools import product

import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.steps import TensorFlowRemoveSciPyStep
from thoth.adviser.exceptions import SkipPackage
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlowRemoveSciPyStep(AdviserUnitTestCase):
    """Test related to removing SciPy from a TensorFlow>=2.1<2.3 stack."""

    UNIT_TESTED = TensorFlowRemoveSciPyStep

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize(
        "recommendation_type", [RecommendationType.STABLE, RecommendationType.PERFORMANCE, RecommendationType.SECURITY]
    )
    def test_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        assert "scipy" not in builder_context.project.pipfile.packages
        assert builder_context.is_adviser_pipeline()
        assert TensorFlowRemoveSciPyStep.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,add_direct_scipy",
        [
            (RecommendationType.LATEST, None, False),
            (RecommendationType.TESTING, None, False),
            (RecommendationType.STABLE, None, True),
            (None, DecisionType.RANDOM, False),
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
        add_direct_scipy: bool,
    ) -> None:
        """Test not including this pipeline unit step."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type

        if add_direct_scipy:
            builder_context.project.add_package(package_name="scipy", package_version="==1.2.2", develop=False)
            assert "scipy" in builder_context.project.pipfile.packages.packages

        assert TensorFlowRemoveSciPyStep.should_include(builder_context) is None

    @pytest.mark.parametrize(
        "tf_name,tf_version",
        [
            *product(
                ["tensorflow", "tensorflow-cpu", "tensorflow-gpu", "intel-tensorflow"],
                ["2.1.0", "2.1.1", "2.2.0rc0", "2.2.0"],
            )
        ],
    )
    def test_run_skip_package(self, context: Context, state: State, tf_name: str, tf_version: str) -> None:
        """Test removing scipy from a TensorFlow stack."""
        scipy_package_version = PackageVersion(
            name="scipy",
            version="==1.2.2",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )
        tf_package_version = PackageVersion(
            name=tf_name,
            version=f"=={tf_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        assert "tensorflow" not in state.resolved_dependencies
        state.resolved_dependencies["tensorflow"] = tf_package_version.to_tuple()
        context.register_package_version(tf_package_version)
        context.dependents["scipy"] = {
            scipy_package_version.to_tuple(): {(tf_package_version.to_tuple(), "rhel", "8", "3.6")}
        }

        with TensorFlowRemoveSciPyStep.assigned_context(context):
            unit = TensorFlowRemoveSciPyStep()
            with pytest.raises(SkipPackage):
                unit.run(state, scipy_package_version)

    @pytest.mark.parametrize(
        "tf_name,tf_version",
        [
            *product(
                ["tensorflow", "tensorflow-cpu", "tensorflow-gpu", "intel-tensorflow"],
                ["2.0.0", "1.9.1", "1.15.3", "2.3.0"],
            )
        ],
    )
    def test_run_noop(self, context: Context, state: State, tf_name: str, tf_version: str) -> None:
        """Test not removing scipy from a TensorFlow stack."""
        scipy_package_version = PackageVersion(
            name="scipy",
            version="==1.2.2",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )
        tf_package_version = PackageVersion(
            name=tf_name,
            version=f"=={tf_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        assert "tensorflow" not in state.resolved_dependencies
        state.resolved_dependencies["tensorflow"] = tf_package_version.to_tuple()
        context.register_package_version(tf_package_version)
        context.dependents["scipy"] = {
            scipy_package_version.to_tuple(): {(tf_package_version.to_tuple(), "rhel", "8", "3.6")}
        }

        unit = TensorFlowRemoveSciPyStep()
        with TensorFlowRemoveSciPyStep.assigned_context(context):
            assert unit.run(state, scipy_package_version) is None

    def test_run_deps(self, context: Context, state: State) -> None:
        """Test not removing scipy from a TensorFlow stack if introduced by another dependency."""
        scipy_package_version = PackageVersion(
            name="scipy",
            version="==1.2.2",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )
        tf_package_version = PackageVersion(
            name="tensorflow",
            version="==2.2.0",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )
        another_package_version = PackageVersion(
            name="some-package",
            version="==1.0.0",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        assert "tensorflow" not in state.resolved_dependencies
        state.resolved_dependencies["tensorflow"] = tf_package_version.to_tuple()
        state.resolved_dependencies[another_package_version.name] = another_package_version.to_tuple()
        context.register_package_version(tf_package_version)
        context.dependents["scipy"] = {
            scipy_package_version.to_tuple(): {
                (tf_package_version.to_tuple(), "rhel", "8", "3.6"),
                (another_package_version.to_tuple(), "rhel", "8", "3.6"),
            }
        }

        unit = TensorFlowRemoveSciPyStep()
        with TensorFlowRemoveSciPyStep.assigned_context(context):
            assert unit.run(state, scipy_package_version) is None
