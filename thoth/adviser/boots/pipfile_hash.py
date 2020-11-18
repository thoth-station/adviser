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

"""A boot that checks for Pipfile hash and reports any mismatch to users.."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import TYPE_CHECKING

from thoth.common import get_justification_link as jl

import attr

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PipfileHashBoot(Boot):
    """A boot that checks for Pipfile hash and reports any mismatch to users.."""

    _JUSTIFICATION_LINK = jl("pipfile_hash")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, always."""
        if builder_context.is_included(cls):
            return None

        if (
            builder_context.project.pipfile_lock is not None
            and builder_context.project.pipfile_lock.meta.hash is not None
        ):
            return {}

        return None

    def run(self) -> None:
        """Check for platform configured and adjust to the default one if not provided by user."""
        pipfile_hash = self.context.project.pipfile_lock.meta.hash.get("sha256")
        computed_hash = self.context.project.pipfile.hash().get("sha256")
        if pipfile_hash != computed_hash:
            msg = (
                f"Pipfile hash stated in the Pipfile.lock ({pipfile_hash[:6]}) does not correspond to the "
                f"hash computed ({computed_hash[:6]}) - was Pipfile adjusted?"
            )
            _LOGGER.warning("%s - %s", msg, self._JUSTIFICATION_LINK)
            self.context.stack_info.append({"type": "WARNING", "message": msg, "link": self._JUSTIFICATION_LINK})
