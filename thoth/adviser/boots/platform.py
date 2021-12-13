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

"""A boot to check if recommendation is targeting a supported platform."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr

from thoth.common import get_justification_link as jl

from ..boot import Boot
from ..exceptions import NotAcceptable

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PlatformBoot(Boot):
    """A boot to check if a supported platform is used.

    We could check this based on the database entries, but as this will change rarely, we can
    hardcode supported platforms here.
    """

    _JUSTIFICATION_LINK = jl("platform")
    _SUPPORTED_PLATFORMS = frozenset({"linux-x86_64"})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, always on unsupported platform."""
        if (
            builder_context.project.runtime_environment.platform not in cls._SUPPORTED_PLATFORMS
            and not builder_context.is_included(cls)
        ):
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Check if GPU enabled recommendations should be done."""
        platform = self.context.project.runtime_environment.platform
        msg = f"Platform {platform!r} is not supported, possible platforms are: " + ", ".join(self._SUPPORTED_PLATFORMS)
        self.context.stack_info.append(
            {
                "type": "ERROR",
                "message": msg,
                "link": self._JUSTIFICATION_LINK,
            }
        )
        raise NotAcceptable(f"{msg} - see {self._JUSTIFICATION_LINK}")
