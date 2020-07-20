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

from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
import logging
import math
import operator
import os
import random

import attr

from .annealing import AdaptiveSimulatedAnnealing
from ..state import State


_LOGGER = logging.getLogger(__name__)
# 0 means unlimited memory for policy learning.
_TD_POLICY_SIZE = int(os.getenv("THOTH_TD_POLICY_SIZE", 0))
# How often the policy should be checked for shrinking.
_TD_POLICY_SIZE_CHECK_ITERATION = 1024


@attr.s(slots=True)
class TemporalDifference(AdaptiveSimulatedAnnealing):
    """Implementation of Temporal Difference (TD) based predictor with adaptive simulated annealing schedule."""

    _policy = attr.ib(type=Dict[Tuple[str, str, str], List[Union[float, int]]], factory=dict, init=False)

    def pre_run(self) -> None:
        """Initialize pre-running of this predictor."""
        super().pre_run()
        self._policy.clear()
        self._temperature = float(self.context.limit)

    def set_reward_signal(self, state: State, _: Tuple[str, str, str], reward: float) -> None:
        """Note down reward signal of the last action performed."""
        if math.isnan(reward) or math.isinf(reward):
            # Do not take into account final states or states not leading to correct resolution.
            return

        for package_tuple in state.iter_resolved_dependencies():
            record = self._policy.setdefault(package_tuple, [0.0, 0])
            record[0] += reward
            record[1] += 1

        # We limit number of records stored from time to time. Using sorting in O(N*log(N)) from
        # time to time appears to be much faster than keeping a min-heap queue with O(log(N)) overhead.
        if _TD_POLICY_SIZE and self.context.iteration % _TD_POLICY_SIZE_CHECK_ITERATION == 0:
            _LOGGER.debug("Shrinking learnt policy to %d entries", _TD_POLICY_SIZE)
            self._policy = dict(
                sorted(self._policy.items(), key=operator.itemgetter(1), reverse=True)[:_TD_POLICY_SIZE]
            )

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Run Temporal Difference (TD) with adaptive simulated annealing schedule."""
        self._temperature = self._temperature_function(self._temperature, self.context)

        # Expand highest promising by default.
        max_state = self.context.beam.max()

        # Pick a random state to be expanded if accepted.
        probable_state_idx = random.randrange(1, self.context.beam.size) if self.context.beam.size > 1 else 0
        probable_state = self.context.beam.get(probable_state_idx)
        acceptance_probability = self._compute_acceptance_probability(
            max_state.score, probable_state.score, self._temperature
        )

        if acceptance_probability >= random.random():
            # Perform exploration.
            state = probable_state
            unresolved_dependency_tuple = state.get_random_unresolved_dependency(prefer_recent=True)
        else:
            state = max_state
            unresolved_dependency_tuple = self._do_exploitation(max_state)

        if self.keep_history:
            self._temperature_history.append(
                (
                    self._temperature,
                    state is self.context.beam.max(),
                    acceptance_probability,
                    self.context.accepted_final_states_count,
                )
            )

        return state, unresolved_dependency_tuple

    def _do_exploitation(self, state: State) -> Tuple[str, str, str]:
        """Perform expansion of a highest rated stack with action that should yield highest reward."""
        to_resolve_average = None
        to_resolve_package_tuple = None
        for package_tuple in state.iter_unresolved_dependencies():
            reward_records = self._policy.get(package_tuple)
            if reward_records is None:
                continue

            # Compute average - we want to be skewed based on the reward signal
            # we aggregate (so for example median of medians is not that suitable).
            average = reward_records[0] / reward_records[1]
            if to_resolve_average is None or to_resolve_average < average:
                to_resolve_average = average
                to_resolve_package_tuple = package_tuple

        # Make sure we found a candidate based on rewards marked. If not, pick a random one.
        return to_resolve_package_tuple or state.get_random_unresolved_dependency(prefer_recent=True)
