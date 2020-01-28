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

"""Implementation of Temporal Difference (TD) based predictor with adaptive simulated annealing schedule."""

import logging
import random
import math

import attr
from typing import Tuple
from typing import Optional
from typing import Dict

from ..state import State
from .td import TemporalDifference


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class MCTS(TemporalDifference):
    """Implementation of Monte-Carlo Tree Search (MCTS) based predictor with adaptive simulated annealing schedule."""

    _next_state = attr.ib(type=Optional[State], default=None)

    def pre_run(self) -> None:
        """Initialize pre-running of this predictor."""
        self._next_state = None
        super().pre_run()

    def set_reward_signal(self, state: State, _: Tuple[str, str, str], reward: float) -> None:
        """Note down reward signal of the last action performed."""
        if math.isnan(reward):
            # Invalid state reached, continue with another one next round.
            self._next_state = None
        elif not math.isinf(reward):
            # The state for which we obtained reward is next state, continue with it in the next round.
            self._next_state = state
            return None

        # We have reached a final/terminal state - mark down policy we used and accumulated reward.
        total_reward = state.score
        for package_tuple in state.iter_resolved_dependencies():
            package_tuple_hash = hash(package_tuple)
            old = self._actions.get(package_tuple_hash)
            if old is None:
                old = (0.0, 0)

            self._actions[package_tuple_hash] = (old[0] + total_reward, old[1] + 1)

        # We have reached a new final - get another next time.
        self._next_state = None

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Run MCTS with adaptive simulated annealing schedule."""
        if self._next_state is not None:
            return self._next_state, self._next_state.get_random_unresolved_dependency(prefer_recent=True)

        self._temperature = self._temperature_function(self._temperature, self.context)

        # Expand highest promising by default.
        state = self.context.beam.top()

        # Pick a random state to be expanded if accepted.
        probable_state_idx = random.randrange(1, self.context.beam.size) if self.context.beam.size > 1 else 0
        probable_state = self.context.beam.get(probable_state_idx)
        acceptance_probability = self._compute_acceptance_probability(
            state.score, probable_state.score, self._temperature
        )

        if probable_state_idx != 0 and acceptance_probability >= random.random():
            state, unresolved_dependency_tuple = self._do_exploration()
        else:
            state, unresolved_dependency_tuple = self._do_exploitation()

        if self.keep_history:
            self._temperature_history.append(
                (
                    self._temperature,
                    state is self.context.beam.top(),
                    acceptance_probability,
                    self.context.accepted_final_states_count,
                )
            )

        return state, unresolved_dependency_tuple
