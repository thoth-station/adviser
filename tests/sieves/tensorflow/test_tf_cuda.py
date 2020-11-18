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

"""Test using the right TensorFlow release for specific CUDA releases."""

from typing import Tuple
from itertools import product

import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import TensorFlowCUDASieve
from thoth.adviser.context import Context
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlowCUDASieve(AdviserUnitTestCase):
    """Test using the right TensorFlow release for specific CUDA releases."""

    UNIT_TESTED = TensorFlowCUDASieve

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        builder_context.project.runtime_environment.cuda_version = "10.1"

        for package_name in ("tensorflow", "tensorflow-gpu"):
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
        "recommendation_type,cuda_version",
        list(
            product(
                [RecommendationType.STABLE, RecommendationType.PERFORMANCE, RecommendationType.SECURITY],
                ["8", "9", "10.0", "10.1"],
            )
        ),
    )
    def test_include(
        self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType, cuda_version: str
    ) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.cuda_version = cuda_version
        assert builder_context.is_adviser_pipeline()
        assert TensorFlowCUDASieve.should_include(builder_context) is not None

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,cuda_version",
        [
            (RecommendationType.LATEST, None, "10.1"),  # Do not include for LATEST
            (RecommendationType.TESTING, None, "10.1"),  # Do not include for TESTING
            (None, DecisionType.RANDOM, "10.0"),  # A Dependency Monkey run
            (RecommendationType.STABLE, None, "UNKNOWN_CUDA_VERSION"),  # Unknown CUDA version
            (RecommendationType.STABLE, None, None),  # No CUDA version provided
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
        assert TensorFlowCUDASieve.should_include(builder_context) is None

    @pytest.mark.parametrize(
        "cuda_version,expected_tf_1_support,expected_tf_2_support",
        [
            ("8", "_TF_1_CUDA_8_SUPPORT", "_EMPTY"),
            ("9", "_TF_1_CUDA_9_SUPPORT", "_EMPTY"),
            ("10.0", "_TF_1_CUDA_10_0_SUPPORT", "_TF_2_CUDA_10_0_SUPPORT"),
            ("10.1", "_EMPTY", "_TF_2_CUDA_10_1_SUPPORT"),
            ("UNKNOWN_CUDA_VERSION", "_EMPTY", "_EMPTY"),  # Should not happen based on should_include
        ],
    )
    def test_pre_run(
        self, context: Context, cuda_version: str, expected_tf_1_support: str, expected_tf_2_support: str
    ) -> None:
        """Test initializing the pipeline unit."""
        unit = TensorFlowCUDASieve()

        assert unit._tf_1_cuda_support is unit._EMPTY
        assert unit._tf_2_cuda_support is unit._EMPTY

        unit._messages_logged.add("foo")
        assert unit._messages_logged

        context.project.runtime_environment.cuda_version = cuda_version

        with unit.assigned_context(context):
            unit.pre_run()

        assert not unit._messages_logged
        assert unit._tf_1_cuda_support is getattr(unit, expected_tf_1_support)
        assert unit._tf_2_cuda_support is getattr(unit, expected_tf_2_support)

    @pytest.mark.parametrize("package_name", ["tensorflow", "tensorflow-gpu"])
    def test_unknown_tensorflow(self, context: Context, package_name: str) -> None:
        """Test not discarding if an unknown TensorFlow release is spotted."""
        context.project.runtime_environment.cuda_version = "10.0"
        package_version = PackageVersion(
            name=package_name,
            version="==42.30.03",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        unit = TensorFlowCUDASieve()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (package_version,))))
            assert len(result) == 1
            assert result[0] is package_version, "The pipeline unit should keep the unknown TensorFlow release"

    @pytest.mark.parametrize(
        "package_name,package_version,cuda_version",
        [
            ("tensorflow", "2.3.0", "10.1"),
            ("tensorflow-gpu", "2.3.0", "10.1"),
            ("tensorflow", "2.2.0", "10.1"),
            ("tensorflow-gpu", "2.2.0", "10.1"),
            ("tensorflow", "2.1.0", "10.1"),
            ("tensorflow-gpu", "2.1.0", "10.1"),
            ("tensorflow", "2.0.0", "10.0"),
            ("tensorflow-gpu", "2.0.0", "10.0"),
            ("tensorflow_gpu", "1.15.0", "10.0"),
            ("tensorflow_gpu", "1.14.0", "10.0"),
            ("tensorflow_gpu", "1.13.1", "10.0"),
            ("tensorflow_gpu", "1.12.0", "9"),
            ("tensorflow_gpu", "1.11.0", "9"),
            ("tensorflow_gpu", "1.10.0", "9"),
            ("tensorflow_gpu", "1.9.0", "9"),
            ("tensorflow_gpu", "1.8.0", "9"),
            ("tensorflow_gpu", "1.7.0", "9"),
            ("tensorflow_gpu", "1.6.0", "9"),
            ("tensorflow_gpu", "1.5.0", "9"),
            ("tensorflow_gpu", "1.4.0", "8"),
            ("tensorflow_gpu", "1.3.0", "8"),
            ("tensorflow_gpu", "1.2.0", "8"),
            ("tensorflow_gpu", "1.1.0", "8"),
            ("tensorflow_gpu", "1.0.0", "8"),
        ],
    )
    def test_run_yield(self, context: Context, package_name: str, package_version: str, cuda_version: str) -> None:
        """Test packages the pipeline unit yields respecting CUDA version used.

        See the official docs for listing:
           https://www.tensorflow.org/install/source#gpu
        """
        context.project.runtime_environment.cuda_version = cuda_version
        package_version = PackageVersion(
            name=package_name,
            version=f"=={package_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        unit = TensorFlowCUDASieve()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (package_version,))))
            assert len(result) == 1
            assert result[0] is package_version

    @pytest.mark.parametrize(
        "pv,cuda_version",
        [
            *product((("tensorflow", "2.3.0"),), ("10.0", "9", "8")),
            *product((("tensorflow", "2.2.0"),), ("10.0", "9", "8")),
            *product((("tensorflow", "2.1.0"),), ("10.0", "9", "8")),
            *product((("tensorflow", "2.0.0"),), ("10.1", "9", "8")),
            *product((("tensorflow", "1.15.0"),), ("10.1", "10.0", "9", "8")),
            *product((("tensorflow-gpu", "1.15.0"),), ("10.1", "9", "8")),
            *product((("tensorflow-gpu", "1.14.0"),), ("10.1", "9", "8")),
            *product((("tensorflow-gpu", "1.13.1"),), ("10.1", "9", "8")),
            *product((("tensorflow-gpu", "1.12.0"),), ("10.1", "10.0", "8")),
            *product((("tensorflow-gpu", "1.11.0"),), ("10.1", "10.0", "8")),
            *product((("tensorflow-gpu", "1.10.0"),), ("10.1", "10.0", "8")),
            *product((("tensorflow-gpu", "1.9.0"),), ("10.1", "10.0", "8")),
            *product((("tensorflow-gpu", "1.8.0"),), ("10.1", "10.0", "8")),
            *product((("tensorflow-gpu", "1.7.0"),), ("10.1", "10.0", "8")),
            *product((("tensorflow-gpu", "1.6.0"),), ("10.1", "10.0", "8")),
            *product((("tensorflow-gpu", "1.5.0"),), ("10.1", "10.0", "8")),
            *product((("tensorflow-gpu", "1.4.0"),), ("10.1", "10.0", "9")),
            *product((("tensorflow-gpu", "1.3.0"),), ("10.1", "10.0", "9")),
            *product((("tensorflow-gpu", "1.2.0"),), ("10.1", "10.0", "9")),
            *product((("tensorflow-gpu", "1.1.0"),), ("10.1", "10.0", "9")),
            *product((("tensorflow-gpu", "1.0.0"),), ("10.1", "10.0", "9")),
        ],
    )
    def test_run_no_yield(self, context: Context, pv: Tuple[str, str], cuda_version: str) -> None:
        """Test discarding packages that do not conform to the support matrix.

        See the official docs for listing:
           https://www.tensorflow.org/install/source#gpu
        """
        context.project.runtime_environment.cuda_version = cuda_version
        package_version = PackageVersion(
            name=pv[0],
            version=f"=={pv[1]}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        unit = TensorFlowCUDASieve()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (package_version,))))
            assert len(result) == 0

    def test_sieve_multiple(self, context: Context) -> None:
        """Test proper implementation of the filtering mechanism."""
        context.project.runtime_environment.cuda_version = "10.0"
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
            name="tensorflow",
            version="==1.13.0",
            develop=False,
            index=source,
        )

        unit = TensorFlowCUDASieve()
        with unit.assigned_context(context):
            unit.pre_run()
            result = list(unit.run((pv for pv in (pv_1, pv_2, pv_3))))
            assert len(result) == 1
            assert result[0] == pv_2
