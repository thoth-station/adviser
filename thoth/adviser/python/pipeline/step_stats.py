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

import logging
from typing import Tuple

import attr
from .stats_base import StatsBase

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class StepStats(StatsBase):
    """Statistics accumulated for steps in pipeline."""

    _packages_removed_count = attr.ib(type=dict, default=attr.Factory(dict))

    def log_report(self) -> None:
        """Log report for a pipeline step."""
        total = 0.0
        for step_name, step_duration in self._units_run.items():
            _LOGGER.debug("    Step %r took %.5f seconds", step_name, step_duration)
            if len(self._packages_removed_count.get(step_name, set())) > 0:
                _LOGGER.debug(
                    "     -> number of packages removed from dependency graph: %d",
                    len(self._packages_removed_count[step_name]),
                )
            total += step_duration

        _LOGGER.debug("Steps took %.5f seconds in total", total)

    def mark_removed_package_tuple(self, package_tuple: Tuple[str, str, str]):
        """Keep track of packages removed in a step run for statistics."""
        if self._current_name not in self._packages_removed_count:
            self._packages_removed_count[self._current_name] = set()

        self._packages_removed_count[self._current_name].add(package_tuple)
