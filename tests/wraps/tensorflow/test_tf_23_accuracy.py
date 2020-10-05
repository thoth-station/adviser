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

"""Test wrap that notifies about accuracy bug on safe()/load_model() calls."""

import pytest

from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import TensorFlow23Accuracy

from ...base import AdviserUnitTestCase


class TestTensorFlow23Accuracy(AdviserUnitTestCase):
    """Test wrap that notifies about accuracy bug on safe()/load_model() calls."""

    UNIT_TESTED = TensorFlow23Accuracy

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)

        for package_name in ("tensorflow", "tensorflow-cpu", "tensorflow-gpu", "intel-tensorflow"):
            pipeline_config = self.UNIT_TESTED.should_include(builder_context)
            assert pipeline_config is not None
            assert pipeline_config == {"package_name": package_name}

            unit = self.UNIT_TESTED()
            unit.update_configuration(pipeline_config)

            builder_context.add_unit(unit)

        assert self.UNIT_TESTED.should_include(builder_context) is None, "The unit must not be included"

    def test_run_noop(self) -> None:
        """Test no justification added if TensorFlow 2.3 is not resolved."""
        state = State()
        assert not state.justification
        assert "tensorflow" not in state.resolved_dependencies

        state.add_resolved_dependency(("tensorflow", "2.2.0", "https://pypi.org/simple"))

        unit = TensorFlow23Accuracy()
        unit.run(state)

        assert len(state.justification) == 0

    @pytest.mark.parametrize("tf_version", ["2.3.0"])
    def test_run(self, tf_version: str) -> None:
        """Test adding justification added if TensorFlow 2.3 is not resolved."""
        state = State()
        assert not state.justification
        assert "tensorflow" not in state.resolved_dependencies

        state.add_resolved_dependency(("tensorflow", tf_version, "https://pypi.org/simple"))

        unit = TensorFlow23Accuracy()
        unit.run(state)

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message", "link"}
        assert state.justification[0]["type"] == "WARNING"
        assert state.justification[0]["message"], "No justification message provided"
        assert state.justification[0]["link"], "Empty link to justification document provided"
