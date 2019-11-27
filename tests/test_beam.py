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

"""Test implementation of Beam search part in adviser's implementation."""

import pytest

from hypothesis import given
from hypothesis.strategies import integers
from thoth.adviser.beam import Beam
from thoth.adviser.state import State

from .base import AdviserTestCase


class TestBeam(AdviserTestCase):
    """Test beam implementation."""

    @given(integers(min_value=1))
    def test_initialization_positive(self, width: int) -> None:
        """Test initialization of beam."""
        beam = Beam(width=width)
        assert beam.width == width
        assert beam.states == []

    @given(integers(max_value=0))
    def test_initialization_not_positive_error(self, width: int) -> None:
        """Test initialization of beam - passing negative or zero causes an exception being raised."""
        with pytest.raises(ValueError):
            Beam(width=width)

    def test_wipe(self) -> None:
        """Test wiping out beam states."""
        beam = Beam()

        state1 = State(score=1.0)
        beam.add_state(state1)

        state2 = State(score=0.0)
        beam.add_state(state2)

        assert beam.states == [state1, state2]
        assert beam.iter_states() == [state2, state1]

        assert beam.wipe() is None
        assert beam.iter_states() == []
        assert beam.states == []

        beam.add_state(state1)
        beam.add_state(state2)
        assert beam.states == [state1, state2]
        assert beam.iter_states() == [state2, state1]

    def test_add_state(self) -> None:
        """Test adding state to the beam - respect beam width."""
        beam = Beam(width=2)
        assert beam.width == 2

        state1 = State(score=1.0)
        beam.add_state(state1)
        assert beam.width == 2
        assert len(beam.states) == 1
        assert state1 in beam.states

        state2 = State(score=2.0)
        beam.add_state(state2)
        assert beam.width == 2
        assert len(beam.states) == 2
        assert state2 in beam.states

        state3 = State(score=3.0)
        beam.add_state(state3)
        assert beam.width == 2
        assert len(beam.states) == 2
        assert state3 in beam.states
        assert state2 in beam.states
        assert state1 not in beam.states

        state0 = State(score=0.0)
        beam.add_state(state0)
        assert beam.width == 2
        assert len(beam.states) == 2
        assert state3 in beam.states
        assert state2 in beam.states
        assert state1 not in beam.states
        assert state0 not in beam.states

    def test_states(self) -> None:
        """Test asking for states returns a sorted list of states."""
        beam = Beam(width=4)
        assert beam.width == 4

        state1 = State(score=1.0)
        beam.add_state(state1)
        state3 = State(score=3.0)
        beam.add_state(state3)
        state0 = State(score=0.0)
        beam.add_state(state0)
        state2 = State(score=2.0)
        beam.add_state(state2)

        assert beam.states == [state3, state2, state1, state0]

    def test_add_state_order_multi(self) -> None:
        """Test adding states to beam and order during addition when score is same."""
        beam = Beam(width=2)

        state01 = State(score=0.0)
        state01.add_justification([{"state": "01"}])
        beam.add_state(state01)

        state02 = State(score=0.0)
        state02.add_justification([{"state": "02"}])
        beam.add_state(state02)

        state03 = State(score=0.0)
        state03.add_justification([{"state": "03"}])
        beam.add_state(state03)

        state04 = State(score=0.0)
        state04.add_justification([{"state": "04"}])
        beam.add_state(state04)

        assert beam.states == [state01, state02]

    def test_add_state_order_single(self) -> None:
        """Test adding states to beam and order during addition when score is same."""
        beam = Beam(width=1)

        state01 = State(score=0.0)
        state01.add_justification([{"state": "01"}])
        beam.add_state(state01)

        state02 = State(score=0.0)
        state02.add_justification([{"state": "02"}])
        beam.add_state(state02)

        assert beam.states == [state01]
