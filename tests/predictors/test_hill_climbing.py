#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

"""Test implementation of hill climbing in the state space."""

import flexmock
from hypothesis import given
from hypothesis.strategies import integers

import random

from thoth.adviser.beam import Beam
from thoth.adviser.predictors import HillClimbing
from thoth.adviser.state import State

from ..base import AdviserTestCase


class TestHillClimbing(AdviserTestCase):
    """Tests related to sampling the state space."""

    @given(
        integers(min_value=1, max_value=1024),
    )
    def test_run(self, state_count: int) -> None:
        """Test running the sampling method."""
        beam = Beam()
        for _ in range(state_count):
            state = State(score=random.random())
            beam.add_state(state)

        predictor = HillClimbing()
        context = flexmock(accepted_final_states_count=33)
        next_state = predictor.run(context, beam)
        assert next_state is not None
        assert next_state is beam.top()
