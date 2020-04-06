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
from typing import Optional
from typing import Tuple
from typing import Set

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
    _packages_heated_up = attr.ib(type=Set[str], factory=set)
    _initial_state = attr.ib(type=Optional[State], default=None)
    _latest_versions_heat_up = attr.ib(type=set, factory=set)

    def set_reward_signal(
        self, state: State, package_tuple: Tuple[str, str, str], reward: float
    ) -> None:
        """Set hop to True if we did not get resolve any stack with latest."""
        super().set_reward_signal(state, package_tuple, reward)

        if math.isnan(reward):
            self._hop = True
            if not self._hop_logged:
                _LOGGER.warning(
                    "The latest stack couldn't be resolved, performing hops across package versions"
                )
                self._hop_logged = True

        if math.isinf(reward):
            self._hop = False

    def pre_run(self) -> None:
        """Initialize local variables before each predictor run per resolver."""
        super().pre_run()
        self._hop = False
        self._hop_logged = False
        self._initial_state = None
        self._packages_heated_up.clear()

    def _heat_up(self) -> Optional[Tuple[State, Tuple[str, str, str]]]:
        """Start heating up phase for the predictor.

        This phase generates new states out of the initial state so that the predictor is not stuck
        in states generated out of the very first state and very first dependency.
        """
        if not self._packages_heated_up:
            assert self.context.beam.size == 1
            self._initial_state = self.context.beam.get(0)

        # Keeping the initial state as an attribute in this predictor and this
        # check is an optimization thanks to the logic behind resolver's state
        # manipulation - it reuses the initial state for generating new states
        # (see memory optimization) - if the initial state starts to have
        # resolved dependencies, it means there are no more unresolved
        # dependencies to be tracked or the newly cloned state out of the
        # initial state would be the same as the initial state.
        if self._initial_state.resolved_dependencies:
            # End the heat up phase.
            self._initial_state = None
            return None

        for unresolved_dependency in self._initial_state.unresolved_dependencies:
            if unresolved_dependency in self._packages_heated_up:
                continue

            self._packages_heated_up.add(unresolved_dependency)
            unresolved_dependency_tuple = next(
                iter(
                    self._initial_state.unresolved_dependencies[
                        unresolved_dependency
                    ].values()
                )
            )

            if self.keep_history:
                self._history.append(
                    (
                        self._initial_state.score,
                        self.context.accepted_final_states_count,
                    )
                )

            return self._initial_state, unresolved_dependency_tuple

        self._initial_state = None
        return None

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Get last state expanded and expand first unresolved dependency."""
        if not self._packages_heated_up or self._initial_state:
            heat_up_result = self._heat_up()
            if heat_up_result is not None:
                return heat_up_result

        state = self.context.beam.get_last()

        if state is None:
            state = self.context.beam.get_random()

        if self.keep_history:
            self._history.append(
                (state.score, self.context.accepted_final_states_count)
            )

        if self._hop:
            return state, state.get_random_unresolved_dependency(prefer_recent=True)

        return state, state.get_first_unresolved_dependency()
