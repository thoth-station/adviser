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

"""A boot to adjust RHEL version to its major version."""

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
class RHELVersionBoot(Boot):
    """A boot that changes version of RHEL used.

    RHEL guarantees ABI compatibility across major minor releases.
    """

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, always."""
        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self) -> None:
        """Discard any minor release in RHEL."""
        os_name = self.context.project.runtime_environment.operating_system.name
        os_version = self.context.project.runtime_environment.operating_system.version
        if os_name == "rhel" and os_version is not None:
            version_parts = os_version.split(".", maxsplit=1)
            if len(version_parts) > 1:
                _LOGGER.info(
                    "RHEL major releases guarantee ABI compatibility across minor releases; "
                    "discarding minor release information and using RHEL version %r",
                    version_parts[0],
                )
                self.context.project.runtime_environment.operating_system.version = version_parts[0]
