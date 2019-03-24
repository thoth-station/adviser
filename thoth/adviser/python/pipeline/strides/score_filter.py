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

"""Filter out stacks which have same score.

This stride is used to filter out duplicate stacks - stacks which have same score,
but differ only in a package which does not affect the overall score in any way. As
we preserve order of versions based on semver, we accept the very first stack and
the subsequent ones are checked against score which was given to the accepted stack.
If score does not differ it means stacks differ in a package which did not differentiate
stack scores. The first accepted has newer packages (as we respect semver ordering),
the latter ones have older packages. The heuristic is to provide as latest stack as possible.
"""

import logging
from ..stride_context import StrideContext

import attr

from ..stride import Stride
from ..exceptions import StrideRemoveStack

_LOGGER = logging.getLogger(__name__)


class ScoreFiltering(Stride):
    """Filtering of stacks which encountered runtime errors."""

    _previous_stack_score = attr.ib(type=float, default=None)

    def run(self, stride_context: StrideContext) -> None:
        """Filter out packages which have runtime errors."""
        # We also accept 0 values (no performance info).
        if (
            self._previous_stack_score is None
            or self._previous_stack_score != stride_context.score
        ):
            # Accept this stack and continue with a next one.
            self._previous_stack_score = stride_context.score
            return

        raise StrideRemoveStack(
            f"Stack has same score as already accepted one: {self._previous_stack_score}"
        )
