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

"""Test a wrap that notifies a bug that prevents from running TensorFlow if multiple processes are running on GPU."""

from thoth.adviser.context import Context
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import TensorFlowMultipleProcessesGPUBug

from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestIntelTensorflowWrap(AdviserUnitTestCase):
    """Test a wrap that notifies a bug that prevents from running TensorFlow when running on GPU."""

    UNIT_TESTED = TensorFlowMultipleProcessesGPUBug

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE

        for package_name in ("tensorflow",):
            pipeline_config = self.UNIT_TESTED.should_include(builder_context)
            assert pipeline_config is not None
            assert pipeline_config == {"package_name": package_name}

            unit = self.UNIT_TESTED()
            unit.update_configuration(pipeline_config)

            builder_context.add_unit(unit)

        self.verify_multiple_should_include(builder_context)

    def test_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = RecommendationType.LATEST
        assert builder_context.is_adviser_pipeline()
        assert not builder_context.is_dependency_monkey_pipeline()
        assert self.UNIT_TESTED.should_include(builder_context) is not None

    def test_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including this pipeline unit."""
        builder_context.decision_type = DecisionType.RANDOM
        builder_context.recommendation_type = None
        assert builder_context.is_dependency_monkey_pipeline()
        assert self.UNIT_TESTED.should_include(builder_context) is None

    def test_run(self, state: State, context: Context) -> None:
        """Test running this wrap."""
        state = State()
        assert not state.justification

        state.resolved_dependencies["tensorflow"] = ("tensorflow", "2.3.0", "https://pypi.org/simple")
        unit = self.UNIT_TESTED()

        tf_package_version = PackageVersion(
            name="tensorflow",
            version="==2.3.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        context.register_package_version(tf_package_version)

        with unit.assigned_context(context):
            unit.run(state)

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message", "link"}
        assert state.justification[0]["link"], "Empty link to justification document provided"
        assert state.justification[0]["type"] == "WARNING"
        assert (
            state.justification[0]["message"]
            == "TensorFlow in version 2.3 has a bug that prevents from running if multiple "
            "TensorFlow processes are running"
        )

    def test_run_no_justification(self, state: State) -> None:
        """Test running this wrap without justification being produced."""
        state = State()
        assert not state.justification

        state.resolved_dependencies.pop("tensorflow", None)
        unit = self.UNIT_TESTED()
        unit.run(state)

        assert len(state.justification) == 0
