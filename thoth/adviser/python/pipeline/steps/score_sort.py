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

"""Sort paths in dependency graph based on their scores."""

import logging
from typing import Tuple
from typing import List
from functools import partial

from thoth.python import PackageVersion

from ..step import Step
from ..step_context import StepContext

_LOGGER = logging.getLogger(__name__)


class ScoreSort(Step):
    """Sort paths based on their scores.

    This step should be run as a last step before the actual
    resolution. This way the resolution algorithm will generate
    high scored stacks sooner.
    """

    @staticmethod
    def cmp_function_paths(
        path1: Tuple[float, List[Tuple[str, str, str]]],
        path2: Tuple[float, List[Tuple[str, str, str]]],
    ) -> float:
        """Comparision based on score for paths."""
        score1 = path1[0]
        score2 = path2[0]
        return score1 - score2

    @staticmethod
    def cmp_function_direct(
        step_context: StepContext,
        package_version1: PackageVersion,
        package_version2: PackageVersion,
    ) -> float:
        """Comparision based on score for direct dependencies."""
        return step_context.get_direct_dependency_score(
            package_version1.to_tuple()
        ) - step_context.get_direct_dependency_score(package_version2.to_tuple())

    def run(self, step_context: StepContext):
        """Perform sorting of paths and direct dependencies based on score."""
        step_context.sort_paths(self.cmp_function_paths)
        step_context.sort_direct_dependencies(
            partial(self.cmp_function_direct, step_context)
        )
