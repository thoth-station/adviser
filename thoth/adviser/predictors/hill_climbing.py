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

"""Implementation of hill climbing in the state space."""

import logging

import attr
from typing import List
from typing import Tuple

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from ..predictor import Predictor
from ..state import State
from ..exceptions import NoHistoryKept


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class HillClimbing(Predictor):
    """Implementation of hill climbing in the state space."""

    _history = attr.ib(type=List[Tuple[float, int]], default=attr.Factory(list), init=False)

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Get top state from the beam for the next resolution round."""
        state = self.context.beam.max()

        if self.keep_history:
            self._history.append((state.score, self.context.accepted_final_states_count))

        return state, state.get_first_unresolved_dependency()

    def pre_run(self) -> None:
        """Initialize before the actual hill climbing run."""
        self._history = []

    def plot(self) -> matplotlib.figure.Figure:
        """Plot score of the highest rated stack during hill climbing."""
        if not self._history:
            raise NoHistoryKept("No history datapoints kept")

        x = [i for i in range(len(self._history))]
        y1 = [i[0] for i in self._history]
        y2 = [i[1] for i in self._history]

        fig, host = plt.subplots()
        fig.subplots_adjust(right=0.75)

        par1 = host.twinx()

        par1.spines["right"].set_position(("axes", 1.10))
        self._make_patch_spines_invisible(par1)

        par1.spines["right"].set_visible(True)
        host.spines["right"].set_visible(False)
        host.spines["top"].set_visible(False)

        (p1,) = host.plot(x, y1, ",g", label="Score of the expanded state")
        (p2,) = par1.plot(x, y2, ",y", label="Number of products conducted")

        host.set_xlabel("iteration")
        host.set_ylabel("score")
        par1.set_ylabel("product count")

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
