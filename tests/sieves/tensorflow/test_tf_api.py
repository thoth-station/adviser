#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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

"""Test using the right TensorFlow release based on library usage (symbols used) supplied."""

import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import TensorFlowAPISieve
from thoth.adviser.context import Context
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlowAPISieve(AdviserUnitTestCase):
    """Test using the right TensorFlow release for specific CUDA releases."""

    UNIT_TESTED = TensorFlowAPISieve

    _PACKAGES_AFFECTED = [
        "tensorflow",
        "tensorflow-gpu",
        "intel-tensorflow",
        "tensorflow-cpu",
    ]

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        builder_context.library_usage = {"report": {"flask": ["flask.Flask"], "tensorflow": ["tensorflow."]}}

        pipeline_config = list(self.UNIT_TESTED.should_include(builder_context))
        assert len(self._PACKAGES_AFFECTED) == len(pipeline_config)

        for package_name in self._PACKAGES_AFFECTED:
            assert package_name
            assert {"package_name": package_name} in pipeline_config

        for item in pipeline_config:
            assert pipeline_config
            unit = self.UNIT_TESTED()
            unit.update_configuration(item)
            builder_context.add_unit(unit)

        assert list(self.UNIT_TESTED.should_include(builder_context)) == [], "The unit must not be included"

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
        [RecommendationType.STABLE, RecommendationType.PERFORMANCE, RecommendationType.SECURITY],
    )
    def test_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        builder_context.library_usage = {"report": {"tensorflow": ["tensorflow.v2.__version__"]}}
        assert builder_context.is_adviser_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) != []

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,library_usage",
        [
            (RecommendationType.LATEST, None, {"report": {"tensorflow": ["tensorflow.__version__"]}}),
            (RecommendationType.TESTING, None, {"report": {"tensorflow": ["tensorflow.__version__"]}}),
            (None, DecisionType.RANDOM, {"report": {"tensorflow": ["tensorflow.__version__"]}}),  # Dependency Monkey
            (RecommendationType.STABLE, None, {"report": {"flask": "flask.Flask"}}),  # No tensorflow used.
            (RecommendationType.STABLE, None, None),  # No library usage.
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
        library_usage: str,
    ) -> None:
        """Test not including this pipeline unit."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        builder_context.library_usage = library_usage
        assert builder_context.is_adviser_pipeline() or builder_context.is_dependency_monkey_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_sieve(self, context: Context) -> None:
        """Test sieving TensorFlow based on API symbols."""
        context.library_usage = {
            # run_functions_eagerly available since 2.3.0.
            "report": {"tensorflow": ["tensorflow.v2.__version__", "tensorflow.raw_ops.LoadDataset"]}
        }
        source = Source("https://pypi.org/simple")
        pv_0 = PackageVersion(
            name="tensorflow-gpu",
            version="==2.2.0",
            develop=False,
            index=source,
        )
        pv_1 = PackageVersion(
            name="tensorflow",
            version="==2.2.0",
            develop=False,
            index=source,
        )
        pv_2 = PackageVersion(
            name="tensorflow",
            version="==2.3.0",
            develop=False,
            index=source,
        )
        pv_3 = PackageVersion(
            name="intel-tensorflow",
            version="==2.4.0",
            develop=False,
            index=source,
        )
        pv_4 = PackageVersion(
            name="tensorflow",
            version="==1.13.0",
            develop=False,
            index=source,
        )

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (pv_0, pv_1, pv_2, pv_3, pv_4))))
            assert len(result) == 2
            assert result == [pv_2, pv_3]

    def test_unknown_symbol(self, context: Context) -> None:
        """Test no sieving is done if an unknown symbol is spotted."""
        context.library_usage = {
            # run_functions_eagerly available since 2.3.0.
            "report": {"tensorflow": ["tensorflow.SomeUnknownSymbol"]}
        }
        source = Source("https://pypi.org/simple")
        pv_0 = PackageVersion(
            name="tensorflow",
            version="==2.2.0",
            develop=False,
            index=source,
        )
        pv_1 = PackageVersion(
            name="tensorflow",
            version="==2.3.0",
            develop=False,
            index=source,
        )
        pv_2 = PackageVersion(
            name="tensorflow",
            version="==2.4.0",
            develop=False,
            index=source,
        )

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (pv_0, pv_1, pv_2))))
            assert len(result) == 3
            assert result == [pv_0, pv_1, pv_2]

    def test_multiple_calls(self, context: Context) -> None:
        """Test multiple calls of resolver invalidate internal caches."""
        context.library_usage = {
            # run_functions_eagerly available since 2.3.0.
            "report": {"tensorflow": ["tensorflow.v2.__version__", "tensorflow.raw_ops.LoadDataset"]}
        }
        source = Source("https://pypi.org/simple")
        pv_1 = PackageVersion(
            name="tensorflow",
            version="==2.2.0",
            develop=False,
            index=source,
        )
        pv_2 = PackageVersion(
            name="tensorflow",
            version="==2.3.0",
            develop=False,
            index=source,
        )

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (pv_1, pv_2))))
            assert len(result) == 1
            assert result == [pv_2]

        # Now without symbols introduced in 2.3.0 on the same unit instance.
        context.library_usage = {
            # run_functions_eagerly available since 2.3.0.
            "report": {"tensorflow": ["tensorflow.v2.__version__"]}
        }

        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (pv_1, pv_2))))
            assert len(result) == 2
            assert result == [pv_1, pv_2]
