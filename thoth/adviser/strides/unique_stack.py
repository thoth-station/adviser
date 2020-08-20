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

"""Filter out software stacks that were already resolved.

This pipeline unit is especially useful for dependency monkey runs when no
duplicate software stacks should be resolved.
"""

import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Set
from typing import FrozenSet
from typing import TYPE_CHECKING

import attr

from ..state import State
from ..stride import Stride
from ..exceptions import NotAcceptable

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class UniqueStackStride(Stride):
    """Filter out software stacks that were already resolved.

    As dependency graphs can share nodes, it might happen that the same
    software stack can be resolved multiple times considering different
    resolution paths.
    """

    stacks_seen = attr.ib(type=Set[FrozenSet[Tuple[str, str, str]]], default=attr.Factory(set), init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include this pipeline unit only if user asks for it explicitly."""
        return None

    def pre_run(self) -> None:
        """Initialize internal state of the unit."""
        self.stacks_seen.clear()

    def run(self, state: State) -> None:
        """Filter out software stacks that were already resolved."""
        stack = frozenset(state.resolved_dependencies.values())
        if stack not in self.stacks_seen:
            self.stacks_seen.add(stack)
        else:
            raise NotAcceptable
