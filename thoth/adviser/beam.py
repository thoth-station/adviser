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

"""Implementation of Beam for beam searching part of adviser."""

import heapq
from typing import Any
from typing import List
from typing import Optional

import attr

from .state import State


@attr.s(slots=True)
class Beam:
    """Beam implementation.

    The implementation of beam respecting beam width:

      https://en.wikipedia.org/wiki/Beam_search

    Beam is internally implemented on top of heap queue to optimize inserts and respect beam width in O(log(N)).
    """

    width = attr.ib(default=None, type=Optional[int])
    _states = attr.ib(default=attr.Factory(list), type=List[State])

    _WIDTH_VALIDATOR_ERR_MSG = "Beam width has to be None or positive integer, got {!r}"

    @width.validator
    def _validate_width(self, attribute: Any, value: Optional[int]) -> None:
        """Validate width initialization."""
        assert attribute.name == "width", "Wrong attribute to validate"

        if value is None:
            return

        if isinstance(value, int):
            if value <= 0:
                raise ValueError(self._WIDTH_VALIDATOR_ERR_MSG.format(value))

            return

        raise ValueError(self._WIDTH_VALIDATOR_ERR_MSG.format(value))

    @property
    def states(self) -> List[State]:
        """Return a list of candidates stored in the beam."""
        return sorted(self._states, reverse=True)

    @property
    def size(self) -> int:
        """Get the current size of beam."""
        return len(self._states)

    def wipe(self) -> None:
        """Remove all states from beam."""
        self._states = []

    def iter_states(self) -> List[State]:
        """Iterate over states, do not respect their score in order of iteration."""
        return self._states

    def top(self) -> State:
        """Return the highest rated state as kept in the beam."""
        return self._states[-1]

    def add_state(self, state: State) -> None:
        """Add candidate to the internal candidates listing."""
        if self.width is not None and len(self._states) >= self.width:
            heapq.heappushpop(self._states, state)
        else:
            heapq.heappush(self._states, state)

    def get(self, idx: int) -> State:
        """Get i-th element from the beam, keep it in the beam."""
        return self._states[idx]

    def pop(self, idx: Optional[int] = None) -> State:
        """Pop i-th element from the beam and remove it from the beam (this is actually toppop).

        If index is not provided, pop largest element kept in the beam.
        """
        # Do this operation in O(logN) on top of the internal heap queue:
        #   https://stackoverflow.com/questions/10162679/python-delete-element-from-heap
        if idx is None:
            idx = len(self._states) - 1

        to_return = self._states[idx]
        self._states[idx] = self._states[-1]
        self._states.pop()
        if idx < len(self._states):
            heapq._siftup(self._states, idx)  # type: ignore
            heapq._siftdown(self._states, 0, idx)  # type: ignore

        return to_return
