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

"""A boot to check for fully specified environment."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import TYPE_CHECKING

import attr

from ..boot import Boot
from ..exceptions import NotAcceptable

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class FullySpecifiedEnvironment(Boot):
    """A boot to check for fully specified environment."""

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, always."""
        if not builder_context.is_adviser_pipeline():
            return None

        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self) -> None:
        """Check for version clash in packages."""
        if not self.context.project.runtime_environment.is_fully_specified():
            raise NotAcceptable(
                f"Software environment supplied is not fully specified, OS name "
                f"is {self.context.project.runtime_environment.operating_system.name!r} "
                f"in version {self.context.project.runtime_environment.operating_system.version!r} "
                f"using Python {self.context.project.runtime_environment.python_version!r}"
            )
