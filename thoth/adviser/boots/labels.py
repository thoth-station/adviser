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

"""A boot to notify about labels used during the resolution."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.common import get_justification_link as jl

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class LabelsBoot(Boot):
    """A boot to notify about labels used during the resolution."""

    _JUSTIFICATION_LINK = jl("labels")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self if labels are used."""
        if not builder_context.is_included(cls) and builder_context.labels:
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Notify about labels used during the resolution process.."""
        for key, value in self.context.labels.items():
            msg = f"Considering label {key}={value} in the resolution process"
            _LOGGER.info("%s - see %s", msg, self._JUSTIFICATION_LINK)
            self.context.stack_info.append(
                {
                    "message": msg,
                    "type": "INFO",
                    "link": self._JUSTIFICATION_LINK,
                }
            )
