#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""A boot that adds information about Thoth s2i used."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING
from voluptuous import Required
from voluptuous import Schema

from thoth.common import get_justification_link as jl

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


class ThothS2IInfoBoot(Boot):
    """A boot that adds information about Thoth s2i used."""

    _THOTH_S2I_PREFIX = "quay.io/thoth-station/s2i-thoth-"
    _THOTH_S2I_BASE = "quay.io/thoth-station/"

    CONFIGURATION_DEFAULT = {"message": None, "link": None, "type": "INFO"}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("message"): str,
            Required("link"): str,
            Required("type"): str,
        }
    )

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[Any, Any], None, None]:
        """Include this boot in adviser if Thoth s2i is used.."""
        base_image = builder_context.project.runtime_environment.base_image
        if not builder_context.is_included(cls) and base_image and base_image.startswith(cls._THOTH_S2I_PREFIX):
            thoth_s2i_name = base_image.split(":", maxsplit=1)[0]
            thoth_s2i_name = thoth_s2i_name[len(cls._THOTH_S2I_BASE) :]
            yield {
                "message": "Check more information about the runtime environment used",
                "link": jl(thoth_s2i_name),
                "type": "INFO",
            }
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Add information about the base image used to justification."""
        self.context.stack_info.append(self.configuration)
