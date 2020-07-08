#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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
from typing import Optional
from typing import Dict
from typing import Any
from typing import TYPE_CHECKING

import attr

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class UbiBoot(Boot):
    """Remap UBI to RHEL.

    As UBI has ABI compatibility with RHEL, remap any UBI to RHEL.
    """

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, always."""
        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self) -> None:
        """Remap UBI to RHEL as Thoth keeps track of RHEL and UBI is ABI compatible."""
        if self.context.project.runtime_environment.operating_system.name == "ubi":
            _LOGGER.info("Using observations for RHEL instead of UBI, RHEL is ABI compatible with UBI")
            self.context.project.runtime_environment.operating_system.name = "rhel"
