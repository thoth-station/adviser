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

"""A boot unit representatives used for testing.."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

from thoth.adviser.boot import Boot
from voluptuous import Schema
from voluptuous import Required

if TYPE_CHECKING:
    from thoth.adviser.pipeline_builder import PipelineBuilderContext


class Boot1(Boot):
    """A testing boot implementation."""

    CONFIGURATION_DEFAULT = {"some_parameter": -0.2, "package_name": "flask"}
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): str, Required("some_parameter"): float})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if this pipeline unit should be included in the pipeline configuration."""
        yield from ()
        return None

    def run(self) -> None:
        """Run noop method."""


class Boot2(Boot):
    """A testing boot implementation."""

    CONFIGURATION_DEFAULT = {"package_name": None}

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if this pipeline unit should be included in the pipeline configuration."""
        yield from ()
        return None

    def run(self) -> None:
        """Run noop method."""


__all__ = ["Boot1", "Boot2"]
