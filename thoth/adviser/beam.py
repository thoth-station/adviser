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
import heapq
from typing import Any
from typing import List
from typing import Tuple
from typing import Generator
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

    The implementation of beam respecting beam width:

      https://en.wikipedia.org/wiki/Beam_search

    Beam is internally implemented on top of heap queue to optimize inserts and respect beam width in O(log(N)).
    """

    width = attr.ib(default=None, type=Optional[int])
    _states = attr.ib(
        default=attr.Factory(list), type=List[Tuple[Tuple[float, int], State]]
    )
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

        Used to keep track of beam history.
        """
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
        host.tick_params(axis="y", colors="black", **tkw)
        host.tick_params(axis="x", **tkw)
        par1.tick_params(axis="y", colors=p2.get_color(), **tkw)

        font_prop = FontProperties()
        font_prop.set_size("small")
        fig.legend(
            loc="upper center",
            bbox_to_anchor=(0.50, 1.00),
            ncol=2,
            fancybox=True,
            shadow=True,
            prop=font_prop,
        )
        host.yaxis.label.set_color("black")

        if output_file:
            parts = output_file.rsplit(".", maxsplit=1)
            if len(parts) != 2:
                raise ValueError(
                    f"Cannot determine plot format: no extension parsed from {output_file!r}"
                )

            _LOGGER.debug("Saving figure to %r (format: %r)", output_file, parts[-1])
            fig.savefig(f"{parts[0]}_beam.{parts[1]}", format=parts[-1])

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
            self._top_idx = len(self._states) // 2
            for idx, _ in enumerate(self._states[self._top_idx + 1 :]):
                if self._states[self._top_idx][0] < self._states[idx][0]:
                    self._top_idx = idx

        return self._top_idx

    def add_state(self, state: State) -> None:
        """Add state to the internal state listing (do it in O(log(N)) time."""
        item = ((state.score, self._counter), state)

        if self.width is not None and len(self._states) >= self.width:
            heapq.heappushpop(self._states, item)
        else:
            heapq.heappush(self._states, item)

        self._top_idx = None
        self._counter -= 1

    def get(self, idx: int) -> State:
        """Get i-th element from the beam (constant time), keep it in the beam."""
        return self._states[idx][1]

    def pop(self, idx: Optional[int] = None) -> State:
        """Pop i-th element from the beam and remove it from the beam (this is actually toppop).

        If index is not provided, pop one of the largest elements kept in the beam.

        If top_state is pre-cached, this operation is done in O(log(N)), O(N) otherwise.
        """
        if idx is None:
            idx = self.get_top_idx()

        # Do this operation in O(logN) on top of the internal heap queue:
        #   https://stackoverflow.com/questions/10162679/python-delete-element-from-heap
        to_return = self._states[idx]
        self._states[idx] = self._states[-1]
        self._states.pop()
        if idx < len(self._states):
            heapq._siftup(self._states, idx)  # type: ignore
            heapq._siftdown(self._states, 0, idx)  # type: ignore

        self._top_idx = None
        return to_return[1]
