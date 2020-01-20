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

"""Implementation of predictor used for resolving latest stacks in the state space."""

import logging
import math

import attr
from typing import Tuple

from .hill_climbing import HillClimbing
from ..state import State


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class ApproximatingLatest(HillClimbing):
    """Implementation of predictor used for resolving latest stacks in the state space.

    This predictor approximates resolution to the latest software stack. The resolution to the latest is
    approximated using continuous resolution with an optional randomness not to get stuck in a "trap"
    if resolution to all latest cannot be satisfied.
    """

    _hop = attr.ib(type=bool, default=False)
    _hop_logged = attr.ib(type=bool, default=False)

    def set_reward_signal(self, state: State, package_tuple: Tuple[str, str, str], reward: float) -> None:
        """Set hop to True if we did not get resolve any stack with latest."""
        super().set_reward_signal(state, package_tuple, reward)

        if math.isnan(reward):
            self._hop = True
            if not self._hop_logged:
                _LOGGER.warning("The latest stack couldn't be resolved, performing hops across package versions")
                self._hop_logged = True

        if math.isinf(reward):
            self._hop = False

    def pre_run(self) -> None:
        """Initialize local variables before each predictor run per resolver."""
        super().pre_run()
        self._hop = False
        self._hop_logged = False

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Get last state expanded and expand first unresolved dependency."""
        state = self.context.beam.get_last()

        if state is None:
            state = self.context.beam.get_random()

        if self.keep_history:
            self._history.append((state.score, self.context.accepted_final_states_count))

        if self._hop:
            return state, state.get_random_unresolved_dependency(prefer_recent=True)

        return state, state.get_first_unresolved_dependency()
