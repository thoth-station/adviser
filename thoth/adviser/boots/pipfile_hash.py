#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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
from typing import Any
from typing import Dict
from typing import Generator
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

    _JUSTIFICATION_PIPFILE_HASH_LINK = jl("pipfile_hash")
    _JUSTIFICATION_RM_USER_STACK = jl("rm_user_stack")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, always."""
        if (
            not builder_context.is_included(cls)
            and builder_context.project.pipfile_lock is not None
            and builder_context.project.pipfile_lock.meta.hash is not None
        ):
            yield {}
            return None

        yield from ()
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
            _LOGGER.warning("%s - %s", msg, self._JUSTIFICATION_PIPFILE_HASH_LINK)
            self.context.stack_info.append(
                {"type": "WARNING", "message": msg, "link": self._JUSTIFICATION_PIPFILE_HASH_LINK}
            )

            msg = "Detected changes in the lock file invalidate using user's stack as a base"
            self.context.stack_info.append(
                {
                    "type": "WARNING",
                    "message": msg,
                    "link": self._JUSTIFICATION_RM_USER_STACK,
                }
            )
            _LOGGER.warning("%s - %s", msg, self._JUSTIFICATION_RM_USER_STACK)
            self.context.project.pipfile_lock = None

        if (
            self.context.cli_parameters.get("dev", False)
            and self.context.project.pipfile.dev_packages.packages
            and self.context.project.pipfile_lock
            and not self.context.project.pipfile_lock.dev_packages.packages
        ):
            self.context.project.pipfile_lock = None
            msg = (
                "User's lock file submitted does not provide development dependencies, discarding the "
                "lock file provided as the resolution will consider also development dependencies"
            )
            _LOGGER.warning("%s - %s", msg, self._JUSTIFICATION_RM_USER_STACK)
            self.context.stack_info.append(
                {
                    "type": "WARNING",
                    "message": msg,
                    "link": self._JUSTIFICATION_RM_USER_STACK,
                }
            )
        elif (
            not self.context.cli_parameters.get("dev", False)
            and self.context.project.pipfile_lock
            and self.context.project.pipfile_lock.dev_packages.packages
        ):
            self.context.project.pipfile_lock = None
            msg = (
                "User's lock file submitted has locked development dependencies but the resolution was "
                "triggered without requesting to resolve development dependencies, the submitted lock file will "
                "not be considered"
            )
            _LOGGER.warning("%s - %s", msg, self._JUSTIFICATION_RM_USER_STACK)
            self.context.stack_info.append(
                {
                    "type": "WARNING",
                    "message": msg,
                    "link": self._JUSTIFICATION_RM_USER_STACK,
                }
            )
