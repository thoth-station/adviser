#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Filter out states randomly."""

import logging
import random
from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

import attr

from ..state import State
from ..stride import Stride
from ..exceptions import NotAcceptable

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class RandomDecisionStride(Stride):
    """Filter out states randomly."""

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Allow inclusion only per user request."""
        return None

    def run(self, state: State) -> None:
        """Flip a coin and decide - tails are not acceptable."""
        if bool(random.getrandbits(1)):
            raise NotAcceptable(f"State with score {state.score!r} was randomly discarded by flipping a coin")
