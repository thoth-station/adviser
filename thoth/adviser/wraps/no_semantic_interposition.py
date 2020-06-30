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

"""A wrap that notifies about optimized Python3.8 builds on RHEL with -fno-semantic-interposition."""

from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

from ..state import State
from ..wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


class NoSemanticInterpositionWrap(Wrap):
    """A wrap that recommends to switch to Python 3.8 on RHEL 8.2.

    https://developers.redhat.com/blog/2020/06/25/red-hat-enterprise-linux-8-2-brings-faster-python-3-8-run-speeds/
    """

    _JUSTIFICATION = [
        {
            "type": "INFO",
            "message": "Consider using UBI or RHEL 8.2 with Python 3.8 that has optimized Python interpreter with "
            "performance gain up to 30%",
        }
    ]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include this wrap in adviser for RHEL/UBI 8.2."""
        if builder_context.is_included(cls):
            return None

        if not builder_context.is_adviser_pipeline():
            return None

        if (
            builder_context.project.runtime_environment.operating_system.name in ("rhel", "ubi")
            and builder_context.project.runtime_environment.operating_system.version == "8.2"
            and builder_context.project.runtime_environment.python_version != "3.8"
        ):
            return {}

        return None

    def run(self, state: State) -> None:
        """Recommend using Python3.8 on RHEL/UBI 8.2."""
        state.add_justification(self._JUSTIFICATION)
