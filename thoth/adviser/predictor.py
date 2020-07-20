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

"""A base class for implementing predictor."""

import abc
import logging
from contextlib import contextmanager

import attr
from typing import Any
from typing import Tuple
from typing import Optional
from typing import Generator

import matplotlib.figure

from .context import Context
from .report import Report
from .state import State
from .utils import should_keep_history

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Predictor:
    """A base class for implementing a predictor for resolver."""

    keep_history = attr.ib(type=bool, kw_only=True, default=None, converter=should_keep_history)

    _CONTEXT: Optional[Context] = None

    @classmethod
    @contextmanager
    def assigned_context(cls, context: Context) -> Generator[None, None, None]:
        """Assign context to predictor."""
        try:
            cls._CONTEXT = context
            yield
        finally:
            cls._CONTEXT = None

    @property
    def context(self) -> Context:
        """Get context in which the unit runs in."""
        if self._CONTEXT is None:
            raise ValueError("Requesting resolver context outside of resolver run")

        return self._CONTEXT

    def pre_run(self) -> None:
        """Pre-initialize the predictor.

        This method is called before any resolving with a freshly instantiated context. The default operation is a noop,
        but predictor can perform any initial setup in this method. This method should not raise any exception.
        """
        # noop

    @abc.abstractmethod
    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Run the main method used to run the predictor."""
        raise NotImplementedError

    def post_run(self) -> None:
        """Post-run method run after the resolving has been done."""
        # noop

    def post_run_report(self, report: Report) -> None:
        """Post-run method run after the resolving has finished - this method is called only if resolving with a report.

        The default operation is a noop, but a predictor can perform any post-run operations in this method. This
        method should not raise any exception.
        """
        # noop

    def set_reward_signal(self, state: State, package_tuple: Tuple[str, str, str], reward: float) -> None:
        """Signalize the reward.

        @param state: (child) state for which the reward signal is triggered
        @param package_tuple: Python package that was added to the state causing the reward
        @param reward: set to nan if the given state was not accepted a special value
                       of inf notifies about a new final state
        """
        # noop

    def finalize_state(self, state_id: int) -> None:  # noqa: D401
        """Finalizer called when the given state is about to be destructed by garbage collector.

        Method suitable if predictor keeps internal state for states. Note that this method is not
        called for remaining states if the resolver terminates.

        @param state_id: id of state that is about to be finalized
        """
        # noop

    def plot(self) -> matplotlib.figure.Figure:
        """Plot information about predictor."""
        _LOGGER.error(
            "Cannot plot predictor history as plotting is not implemented for predictor %r, error is not fatal",
            self.__class__.__name__,
        )

    @staticmethod
    def _make_patch_spines_invisible(ax: Any) -> None:
        """Make spines invisible."""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
