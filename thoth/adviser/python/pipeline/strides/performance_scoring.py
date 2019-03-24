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

"""Score generated stacks based on performance."""

import logging

from ..stride_context import StrideContext
from ..units import get_performance
from ..stride import Stride

_LOGGER = logging.getLogger(__name__)


class PerformanceScoring(Stride):
    """Scoring of resolved stacks based on performance."""

    PARAMETERS_DEFAULT = {"performance_threshold": 0.0}

    def run(self, stride_context: StrideContext) -> None:
        """Performance based scoring of generated stacks."""
        performance_impact_packages = get_performance(
            self.graph,
            self.project,
            stride_context.stack_candidate,
            self.parameters["performance_threshold"],
        )

        score = sum(
            performance_report[0] for performance_report in performance_impact_packages
        )
        if score:
            stride_context.adjust_score(score, [{"performance_score": score}])
