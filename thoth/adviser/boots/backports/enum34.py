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

"""A boot to remove backport of enum34 intended for older Python versions."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import TYPE_CHECKING

import attr
from ...boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Enum34BackportBoot(Boot):
    """Remove backport of enum34, available in the standard library starting Python 3.4.

    https://pypi.org/project/enum34/
    https://docs.python.org/3/library/enum.html
    """

    _MESSAGE = "Direct dependency 'enum34' removed: emum34 is available in Python standard library starting Python 3.4"

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include for Python 3.5 and above for adviser and dependency monkey runs."""
        if builder_context.is_included(cls) or builder_context.project.runtime_environment.python_version is None:
            return None

        if builder_context.project.runtime_environment.get_python_version_tuple() >= (3, 4) and (
            "enum34" in builder_context.project.pipfile.packages.packages
            or "enum34" in builder_context.project.pipfile.dev_packages.packages
        ):
            return {}

        return None

    def run(self) -> None:
        """Remove dependency enum34 for newer Python versions."""
        _LOGGER.warning(self._MESSAGE)
        self.context.stack_info.append({"type": "INFO", "message": self._MESSAGE})
        self.context.project.pipfile.packages.packages.pop("enum34", None)
        self.context.project.pipfile.dev_packages.packages.pop("enum34", None)
