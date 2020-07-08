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

"""Test implementation of Monte-Carlo Tree Search (MCTS) based predictor with annealing schedule."""

import math

import flexmock
import pytest

from thoth.adviser.context import Context
from thoth.adviser.predictors import MCTS
from thoth.adviser.predictors import TemporalDifference
import thoth.adviser.predictors.mcts as mcts_module

from ..base import AdviserTestCase


class TestMCTS(AdviserTestCase):
    """Test implementation of MCTS based predictor with annealing schedule."""

    def test_init(self) -> None:
        """Test the initialization part."""
        predictor = MCTS()
        assert predictor._policy == {}
        assert predictor._temperature_history == []
        assert predictor._temperature == 0.0
        assert predictor._next_state is None

    def test_pre_run(self) -> None:
        """Test calling pre-run for the initialization part."""
        flexmock(TemporalDifference)
        TemporalDifference.should_receive("pre_run").once()

        state = flexmock()
        predictor = MCTS()
        assert predictor._next_state is None
        predictor._next_state = state
        predictor.pre_run()
        assert predictor._next_state is None

    def test_set_reward_signal_nan(self) -> None:
        """Test the reward signal if no new state was generated."""
        predictor = MCTS()

        state = flexmock()

        assert predictor._policy == {}
        predictor._next_state = flexmock()
        predictor.set_reward_signal(state, ("numpy", "2.0.0", "https://pypi.org/simple"), math.nan)
        assert predictor._next_state is None
        assert predictor._policy == {}

    def test_set_reward_signal(self) -> None:
        """Test the reward signal if no new state was generated."""
        predictor = MCTS()

        state = flexmock()

        assert predictor._policy == {}
        predictor._next_state = flexmock()

        predictor.set_reward_signal(state, ("numpy", "2.0.0", "https://pypi.org/simple"), 7355608.0)
        assert predictor._next_state is state
        assert predictor._policy == {}

    def test_set_reward_signal_inf(self) -> None:
        """Test the reward signal if a final state was generated."""
        predictor = MCTS()

        state = flexmock(score=3.1)
        state.should_receive("iter_resolved_dependencies").and_return(
            [
                ("numpy", "2.0.0", "https://pypi.org/simple"),
                ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
            ]
        )
        # numpy was already seen, tensorflow was not seen yet
        predictor._policy = {
            ("numpy", "2.0.0", "https://pypi.org/simple"): [2.3, 100],
        }
        predictor._next_state = flexmock()
        predictor.set_reward_signal(state, ("numpy", "2.0.0", "https://pypi.org/simple"), math.inf)
        assert predictor._next_state is None
        assert predictor._policy == {
            ("numpy", "2.0.0", "https://pypi.org/simple"): [2.3 + 3.1, 101],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [3.1, 1],
        }

    @pytest.mark.parametrize("next_state", [None, flexmock()])
    def test_run_heat_up(self, context: Context, next_state) -> None:
        """Test running the predictor in the "heat-up" phase regardless next state being set."""
        state = flexmock()
        unresolved_dependency = ("tensorflow", "2.0.0", "https://pypi.org/simple")

        predictor = MCTS()
        predictor._next_state = None

        flexmock(TemporalDifference)
        TemporalDifference.should_receive("run").with_args().and_return(state, unresolved_dependency).once()

        context.iteration = 1  # Some small number to hit the heat-up part.
        with predictor.assigned_context(context):
            assert predictor.run() == (state, unresolved_dependency)

    def test_run_next_state(self, context: Context) -> None:
        """Test running the predictor when the next state is scheduled."""
        state = flexmock()
        unresolved_dependency = ("tensorflow", "2.0.0", "https://pypi.org/simple")
        state.should_receive("get_random_unresolved_dependency").with_args(prefer_recent=True).and_return(
            unresolved_dependency
        ).once()

        predictor = MCTS()
        predictor._next_state = state
        context.beam.should_receive("get_last").and_return(state).once()
        context.iteration = 1000000  # Some big number not to hit the heat-up part.
        with predictor.assigned_context(context):
            assert predictor.run() == (state, unresolved_dependency)

    def test_run_next_state_no_last(self, context: Context) -> None:
        """Test running the predictor when the next state is not last state added to beam."""
        state = flexmock()
        unresolved_dependency = ("tensorflow", "2.0.0", "https://pypi.org/simple")

        predictor = MCTS()
        predictor._next_state = flexmock()
        context.beam.should_receive("get_last").and_return(flexmock()).once()

        flexmock(TemporalDifference)
        TemporalDifference.should_receive("run").with_args().and_return(state, unresolved_dependency).once()

        context.iteration = 1000000  # Some big number not to hit the heat-up part.
        with predictor.assigned_context(context):
            assert predictor.run() == (state, unresolved_dependency)

    def test_run_no_next_state(self, context: Context) -> None:
        """Test running the predictor when no next state is scheduled."""
        predictor = MCTS()
        assert predictor._next_state is None

        # If no next state kept, we follow logic from the TD-learning.
        flexmock(TemporalDifference)
        state = flexmock()
        unresolved_dependency = flexmock()
        TemporalDifference.should_receive("run").with_args().and_return(state, unresolved_dependency).once()
        context.iteration = 1000000  # Some big number not to hit the heat-up part.
        with predictor.assigned_context(context):
            assert predictor.run() == (state, unresolved_dependency)

    def test_policy_size_no_shrink(self, context: Context) -> None:
        """Test limiting policy size over runs."""
        # The main difference with the similar TD test is in reward signal propagated.
        predictor = MCTS()

        predictor._policy = {
            ("numpy", "2.0.0", "https://pypi.org/simple"): [1.0, 100],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [2.0, 100],
        }

        rewarded = list(predictor._policy.keys())[0]  # numpy
        state = flexmock(score=1.0)
        state.should_receive("iter_resolved_dependencies").with_args().and_return([rewarded]).once()

        # No shrink as we are in this iteration.
        context.iteration = mcts_module._MCTS_POLICY_SIZE_CHECK_ITERATION + 1
        old_policy_size = mcts_module._MCTS_POLICY_SIZE
        with predictor.assigned_context(context):
            try:
                mcts_module._MCTS_POLICY_SIZE = 1
                predictor.set_reward_signal(state, rewarded, math.inf)
            finally:
                mcts_module._MCTS_POLICY_SIZE = old_policy_size

        assert predictor._policy == {
            ("numpy", "2.0.0", "https://pypi.org/simple"): [1.0 + state.score, 100 + 1],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [2.0, 100],
        }
        assert predictor._next_state is None

    def test_policy_size_shrink(self, context: Context) -> None:
        """Test limiting policy size over runs."""
        # The main difference with the similar TD test is in reward signal propagated.
        predictor = MCTS()

        predictor._policy = {
            ("numpy", "2.0.0", "https://pypi.org/simple"): [1.0, 100],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [3.0, 100],
        }

        rewarded = list(predictor._policy.keys())[0]  # numpy
        state = flexmock(score=0.5)
        state.should_receive("iter_resolved_dependencies").with_args().and_return([rewarded]).once()

        # No shrink as we are in this iteration.
        context.iteration = 3 * mcts_module._MCTS_POLICY_SIZE_CHECK_ITERATION
        old_policy_size = mcts_module._MCTS_POLICY_SIZE
        with predictor.assigned_context(context):
            try:
                mcts_module._MCTS_POLICY_SIZE = 1
                predictor.set_reward_signal(state, rewarded, math.inf)
            finally:
                mcts_module._MCTS_POLICY_SIZE = old_policy_size

        # the numpy entry with a value of [1.5, 101] gets removed
        assert predictor._policy == {
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [3.0, 100],
        }
        assert predictor._next_state is None
