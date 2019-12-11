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

import os
from collections import OrderedDict
from typing import Any
from typing import List
from typing import Tuple
from typing import Generator
from typing import Dict
from typing import Optional
import operator
import logging

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

import attr

from .exceptions import NoHistoryKept
from .state import State

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
    _states = attr.ib(
        default=attr.Factory(list), type=List[Tuple[Tuple[float, int], State]]
    )
    # Mapping id(state) -> index in the heap to guarantee O(1) state index lookup and
    # subsequent O(log(N)) state removal from the beam.
    _states_idx = attr.ib(
        default=attr.Factory(dict), type=Dict[int, int]
    )
    # Use ordered dict to preserve order of inserted states not to introduce
    # randomness (that would be introduced using a set) across multiple runs.
    _last_added = attr.ib(
        default=attr.Factory(OrderedDict)
    )  # type: OrderedDict[int, Tuple[Tuple[float, int], State]]
    _counter = attr.ib(default=0, type=int)
    _top_idx = attr.ib(default=None, type=Optional[int])
    _beam_history = attr.ib(
        type=List[Tuple[int, Optional[float]]], default=attr.Factory(list), kw_only=True
    )

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

    def new_iteration(self) -> None:
        """Called once a new iteration is done in resolver.

        Used to keep track of beam history and to keep track of states added.
        """
        self._last_added = OrderedDict()

        if bool(int(os.getenv("THOTH_ADVISER_NO_HISTORY", 0))):
            return

        self._beam_history.append(
            (self.size, self.top().score if self.size > 0 else None)
        )

    @staticmethod
    def _make_patch_spines_invisible(ax: Any) -> None:
        """Make spines invisible."""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    def plot(self, output_file: Optional[str] = None) -> matplotlib.figure.Figure:
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

        p1, = host.plot(x, y1, ",g", label="Beam size")
        p2, = par1.plot(x, y2, ",b", label="Top rated state score")

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
            loc="upper center",
            bbox_to_anchor=(0.50, 1.00),
            ncol=2,
            fancybox=True,
            shadow=True,
            prop=font_prop,
        )

        if output_file:
            parts = output_file.rsplit(".", maxsplit=1)
            if len(parts) != 2:
                raise ValueError(
                    f"Cannot determine plot format: no extension parsed from {output_file!r}"
                )

            output_file = f"{parts[0]}_beam.{parts[1]}"
            _LOGGER.debug("Saving figure to %r (format: %r)", output_file, parts[-1])
            fig.savefig(output_file, format=parts[-1])

        return fig

    @property
    def size(self) -> int:
        """Get the current size of beam."""
        return len(self._states)

    def wipe(self) -> None:
        """Remove all states from beam."""
        self._states = []

    def iter_states(self) -> Generator[State, None, None]:
        """Iterate over states, do not respect their score in order of iteration."""
        return (item[1] for item in self._states)

    def iter_states_sorted(self, reverse: bool = True) -> Generator[State, None, None]:
        """Iterate over sorted states."""
        return (
            item[1]
            for item in sorted(
                self._states, key=operator.itemgetter(0), reverse=reverse
            )
        )

    def iter_new_added_states(self) -> Generator[State, None, None]:
        """Iterate over states added in the resolution round."""
        return (item[1] for item in self._last_added.values())

    def iter_new_added_states_sorted(
        self, reverse: bool = True
    ) -> Generator[State, None, None]:
        """Iterate over newly added states, sorted based on the score."""
        return (
            item[1]
            for item in sorted(
                self._last_added.values(), key=operator.itemgetter(0), reverse=reverse
            )
        )

    def top(self) -> State:
        """Return the highest rated state as kept in the beam.

        This operation is done in O(N) if top is not pre-cached, O(1) otherwise.
        """
        if len(self._states) == 0:
            raise IndexError("Beam is empty")

        idx = self.get_top_idx()
        return self._states[idx][1]

    def get_top_idx(self) -> int:
        """Get index of the highest rated state kept in the beam.

        This operation is done in O(N) time if top is not pre-cached, O(1) otherwise.
        """
        if self.size == 0:
            raise KeyError("Beam is empty")

        if self._top_idx is None:
            # Perform the operation in O(N/2) ~ O(N) time.
            self._top_idx = len(self._states) // 2
            for idx, _ in enumerate(self._states[self._top_idx + 1:]):
                if self._states[self._top_idx][0] < self._states[idx][0]:
                    self._top_idx = idx

        return self._top_idx

    def _heappushpop(self, item: Tuple[Tuple[float, int], State]) -> Tuple[Tuple[float, int], State]:
        """Fast version of a heappush followed by a heappop."""
        if self._states and self._states[0] < item:
            item, self._states[0] = self._states[0], item
            self._states_idx[id(self._states[0][1])] = 0
            self._states_idx.pop(id(item[1]))
            self._siftup(0)

        return item

    def _heappush(self, item: Tuple[Tuple[float, int], State]) -> None:
        """Push item onto heap, maintaining the heap invariant."""
        self._states_idx[id(item[1])] = len(self._states)
        self._states.append(item)
        self._siftdown(0, len(self._states) - 1)

    def _siftup(self, pos: int) -> None:
        """Perform sift up operation on the states heap."""
        endpos = len(self._states)
        startpos = pos
        newitem = self._states[pos]
        # Bubble up the smaller child until hitting a leaf.
        childpos = 2 * pos + 1  # leftmost child position
        while childpos < endpos:
            # Set childpos to index of smaller child.
            rightpos = childpos + 1
            if rightpos < endpos and not self._states[childpos] < self._states[rightpos]:
                childpos = rightpos
            # Move the smaller child up.
            self._states[pos] = self._states[childpos]
            self._states_idx[(id(self._states[pos][1]))] = pos
            pos = childpos
            childpos = 2 * pos + 1
        # The leaf at pos is empty now.  Put newitem there, and bubble it up
        # to its final resting place (by sifting its parents down).
        self._states[pos] = newitem
        self._states_idx[id(newitem[1])] = pos
        self._siftdown(startpos, pos)

    def _siftdown(self, startpos: int, pos: int) -> None:
        """Perform sift-down operation on the states heap."""
        newitem = self._states[pos]
        # Follow the path to the root, moving parents down until finding a place
        # newitem fits.
        while pos > startpos:
            parentpos = (pos - 1) >> 1
            parent = self._states[parentpos]
            if newitem < parent:
                self._states[pos] = parent
                self._states_idx[id(parent[1])] = pos
                pos = parentpos
                continue
            break

        self._states[pos] = newitem
        self._states_idx[id(self._states[pos][1])] = pos

    def add_state(self, state: State) -> None:
        """Add state to the internal state listing (do it in O(log(N)) time."""
        item = ((state.score, self._counter), state)

        if self.width is not None and len(self._states) >= self.width:
            popped = self._heappushpop(item)
            self._last_added.pop(id(popped), None)
            if popped is not item:
                self._last_added[id(item)] = item
        else:
            self._heappush(item)
            self._last_added[id(item)] = item

        self._top_idx = None
        self._counter -= 1

    def get(self, idx: int) -> State:
        """Get i-th element from the beam (constant time), keep it in the beam.

        This method is suitable for random state indexing in the beam (like in case of adaptive
        simulated annealing). The actual index is not into a sorted array and has no special meaning
        assigned - beam under the hood uses min-heapq (as of now), but the index used is not guaranteed to
        point to a heap-like data structure.
        """
        return self._states[idx][1]

    def remove(self, state: State) -> None:
        """Remove the given state from beam."""
        idx = self._states_idx.get(id(state))
        if idx is None:
            raise KeyError("The state requested for removal was not found in the beam")

        self.pop(idx)

    def pop(self, idx: Optional[int] = None) -> State:
        """Pop i-th element from the beam and remove it from the beam (this is actually toppop).

        If index is not provided, pop one of the largest elements kept in the beam.

        If top_state is pre-cached or idx is explicitly set, this operation is done in O(log(N)), O(N) otherwise.
        """
        if idx is None:
            idx = self.get_top_idx()

        # Do this operation in O(log(N)) on top of the internal heap queue:
        #   https://stackoverflow.com/questions/10162679/python-delete-element-from-heap
        to_return = self._states[idx]
        self._states[idx] = self._states[-1]
        self._states.pop()
        if idx < len(self._states):
            self._siftup(idx)
            self._siftdown(0, idx)

        self._top_idx = None
        self._last_added.pop(to_return[0], None)  # type: ignore
        return to_return[1]
