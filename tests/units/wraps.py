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

"""A generic unit representatives used for testing.."""

from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

from thoth.adviser.wrap import Wrap
from thoth.adviser.state import State

if TYPE_CHECKING:
    from thoth.adviser.pipeline_builder import PipelineBuilderContext


class Wrap1(Wrap):
    """A testing wrap implementation."""

    CONFIGURATION_DEFAULT = {
        "thoth": [2018, 2019],
        "cities": ["Brno", "Bonn", "Boston", "Milan"],
    }

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Check if this pipeline unit should be included in the pipeline configuration."""

    def run(self, state: State) -> None:
        """Run noop method."""


class Wrap2(Wrap):
    """A testing wrap implementation."""

    CONFIGURATION_DEFAULT: Dict[str, Any] = {}

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Check if this pipeline unit should be included in the pipeline configuration."""

    def run(self, state: State) -> None:
        """Run noop method."""


__all__ = ["Wrap1", "Wrap2"]
