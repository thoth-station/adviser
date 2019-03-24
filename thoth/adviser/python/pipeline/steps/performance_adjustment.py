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

"""Performance based scoring step."""

import logging

from ..step import Step
from ..step_context import StepContext
from ..units import get_performance

_LOGGER = logging.getLogger(__name__)


class PerformanceAdjustment(Step):
    """A step which scores paths based on performance."""

    # Keep this as class variable as we want one warning report per adviser run.
    _REPORTED_NO_ISIS_RECORD = set()
    PARAMETERS_DEFAULT = {"performance_threshold": 0.0}

    def run(self, step_context: StepContext):
        """Score paths based on score of packages which have a performance impact."""
        all_packages = [
            package_version.to_tuple()
            for package_version in step_context.iter_all_dependencies()
        ]
        performance_impact_packages = get_performance(
            self.graph,
            self.project,
            all_packages,
            self.parameters["performance_threshold"],
        )

        for score, package_tuples in performance_impact_packages:
            _LOGGER.info(
                "Prioritizing packages %r due to good performance: %f",
                package_tuples,
                score,
            )
            for package_tuple in package_tuples:
                step_context.score_package_tuple(package_tuple, score=score)
