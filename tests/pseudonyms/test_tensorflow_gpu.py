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

"""Test recommending tensorflow-gpu where tensorflow runs on CUDA."""

import pytest

from typing import List

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.pseudonyms import TensorFlowGPUPseudonym
from thoth.adviser.context import Context
from thoth.python import PackageVersion
from thoth.python import Source

from ..base import AdviserUnitTestCase


class TestTensorFlowGPUPseudonym(AdviserUnitTestCase):
    """Test recommending tensorflow-gpu where tensorflow runs on CUDA."""

    UNIT_TESTED = TensorFlowGPUPseudonym

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        builder_context.project.runtime_environment.cuda_version = "10.1"
        self.verify_multiple_should_include(builder_context)

    def test_recommendation_types_considered(self) -> None:
        """Test recommendation types that were considered during implementation of this pipeline unit.

        This test will fail when a new recommendation type is added. In such case, review the pipeline unit
        implementation and adjust it accordingly.
        """
        assert set(RecommendationType) == {
            RecommendationType.STABLE,
            RecommendationType.TESTING,
            RecommendationType.LATEST,
            RecommendationType.PERFORMANCE,
            RecommendationType.SECURITY,
        }

    @pytest.mark.parametrize(
        "recommendation_type",
        [
            RecommendationType.TESTING,
            RecommendationType.STABLE,
            RecommendationType.PERFORMANCE,
            RecommendationType.SECURITY,
        ],
    )
    def test_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.cuda_version = "10.1"
        assert builder_context.is_adviser_pipeline()
        assert self.UNIT_TESTED.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,cuda_version",
        [
            (RecommendationType.LATEST, None, "10.1"),  # Do not include for LATEST
            (RecommendationType.PERFORMANCE, None, None),  # Do not include when no CUDA is used.
            (None, DecisionType.RANDOM, None),  # A Dependency Monkey run
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
        cuda_version: str,
    ) -> None:
        """Test not including this pipeline unit."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.cuda_version = cuda_version
        assert builder_context.is_adviser_pipeline() or builder_context.is_dependency_monkey_pipeline()
        assert self.UNIT_TESTED.should_include(builder_context) is None

    def test_pre_run(self, context: Context) -> None:
        """Test initializing the pipeline unit."""
        unit = self.UNIT_TESTED()

        assert not unit._pseudonyms
        unit._pseudonyms = frozenset({"1.2.2"})

        with unit.assigned_context(context):
            unit.pre_run()

        assert not unit._pseudonyms

    def test_run_pseudonym(self, context: Context) -> None:
        """Test adding a pseudonym for TensorFlow."""
        unit = self.UNIT_TESTED()

        package_version = PackageVersion(
            name=unit.configuration["package_name"],
            version="==1.0.0",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        context.graph.should_receive("get_solved_python_package_versions_all").with_args(
            package_name="tensorflow-gpu",
            package_version=None,
            index_url="https://pypi.org/simple",
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return(
            [
                ("tensorflow-gpu", "1.0.0", "https://pypi.org/simple"),
                ("tensorflow-gpu", "2.0.0", "https://pypi.org/simple"),
            ]
        ).once()

        with unit.assigned_context(context):
            unit.pre_run()
            result = unit.run(package_version)
            assert list(result) == [("tensorflow-gpu", package_version.locked_version, package_version.index.url)]

    @pytest.mark.parametrize("tf_versions", [[], ["2.0.0"]])
    def test_run_noop(self, context: Context, tf_versions: List[str]) -> None:
        """Test not adding a pseudonym for TensorFlow if no alternative releases found."""
        unit = self.UNIT_TESTED()

        package_version = PackageVersion(
            name=unit.configuration["package_name"],
            version="==1.0.0",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        context.graph.should_receive("get_solved_python_package_versions_all").with_args(
            package_name="tensorflow-gpu",
            package_version=None,
            index_url="https://pypi.org/simple",
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return(tf_versions).once()

        with unit.assigned_context(context):
            unit.pre_run()
            assert list(unit.run(package_version)) == []
