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

"""Test implementation of Adaptive Simulated Annealing (ASA)."""

import os
import flexmock

from hypothesis import given
from hypothesis.strategies import integers
from hypothesis.strategies import floats

from thoth.adviser.predictors import AdaptiveSimulatedAnnealing
from thoth.adviser.enums import RecommendationType

from ..base import AdviserTestCase


class TestAdaptiveSimulatedAnnealing(AdviserTestCase):
    """Tests related to Adaptive Simulated Annealing (ASA)."""

    @given(
        floats(min_value=0.0, allow_nan=False, allow_infinity=False),
        integers(min_value=1),
        integers(min_value=1),
    )
    def test_exp(self, t0: float, count: int, limit: int) -> None:
        """Test the exp function never drops bellow 0."""
        # Iteration parameter has no effect.
        assert (
            AdaptiveSimulatedAnnealing._exp(
                iteration=0, t0=t0, count=count, limit=limit
            )
            >= 0.0
        ), "Temperature dropped bellow 0 or is NaN"

    @given(
        floats(allow_nan=False, allow_infinity=False),
        floats(allow_nan=False, allow_infinity=False),
        floats(min_value=0.0, allow_nan=False, allow_infinity=False),
    )
    def test_acceptance_probability(
        self, top_score: float, neighbour_score: float, temperature: float
    ) -> None:
        """Test acceptance probability is always between 0 and 1."""
        acceptance_probability = AdaptiveSimulatedAnnealing._compute_acceptance_probability(
            top_score=top_score,
            neighbour_score=neighbour_score,
            temperature=temperature,
        )
        assert (
            0.0 <= acceptance_probability <= 1.0
        ), "Acceptance probability not within 0 and 1"

    def test_keep_temperature_history_init(self) -> None:
        """Test initialization of temperature history."""
        assert "THOTH_ADVISER_NO_HISTORY" not in os.environ
        predictor = AdaptiveSimulatedAnnealing()
        assert (
            predictor.keep_temperature_history is True
        ), "Temperature history not kept by default"

        flexmock(os)
        os.should_receive("getenv").with_args("THOTH_ADVISER_NO_HISTORY", 0).and_return(
            "0"
        ).and_return("1").twice()

        predictor = AdaptiveSimulatedAnnealing()
        assert predictor.keep_temperature_history is True

        predictor = AdaptiveSimulatedAnnealing()
        assert predictor.keep_temperature_history is False

    def test_pre_run(self) -> None:
        """Test pre-run initialization."""
        context = flexmock(limit=100)

        predictor = AdaptiveSimulatedAnnealing()
        assert predictor._temperature == 0.0
        predictor._temperature_history = [(0.1, False, 0.2, 3), (0.42, True, 0.66, 47)]

        predictor.pre_run(context)
        assert (
            predictor._temperature == context.limit
        ), "Predictor's limit not initialized correctly"
        assert (
            predictor._temperature_history == []
        ), "Predictor's temperature history no discarded"

    def test_run_latest(self) -> None:
        """Test running simulated annealing for latest recommendation (hill climbing)."""
        flexmock(AdaptiveSimulatedAnnealing)
        predictor = AdaptiveSimulatedAnnealing()
        context = flexmock(recommendation_type=RecommendationType.LATEST)

        # Only recommendation type is accessed.
        assert predictor.run(context, None) == 0
