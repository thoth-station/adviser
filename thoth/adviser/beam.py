#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

import random
from typing import Any
from typing import List
from typing import Tuple
from typing import Generator
from typing import Optional
import logging

from fext import ExtHeapQueue
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

import attr

from .exceptions import NoHistoryKept
from .state import State
from .utils import should_keep_history

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Beam:
    """Beam implementation.

    The implementation of beam respecting beam width: https://en.wikipedia.org/wiki/Beam_search

    Beam is internally implemented on top of a min-heap queue to optimize inserts and respect
    beam width in O(log(N)).

    The most frequent operation performed on the beam is not always the same - it depends
    on the beam width and number of states generated. If number of states generated  is
    more than the width of the beam, its reasonable to optimize insertions into the beam
    with checks on beam width.

    If number of states generated is smaller than the beam width, the beam could be optimized
    for removal of states.

    As the first scenario is seen in a real-world deployment, the beam uses min-heapq to keep
    addition to the beam with beam_width checks in O(log(N)) and removals of the states in
    O(log(N)). To satisfy removals in O(log(N)), the beam maintains a dictionary mapping a state
    to its index in the beam.
    """

    width = attr.ib(default=None, type=Optional[int])
    keep_history = attr.ib(type=bool, kw_only=True, default=None, converter=should_keep_history)

    _beam_history = attr.ib(type=List[Tuple[int, Optional[float]]], default=attr.Factory(list), kw_only=True)

    _heap = attr.ib(type=ExtHeapQueue, init=False)
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

    @_heap.default
    def _heap_default(self) -> ExtHeapQueue:
        """Initialize the extended heap queue."""
        if self.width is not None:
            return ExtHeapQueue(size=self.width)

        return ExtHeapQueue()

    def new_iteration(self) -> None:  # noqa: D401
        """Called once a new iteration is done in resolver.

        Used to keep track of beam history and to keep track of states added.
        """
        if not self.keep_history:
            return

        self._beam_history.append((self.size, self.max().score if self.size > 0 else None))

    @staticmethod
    def _make_patch_spines_invisible(ax: Any) -> None:
        """Make spines invisible."""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    def plot(self) -> matplotlib.figure.Figure:
        """Plot temperature history of adaptive simulated annealing."""
        if not self._beam_history:
            raise NoHistoryKept("No history datapoints kept for beam")

        x = [i for i in range(len(self._beam_history))]
        # Beam size over time.
        y1 = [i[0] for i in self._beam_history]
        # Highest rated state history.
        y2 = [i[1] for i in self._beam_history]

        fig, host = plt.subplots()
        fig.subplots_adjust(right=0.75)

        par1 = host.twinx()

        par1.spines["right"].set_position(("axes", 1.10))
        self._make_patch_spines_invisible(par1)

        par1.spines["right"].set_visible(True)
        host.spines["right"].set_visible(False)
        host.spines["top"].set_visible(False)

        (p1,) = host.plot(x, y1, ",g", label="Beam size")
        (p2,) = par1.plot(x, y2, ",b", label="Top rated state score")

        host.set_xlabel("iteration")
        host.set_ylabel("beam size")
        par1.set_ylabel("score")

        host.yaxis.label.set_color(p1.get_color())
        par1.yaxis.label.set_color(p2.get_color())

        tkw = dict(size=4, width=1.5)
        host.tick_params(axis="y", colors=p1.get_color(), **tkw)
        host.tick_params(axis="x", **tkw)
        par1.tick_params(axis="y", colors=p2.get_color(), **tkw)

        font_prop = FontProperties()
        font_prop.set_size("medium")
        fig.legend(
            loc="upper center", bbox_to_anchor=(0.50, 1.00), ncol=2, fancybox=True, shadow=True, prop=font_prop,
        )
        return fig

    @property
    def size(self) -> int:
        """Get the current size of beam."""
        return len(self._heap)

    def wipe(self) -> None:
        """Remove all states from beam."""
        self._heap.clear()

    def iter_states(self) -> List[State]:
        """Iterate over states, do not respect their score in order of iteration."""
        to_return = self._heap.items()  # type: List[State]
        return to_return

    def iter_states_sorted(self, reverse: bool = True) -> Generator[State, None, None]:
        """Iterate over sorted states."""
        return (item for item in sorted(self._heap.items(), reverse=reverse))

    def max(self) -> State:
        """Return the highest rated state as kept in the beam."""
        to_return = self._heap.get_max()  # type: State
        return to_return

    def add_state(self, state: State) -> None:
        """Add state to the internal state listing (do it in O(log(N)) time."""
        self._heap.push(state.score, state)

    def get(self, idx: int) -> State:
        """Get i-th element from the beam (constant time), keep it in the beam.

        This method is suitable for random state indexing in the beam (like in case of adaptive
        simulated annealing). The actual index is not into a sorted array and has no special meaning
        assigned - beam under the hood uses min-heapq (as of now), but the index used is not guaranteed to
        point to a heap-like data structure.
        """
        to_return = self._heap.get(idx)  # type: State
        return to_return

    def get_last(self) -> Optional[State]:
        """Get state that was added in the previous resolution round."""
        to_return = self._heap.get_last()  # type: Optional[State]
        return to_return

    def get_random(self) -> State:
        """Get a random state from beam."""
        idx = random.randint(0, self.size - 1) if self.size > 1 else 0
        return self.get(idx)

    def remove(self, state: State) -> None:
        """Remove the given state from beam."""
        self._heap.remove(state)

    def pop(self, idx: Optional[int] = None) -> State:
        """Pop i-th element from the beam and remove it from the beam (this is actually toppop).

        If index is not provided, pop the largest item kept in the beam.
        """
        if idx is None:
            to_pop_state = self._heap.get_max()  # type: State
        else:
            to_pop_state = self._heap.get(idx)

        self._heap.remove(to_pop_state)
        return to_pop_state
