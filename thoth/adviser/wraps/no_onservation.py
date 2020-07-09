#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""A wrap that notifies about missing observations."""

from typing import TYPE_CHECKING
from typing import Optional, Dict, Any

from ..state import State
from ..wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


class NoObservationWrap(Wrap):
    """A wrap that notifies about missing observations."""

    _JUSTIFICATION = [{"type": "INFO", "message": "No observations spotted for this stack in Thoth's database",}]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[Any, Any]]:
        """Include this wrap in adviser, once."""
        if not builder_context.is_included(cls) and builder_context.is_adviser_pipeline():
            return {}

        return None

    def run(self, state: State) -> None:
        """Check for no observations made on the given state."""
        if not state.justification:
            state.add_justification(self._JUSTIFICATION)
