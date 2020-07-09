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

"""Implementation of Monte-Carlo Tree Search (MCTS) based predictor with adaptive simulated annealing schedule."""

import attr

from typing import Optional
from typing import Tuple
import logging
import math
import operator
import os

from ..context import Context
from ..state import State
from .td import TemporalDifference


_LOGGER = logging.getLogger(__name__)
# 0 means unlimited memory for policy learning.
_MCTS_POLICY_SIZE = int(os.getenv("THOTH_MCTS_POLICY_SIZE", 0))
# Percentage relative to `limit` for the heat-up part.
_MCTS_HEAT_UP = int(os.getenv("THOTH_MCTS_HEAT_UP", 10))
_MCTS_POLICY_SIZE_CHECK_ITERATION = 1024


@attr.s(slots=True)
class MCTS(TemporalDifference):
    """Implementation of Monte-Carlo Tree Search (MCTS) based predictor with adaptive simulated annealing schedule."""

    _next_state = attr.ib(type=Optional[State], default=None, init=False)

    def pre_run(self) -> None:
        """Initialize pre-running of this predictor."""
        self._next_state = None
        super().pre_run()

    def _temperature_function(self, t0: float, context: Context) -> float:
        """Temperature function used to compute new temperature."""
        # This function, in comparision to TD/SA, does not need to take into account iteration as it
        # works on accepted states.
        k = context.accepted_final_states_count / context.limit
        temperature = t0 * 0.99 ** k
        _LOGGER.debug(
            "New temperature for (iteration=%d, t0=%g, accepted final states=%d, limit=%d, beam size= %d, k=%f) = %g",
            context.iteration,
            t0,
            context.accepted_final_states_count,
            context.limit,
            context.beam.size,
            k,
            temperature,
        )
        return max(temperature, 0.0)

    def set_reward_signal(self, state: State, _: Tuple[str, str, str], reward: float) -> None:
        """Note down reward signal of the last action performed."""
        if math.isnan(reward):
            # Invalid state reached, continue with another one in the next round.
            self._next_state = None
            return
        elif not math.isinf(reward):
            # The state for which we obtained reward is next state, continue with it in the next round.
            self._next_state = state
            return

        # We have reached a final/terminal state - mark down policy we used and accumulated reward.
        total_reward = state.score
        for package_tuple in state.iter_resolved_dependencies():
            record = self._policy.setdefault(package_tuple, [0.0, 0])
            record[0] += total_reward
            record[1] += 1

        # We have reached a new final - get another next time.
        self._next_state = None

        # We limit number of records stored from time to time. Using sorting in O(N*log(N)) from
        # time to time appears to be much faster than keeping a min-heap queue with O(log(N)) overhead.
        if _MCTS_POLICY_SIZE and self.context.iteration % _MCTS_POLICY_SIZE_CHECK_ITERATION == 0:
            _LOGGER.warning("Shrinking learnt policy to %d entries", _MCTS_POLICY_SIZE)
            self._policy = dict(
                sorted(self._policy.items(), key=operator.itemgetter(1), reverse=True)[:_MCTS_POLICY_SIZE]
            )

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Run MCTS with adaptive simulated annealing schedule."""
        # In a heat up part, we run TD-like learning on the first candidates, not to get stuck in one state
        # that generates its children.
        if self.context.iteration < self.context.limit // _MCTS_HEAT_UP:
            return super().run()

        # As beam can be limited to width, it can happen that the last stack is pushed away (based on the score)
        # from the beam. To avoid expanding state that is not present in the beam, check that the last added state
        # in the beam is the one we keep as next expanded. If they do not match, the last added is not the next state
        # we wanted to expand - this is based on the MCTS logic.
        if self._next_state is not None and self._next_state is self.context.beam.get_last():
            return (
                self._next_state,
                self._next_state.get_random_unresolved_dependency(prefer_recent=True),
            )

        return super().run()
