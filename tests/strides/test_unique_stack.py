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

"""Test filtering duplicate stacks."""

from flexmock import flexmock
import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.state import State
from thoth.adviser.strides import UniqueStackStride
from thoth.adviser.pipeline_builder import PipelineBuilderContext

from ..base import AdviserTestCase


class TestUniqueStackStride(AdviserTestCase):
    """Test filtering duplicate stacks."""

    @pytest.mark.parametrize(
        "recommendation_type,decision_type",
        [*((v, None) for v in RecommendationType.__members__), *((None, d) for d in DecisionType.__members__),],
    )
    def test_should_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
    ) -> None:
        """Test no inclusion of this pipeline unit."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        assert builder_context.is_adviser_pipeline() or builder_context.is_dependency_monkey_pipeline()
        assert UniqueStackStride.should_include(builder_context) is None

    def test_run(self) -> None:
        """Test running this stride to filter same stacks."""
        context = flexmock()

        state = State()
        state.add_resolved_dependency(("tensorflow", "2.2.0", "https://pypi.org/simple"))

        unit = UniqueStackStride()
        with unit.assigned_context(context):
            assert unit.run(state) is None

            # Running the stride on the same stack should cause rejecting it.
            with pytest.raises(NotAcceptable):
                unit.run(state)

            # A stack with another package should be included.
            state.add_resolved_dependency(("numpy", "1.19.1", "https://pypi.org/simple"))
            assert unit.run(state) is None
