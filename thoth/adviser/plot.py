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

"""Routines for dependency monkey and its output handling."""

from typing import Any
from typing import Optional
from typing import List
from typing import Tuple
import logging

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from .exceptions import NoHistoryKept

_LOGGER = logging.getLogger(__name__)


def _make_patch_spines_invisible(ax: Any) -> None:
    """Make spines invisible."""
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


def plot_history(
    temperature_history: Optional[List[Tuple[float, bool, float, int]]],
    output_file: Optional[str] = None,
) -> matplotlib.figure.Figure:
    """Plot temperature history during annealing."""
    # Code adjusted based on:
    #    https://matplotlib.org/3.1.1/gallery/ticks_and_spines/multiple_yaxis_with_spines.html

    if temperature_history is None:
        raise NoHistoryKept("No history datapoints kept")

    x = [i for i in range(len(temperature_history))]
    # Top rated candidate was chosen.
    y1 = [i[0] if i[1] is True else None for i in temperature_history]
    # A neighbour candidate was chosen.
    y2 = [i[0] if i[1] is False else None for i in temperature_history]
    # Acceptance probability - as the probability in 0 - 1, lets make it larger - scale to temperature size.
    y3 = [i[2] for i in temperature_history]
    # Number of products.
    y4 = [i[3] for i in temperature_history]

    fig, host = plt.subplots()
    fig.subplots_adjust(right=0.75)

    par1 = host.twinx()
    par2 = host.twinx()

    # Offset the right spine of par1 and par2. The ticks and label have already been
    # placed on the right by twinx above.
    par1.spines["right"].set_position(("axes", 1.050))
    par2.spines["right"].set_position(("axes", 1.225))

    # Having been created by twinx, par1 par2 have their frame off, so the line of its
    # detached spine is invisible. First, activate the frame but make the patch
    # and spines invisible.
    _make_patch_spines_invisible(par1)
    _make_patch_spines_invisible(par2)

    # Second, show the right spine.
    par1.spines["right"].set_visible(True)
    par2.spines["right"].set_visible(True)
    host.spines["right"].set_visible(False)
    host.spines["top"].set_visible(False)

    p1, = host.plot(x, y1, ".g", label="Expansion of a highest rated candidate")
    host.plot(x, y2, ",r", label="Expansion of a neighbour candidate")
    p3, = par1.plot(
        x, y3, ",b", label="Acceptance probability for a neighbour candidate"
    )
    p4, = par2.plot(x, y4, ",y", label="Number of products produced in the pipeline")

    host.set_xlabel("iteration")
    host.set_ylabel("temperature")
    par1.set_ylabel("acceptance probability")
    par2.set_ylabel("product count")

    host.yaxis.label.set_color(p1.get_color())
    par1.yaxis.label.set_color(p3.get_color())
    par2.yaxis.label.set_color(p4.get_color())

    tkw = dict(size=4, width=1.5)
    host.tick_params(axis="y", colors="black", **tkw)
    par1.tick_params(axis="y", colors=p3.get_color(), **tkw)
    par2.tick_params(axis="y", colors=p4.get_color(), **tkw)
    host.tick_params(axis="x", **tkw)

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
        fig.savefig(output_file, format=parts[-1])

    return fig
