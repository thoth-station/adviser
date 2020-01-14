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

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Get last state expanded and expand first unresolved dependency."""
        state = self.context.beam.get_last()

        if state is None:
            state = self.context.beam.get_random()

        if self.keep_history:
            self._history.append((state.score, self.context.accepted_final_states_count))

        return state, state.get_random_unresolved_dependency(prefer_recent=True)
