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

"""A base class for implementing predictor."""

import abc
import logging
import os

import attr
from typing import Any
from typing import Tuple

import matplotlib.figure

from .beam import Beam
from .context import Context
from .report import Report
from .state import State

_LOGGER = logging.getLogger(__name__)


def _keep_history(value: Any) -> bool:
    """Check if the predictor history should be kept.

    If not set explicitly during invocation, check environment variable to turn of history tracking.
    """
    if value is None:
        return not bool(int(os.getenv("THOTH_ADVISER_NO_HISTORY", 0)))

    if isinstance(value, bool):
        return value

    raise ValueError(
        f"Unknown keep temperature history value: {value!r} if of type {type(value)!r}"
    )


@attr.s(slots=True)
class Predictor:
    """A base class for implementing a predictor for resolver."""

    keep_history = attr.ib(
        type=bool, kw_only=True, default=None, converter=_keep_history
    )

    def pre_run(self, context: Context) -> None:
        """Pre-initialize the predictor.

        This method is called before any resolving with a freshly instantiated context. The default operation is a noop,
        but predictor can perform any initial setup in this method. This method should not raise any exception.
        """

    @abc.abstractmethod
    def run(self, context: Context, beam: Beam) -> Tuple[State, str]:
        """The main method used to run the predictor.

        The method accepts a beam of states and returns the state which should be
        used for next expansion and package name that should be resolved .The beam has to be kept untouched.
        """
        raise NotImplementedError

    def post_run(self, context: Context) -> None:
        """Post-run method run after the resolving has been done.

        The default operation is a noop, but a predictor can perform any post-run operations in this method. This
        method should not raise any exception.
        """

    def post_run_report(self, context: Context, report: Report) -> None:
        """Post-run method run after the resolving has finished - this method is called only if resolving with a report.

        The default operation is a noop, but a predictor can perform any post-run operations in this method. This
        method should not raise any exception.
        """

    def plot(self) -> matplotlib.figure.Figure:
        """Plot information about predictor."""
        _LOGGER.error(
            "Cannot plot predictor history as plotting is not implemented for predictor %r, error is not fatal",
            self.__class__.__name__
        )

    @staticmethod
    def _make_patch_spines_invisible(ax: Any) -> None:
        """Make spines invisible."""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
