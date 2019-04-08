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

"""Context passed into stride in stack generation pipeline."""

from typing import List
from typing import Tuple

import attr

from .context_base import ContextBase
from .stride_stats import StrideStats


@attr.s(slots=True)
class StrideContext(ContextBase):
    """A context carried during stride scoring and checking."""

    stack_candidate = attr.ib(type=List[Tuple[str, str, str]])
    _score = attr.ib(type=float, default=0.0)
    _justification = attr.ib(type=list, default=attr.Factory(list))
    _stats = attr.ib(type=StrideStats, default=attr.Factory(StrideStats))

    @property
    def score(self) -> float:
        """Get score of stack candidate."""
        return self._score

    @property
    def justification(self) -> List[dict]:
        """Retrieve a list of justifications."""
        return self._justification

    def adjust_score(self, score: float, justification: List[dict] = None) -> None:
        """Adjust score for the given stack candidate, modify justification reported to end user."""
        self._score += score
        if justification:
            self._justification.extend(justification)
