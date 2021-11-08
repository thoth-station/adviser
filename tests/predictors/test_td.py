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

"""Test implementation of Temporal Difference (TD) based predictor with annealing schedule."""

import math
import random

from hypothesis import given
from hypothesis.strategies import floats
from hypothesis.strategies import integers
from flexmock import flexmock
import pytest

from thoth.adviser.context import Context
from thoth.adviser.predictors import TemporalDifference
from thoth.adviser.predictors import AdaptiveSimulatedAnnealing
from thoth.adviser.state import State

from ..base import AdviserTestCase


class TestTemporalDifference(AdviserTestCase):
    """Test implementation of Temporal Difference (TD) based predictor with annealing schedule."""

    @given(
        floats(allow_nan=False, allow_infinity=False),
        floats(allow_nan=False, allow_infinity=False),
        floats(min_value=0.0, allow_nan=False, allow_infinity=False),
    )
    def test_acceptance_probability(self, top_score: float, neighbour_score: float, temperature: float) -> None:
        """Test acceptance probability is always between 0 and 1."""
        acceptance_probability = TemporalDifference._compute_acceptance_probability(
            top_score=top_score,
            neighbour_score=neighbour_score,
            temperature=temperature,
        )
        assert 0.0 <= acceptance_probability <= 1.0, "Acceptance probability not within 0 and 1"

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
        assert predictor._temperature_function(t0=t0, context=context) >= 0.0, "Temperature dropped bellow 0 or is NaN"

    def test_init(self) -> None:
        """Test instantiation."""
        predictor = TemporalDifference()
        assert predictor._policy == {}
        assert predictor._temperature_history == []
        assert predictor._temperature == 0.0

    def test_pre_run(self) -> None:
        """Test initialization done before running."""
        predictor = TemporalDifference()

        predictor._policy = {("tensorflow", "2.0.0", "https://pypi.org/simple"): [1.0, 2]}
        predictor._temperature_history = [(0.212, True, 0.23, 100)]
        predictor._temperature = 12.3

        context = flexmock(limit=42)
        with predictor.assigned_context(context):
            predictor.pre_run()

        assert predictor._policy == {}
        assert predictor._temperature_history == []
        assert isinstance(predictor._temperature, float)
        assert predictor._temperature == float(context.limit)

    @pytest.mark.parametrize("float_case", [math.nan, math.inf, -math.inf])
    def test_set_reward_signal_nan_inf(self, float_case: float) -> None:
        """Test (not) keeping the reward signal for nan/inf."""
        predictor = TemporalDifference()
        state = State()
        state.add_resolved_dependency(("tensorflow", "2.3.0", "https://pypi.org/simple"))
        state.add_resolved_dependency(("flask", "0.12", "https://pypi.org/simple"))
        state.add_unresolved_dependency(("termial-random", "0.0.2", "https://pypi.org/simple"))
        predictor._policy = {
            ("flask", "0.12", "https://pypi.org/simple"): [0.2, 1],
        }
        predictor._steps_taken = 2
        predictor._steps_reward = 1.2
        predictor._next_state = state

        assert (
            predictor.set_reward_signal(state, ("tensorflow", "2.0.0", "https://pypi.org/simple"), float_case) is None
        )

        assert predictor._policy == {
            ("flask", "0.12", "https://pypi.org/simple"): [1.4, 2],
            ("tensorflow", "2.3.0", "https://pypi.org/simple"): [1.2, 1],
        }
        assert predictor._steps_taken == 0
        assert predictor._steps_reward == 0.0
        assert predictor._next_state is None

    def test_set_reward_signal_unseen(self) -> None:
        """Test keeping the reward signal for an unseen step."""
        reward = 42.24
        package_tuple = ("tensorflow", "2.0.0", "https://thoth-station.ninja")

        state = flexmock()
        state.should_receive("iter_resolved_dependencies").and_return([package_tuple]).once()

        predictor = TemporalDifference()
        predictor._policy = {
            ("numpy", "1.0.0", "https://pypi.org/simple"): [30.30, 92],
        }

        predictor._steps_taken = 1
        predictor.set_reward_signal(state, None, reward)

        assert predictor._policy == {
            package_tuple: [42.24, 1],
            ("numpy", "1.0.0", "https://pypi.org/simple"): [30.30, 92],
        }

    def test_set_reward_signal_seen(self) -> None:
        """Test keeping the reward signal for a seen step."""
        reward = 24.42
        package_tuple = ("pytorch", "1.0.2", "https://thoth-station.ninja")

        state = flexmock()
        state.should_receive("iter_resolved_dependencies").and_return([package_tuple]).once()

        predictor = TemporalDifference()
        predictor._policy = {
            package_tuple: [16.23, 2010],
            ("numpy", "1.0.0", "https://pypi.org/simple"): [30.30, 92],
        }

        predictor._steps_taken = 1
        predictor.set_reward_signal(state, None, reward)

        assert predictor._policy == {
            package_tuple: [16.23 + reward, 2011],
            ("numpy", "1.0.0", "https://pypi.org/simple"): [30.30, 92],
        }

    def test_do_exploitation(self) -> None:
        """Tests on exploitation computation."""
        predictor = TemporalDifference()
        predictor._policy = {
            ("tensorflow", "2.1.0", "https://thoth-station.ninja"): [2020.21, 666],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja"): [16.61, 1992],
            ("numpy", "1.0.0", "https://pypi.org/simple"): [30.30, 92],
        }

        state = flexmock()
        state.should_receive("iter_unresolved_dependencies").and_return(
            [
                ("spacy", "2.2.4", "https://pypi.org/simple"),
                ("numpy", "1.0.0", "https://pypi.org/simple"),
                ("tensorflow", "2.1.0", "https://thoth-station.ninja"),
            ]
        ).once()

        state.should_receive("get_random_unresolved_dependency").times(0)
        assert predictor._do_exploitation(state) == (
            "tensorflow",
            "2.1.0",
            "https://thoth-station.ninja",
        )

    def test_do_exploitation_no_records(self) -> None:
        """Tests on exploitation when no relevant records found."""
        predictor = TemporalDifference()
        assert predictor._policy == {}

        random_unresolved_dependency = (("tensorflow", "2.1.0", "https://thoth-station.ninja"),)

        state = flexmock()
        state.should_receive("iter_unresolved_dependencies").and_return(
            [
                ("micropipenv", "0.1.4", "https://pypi.org/simple"),
                random_unresolved_dependency,
            ]
        ).once()

        state.should_receive("get_random_unresolved_dependency").with_args(prefer_recent=True).and_return(
            random_unresolved_dependency
        ).once()

        assert predictor._do_exploitation(state) == random_unresolved_dependency

    def test_run_exploration(self, context: Context) -> None:
        """Tests run when exploration is performed."""
        flexmock(TemporalDifference)
        flexmock(TemporalDifference)
        flexmock(AdaptiveSimulatedAnnealing)

        flexmock(State)
        max_state = State(score=3.0)
        probable_state = State(score=2.0)

        context.beam.add_state(max_state)
        context.beam.add_state(probable_state)

        unresolved_dependency = (
            "pytorch",
            "1.0.0",
            "https://thoth-station.ninja/simple",
        )

        flexmock(random)
        random.should_receive("randrange").with_args(1, 2).and_return(0).once()
        random.should_receive("random").and_return(
            0.50
        ).once()  # *lower* than acceptance_probability that is 0.75 so we do exploitation
        probable_state.should_receive("get_random_unresolved_dependency").with_args(prefer_recent=True).and_return(
            unresolved_dependency
        ).once()
        TemporalDifference.should_receive("_temperature_function").with_args(1.0, context).and_return(0.9).once()
        AdaptiveSimulatedAnnealing.should_receive("_compute_acceptance_probability").with_args(
            max_state.score, probable_state.score, 0.9
        ).and_return(0.75).once()
        context.beam.should_receive("max").with_args().and_return(max_state).once()

        predictor = TemporalDifference(step=1)
        predictor._steps_taken = 0
        predictor._temperature = 1.0
        with predictor.assigned_context(context):
            assert predictor.run() == (probable_state, unresolved_dependency)
            assert predictor._steps_taken == 1

    def test_run_exploitation(self, context: Context) -> None:
        """Tests run when exploitation is performed."""
        flexmock(TemporalDifference)
        flexmock(AdaptiveSimulatedAnnealing)

        max_state = State(score=3.0)
        probable_state = State(score=2.0)

        context.beam.add_state(max_state)
        context.beam.add_state(probable_state)

        unresolved_dependency = (
            "pytorch",
            "1.0.0",
            "https://thoth-station.ninja/simple",
        )

        flexmock(random)
        random.should_receive("randrange").with_args(1, 2).and_return(0).once()
        random.should_receive("random").and_return(
            0.99
        ).once()  # *higher* than acceptance_probability that is 0.75 so we do exploitation
        TemporalDifference.should_receive("_do_exploitation").with_args(max_state).and_return(
            unresolved_dependency
        ).once()
        TemporalDifference.should_receive("_temperature_function").with_args(1.0, context).and_return(0.9).once()
        AdaptiveSimulatedAnnealing.should_receive("_compute_acceptance_probability").with_args(
            max_state.score, probable_state.score, 0.9
        ).and_return(0.75).once()
        context.beam.should_receive("max").with_args().and_return(max_state).once()

        predictor = TemporalDifference(step=1)
        predictor._temperature = 1.0
        predictor._steps_taken = 0
        with predictor.assigned_context(context):
            assert predictor.run() == (max_state, unresolved_dependency)
            assert predictor._steps_taken == 1

    def test_validation(self) -> None:
        """Test validation of configuration supplied for n-step TD-learning."""
        with pytest.raises(ValueError):
            TemporalDifference(step=0)

        with pytest.raises(ValueError):
            TemporalDifference(step=-3)

        with pytest.raises(ValueError):
            TemporalDifference(step="foo")

    def test_step_default(self) -> None:
        """Test default parameter for step."""
        predictor = TemporalDifference()
        assert predictor.step == 1
        assert predictor._steps_taken == 0

    def test_n_step_td_step_adjust(self, context: Context) -> None:
        """Test adjusting steps taken on reward signal propagation."""
        predictor = TemporalDifference(step=1)
        predictor._temperature = 1.0
        predictor._steps_taken = 1
        package_tuple = ("tensorflow", "2.3.1", "https://pypi.org/simple")
        state = State()
        state.add_resolved_dependency(package_tuple)
        with predictor.assigned_context(context):
            predictor.set_reward_signal(state, package_tuple, 0.33)

        assert predictor._policy.get(package_tuple) == [0.33, 1]
        assert predictor._steps_taken == 0

    def test_n_step_td_step_no_adjust(self, context: Context) -> None:
        """Test adjusting steps taken on reward signal propagation."""
        predictor = TemporalDifference(step=1)
        predictor._temperature = 1.0
        predictor._steps_taken = 0
        package_tuple = ("tensorflow", "2.3.1", "https://pypi.org/simple")
        state = State()
        state.add_resolved_dependency(package_tuple)
        with predictor.assigned_context(context):
            predictor.set_reward_signal(state, package_tuple, 0.33)

        assert predictor._policy.get(package_tuple) is None

        predictor._steps_taken = 1

        with predictor.assigned_context(context):
            predictor.set_reward_signal(state, package_tuple, 0.2)

        assert predictor._policy.get(package_tuple) == [0.53, 1]
        assert predictor._steps_taken == 0
