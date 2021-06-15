#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

from thoth.adviser.stride import Stride
from thoth.adviser.state import State
from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required

if TYPE_CHECKING:
    from thoth.adviser.pipeline_builder import PipelineBuilderContext


class Stride1(Stride):
    """A testing stride implementation."""

    CONFIGURATION_DEFAULT = {
        "linus": {"residence": "oregon", "children": 3, "parents": ["nils", "anna"]},
        "package_name": None,
    }
    CONFIGURATION_SCHEMA: Schema = Schema({Required("linus"): object, Required("package_name"): SchemaAny(str, None)})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if this pipeline unit should be included in the pipeline configuration."""
        yield from ()
        return None

    def run(self, state: State) -> Optional[Tuple[float, List[Dict[str, str]]]]:
        """Run noop method."""


class Stride2(Stride):
    """A testing stride implementation."""

    CONFIGURATION_DEFAULT = {"foo": None, "package_name": "thamos"}
    CONFIGURATION_SCHEMA: Schema = Schema({Required("foo"): object, Required("package_name"): SchemaAny(str, None)})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if this pipeline unit should be included in the pipeline configuration."""
        yield from ()
        return None

    def run(self, state: State) -> Optional[Tuple[float, List[Dict[str, str]]]]:
        """Run noop method."""


__all__ = ["Stride1", "Stride2"]
