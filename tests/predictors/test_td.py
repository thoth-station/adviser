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

"""Test implementation of Temporal Difference (TD) based predictor with annealing schedule."""

import flexmock

from hypothesis import given
from hypothesis.strategies import integers
from hypothesis.strategies import floats

from thoth.adviser.predictors import TemporalDifference

from ..base import AdviserTestCase


class TestTemporalDifference(AdviserTestCase):
    """Test implementation of Temporal Difference (TD) based predictor with annealing schedule."""

    @given(
        floats(allow_nan=False, allow_infinity=False),
        floats(allow_nan=False, allow_infinity=False),
        floats(min_value=0.0, allow_nan=False, allow_infinity=False),
    )
    def test_acceptance_probability(
        self, top_score: float, neighbour_score: float, temperature: float
    ) -> None:
        """Test acceptance probability is always between 0 and 1."""
        acceptance_probability = TemporalDifference._compute_acceptance_probability(
            top_score=top_score,
            neighbour_score=neighbour_score,
            temperature=temperature,
        )
        assert (
            0.0 <= acceptance_probability <= 1.0
        ), "Acceptance probability not within 0 and 1"

    @given(
        floats(min_value=0.0, allow_nan=False, allow_infinity=False),
        integers(min_value=0),
        integers(min_value=1),
        integers(min_value=0),
        integers(min_value=0),
    )
    def test_temperature_function(
        self,
        t0: float,
        accepted_final_states_count: int,
        limit: int,
        iteration: int,
        count: int,
    ) -> None:
        """Test the temperature function never drops bellow 0."""
        context = flexmock(
            accepted_final_states_count=accepted_final_states_count,
            limit=limit,
            iteration=iteration,
            count=count,
            beam=flexmock(size=96),
        )

        predictor = TemporalDifference()
        assert (
            predictor._temperature_function(t0=t0, context=context) >= 0.0
        ), "Temperature dropped bellow 0 or is NaN"

    def test_pre_run(self) -> None:
        """Test initialization done before running."""

    def test_set_reward_signal(self) -> None:
        """Test keeping the reward signal."""

    def test_do_exploitation(self) -> None:
        """Tests on exploitation."""
        # TODO: implement

    def test_do_exploration(self) -> None:
        """Tests on exploration."""
        # TODO: implement
