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

"""Test a sieve that makes sure the right TensorFlow version is used when running on Python 3.9."""

from itertools import product

import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import TensorFlowPython39Sieve
from thoth.adviser.context import Context
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlowPython39Sieve(AdviserUnitTestCase):
    """Test a sieve that makes sure the right TensorFlow version is used when running on Python 3.9."""

    UNIT_TESTED = TensorFlowPython39Sieve

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        builder_context.project.runtime_environment.python_version = "3.9"

        for package_name in ("tensorflow", "tensorflow-gpu", "intel-tensorflow"):
            pipeline_config = self.UNIT_TESTED.should_include(builder_context)
            assert pipeline_config is not None
            assert pipeline_config == {"package_name": package_name}

            unit = self.UNIT_TESTED()
            unit.update_configuration(pipeline_config)

            builder_context.add_unit(unit)

        assert self.UNIT_TESTED.should_include(builder_context) is None, "The unit must not be included"

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
        "recommendation_type,python_version",
        list(
            product(
                [RecommendationType.STABLE, RecommendationType.PERFORMANCE, RecommendationType.SECURITY],
                ["3.9"],
            )
        ),
    )
    def test_include(
        self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType, python_version: str
    ) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.python_version = python_version
        assert builder_context.is_adviser_pipeline()
        assert TensorFlowPython39Sieve.should_include(builder_context) is not None

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,python_version",
        [
            (RecommendationType.LATEST, None, "3.9"),  # Do not include for LATEST
            (RecommendationType.TESTING, None, "3.9"),  # Do not include for TESTING
            (None, DecisionType.RANDOM, "3.9"),  # A Dependency Monkey run
            (RecommendationType.STABLE, None, "3.6"),  # Older Python version.
            (RecommendationType.STABLE, None, None),  # No Python version.
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
        python_version: str,
    ) -> None:
        """Test not including this pipeline unit."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.python_version = python_version
        assert builder_context.is_adviser_pipeline() or builder_context.is_dependency_monkey_pipeline()
        assert TensorFlowPython39Sieve.should_include(builder_context) is None

    @pytest.mark.parametrize(
        "package_name,package_version",
        [
            ("intel-tensorflow", "2.5.0"),
            ("tensorflow", "2.5.0"),
            ("tensorflow-gpu", "2.5.0"),
        ],
    )
    def test_run_yield(self, context: Context, package_name: str, package_version: str) -> None:
        """Test packages the pipeline unit yields respecting Python version compatibility."""
        package_version = PackageVersion(
            name=package_name,
            version=f"=={package_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (package_version,))))
            assert len(result) == 1
            assert result[0] is package_version

    @pytest.mark.parametrize(
        "package_name,package_version",
        [
            ("intel-tensorflow", "2.4.0"),
            ("tensorflow", "2.4.0"),
            ("tensorflow-gpu", "2.4.0"),
            ("intel-tensorflow", "2.3.0"),
            ("tensorflow", "2.3.0"),
            ("tensorflow-gpu", "2.3.0"),
            ("intel-tensorflow", "2.2.0"),
            ("tensorflow", "2.2.0"),
            ("tensorflow-gpu", "2.2.0"),
            ("intel-tensorflow", "1.12.0"),
            ("tensorflow", "1.12.0"),
            ("tensorflow-gpu", "1.12.0"),
        ],
    )
    def test_run_no_yield(self, context: Context, package_name: str, package_version: str) -> None:
        """Test packages the pipeline unit does not yield respecting Python version compatibility."""
        package_version = PackageVersion(
            name=package_name,
            version=f"=={package_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (package_version,))))
            assert len(result) == 0

    def test_sieve_multiple(self, context: Context) -> None:
        """Test proper implementation of the filtering mechanism."""
        context.project.runtime_environment.python_version = "3.9"
        source = Source("https://pypi.org/simple")
        pv_1 = PackageVersion(
            name="tensorflow-gpu",
            version="==1.12.0",
            develop=False,
            index=source,
        )
        pv_2 = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            develop=False,
            index=source,
        )
        pv_3 = PackageVersion(
            name="intel-tensorflow",
            version="==1.13.0",
            develop=False,
            index=source,
        )

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (pv_1, pv_2, pv_3))))
            assert len(result) == 0
