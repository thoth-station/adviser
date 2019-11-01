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

"""Filter out stacks which have same score."""

import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

import attr

from ..stride import Stride
from ..state import State
from ..exceptions import NotAcceptable

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


class ScoreFilteringStride(Stride):
    """Filtering of stacks which encountered runtime errors."""

    _previous_stack_score = attr.ib(type=Optional[float], default=None)

    @classmethod
    def should_include(
        cls, context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Remove CVEs only for advised stacks."""
        if context.is_adviser_pipeline() and not context.is_included(cls):
            return {}

        return None

    def run(self, state: State) -> None:
        """Filter out packages which have runtime errors."""
        if (
            self._previous_stack_score is None
            or self._previous_stack_score != state.score
        ):
            # Accept this stack and continue with a next one.
            _LOGGER.debug("Assigning new score %r", state.score)
            self._previous_stack_score = state.score
            return

        raise NotAcceptable(
            f"Stack has same score as already accepted one: {self._previous_stack_score:g}"
        )
