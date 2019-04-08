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

"""Implementation of statistics for generation pipeline."""

import logging

import attr
from .stats_base import StatsBase

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class StrideStats(StatsBase):
    """Statistics accumulated for strides in pipeline."""

    def log_report(self) -> None:
        """Log report for a pipeline step."""
        total = 0.0
        for stride_name, stride_duration in self._units_run.items():
            _LOGGER.debug(
                "    Stride %r took %.5f seconds", stride_name, stride_duration
            )
            total += stride_duration

        _LOGGER.debug("Strides took %.5f seconds in total", total)
