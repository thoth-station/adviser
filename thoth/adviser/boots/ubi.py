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

"""A boot to remap UBI to RHEL."""

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
class UbiBoot(Boot):
    """Remap UBI to RHEL.

    As UBI has ABI compatibility with RHEL, remap any UBI to RHEL.
    """

    _MESSAGE = "Using observations for RHEL instead of UBI, RHEL is ABI compatible with UBI"
    _JUSTIFICATION_LINK = jl("rhel_ubi")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self if UBI is used."""
        if (
            builder_context.project.runtime_environment.operating_system.name == "ubi"
            and not builder_context.is_included(cls)
        ):
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Remap UBI to RHEL as Thoth keeps track of RHEL and UBI is ABI compatible."""
        _LOGGER.info("%s - see %s", self._MESSAGE, self._JUSTIFICATION_LINK)
        self.context.stack_info.append({"type": "WARNING", "message": self._MESSAGE, "link": self._JUSTIFICATION_LINK})
        self.context.project.runtime_environment.operating_system.name = "rhel"
