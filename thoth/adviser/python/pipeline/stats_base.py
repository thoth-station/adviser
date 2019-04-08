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

"""Implementation of statistics for a stack generation pipeline and every pipeline step."""


import abc
import logging

import attr
from time import monotonic

from .unit_base import PipelineUnitBase

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class StatsBase(metaclass=abc.ABCMeta):
    """Statistics accumulated for a unit or units inside pipeline."""

    # Statistics start time.
    _start_time = attr.ib(type=float, default=attr.Factory(monotonic))
    # Start time for the current unit being executed.
    _unit_start_time = attr.ib(type=float, default=None)
    # A dictionary mapping unit name to its execution time (seconds in floats).
    _units_run = attr.ib(type=dict, default=attr.Factory(dict))
    # Name of the current unit which is being executed.
    _current_name = attr.ib(type=str, default=None)

    @property
    def start_time(self) -> float:
        """Get start time of a pipeline step."""
        return self._start_time

    def start_timer(self) -> None:
        """Start timer for time based statistics."""
        self._unit_start_time = monotonic()

    def get_duration(self) -> float:
        """Return duration of a pipeline step in seconds measured from start till call of this function."""
        now = monotonic()
        return now - self.start_time

    def reset_stats(self, unit: PipelineUnitBase) -> None:
        """Reset stats respecting the next pipeline unit to be run."""
        assert (
            unit.name not in self._units_run
        ), f"Multiple statistics for a unit of a same type run: {unit.name}"
        now = monotonic()
        self._units_run[unit.name] = now - self._unit_start_time
        self._unit_start_time = now
        self._current_name = unit.name

    @abc.abstractmethod
    def log_report(self) -> None:
        """Log report for a pipeline unit."""
