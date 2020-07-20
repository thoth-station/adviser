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

"""A boot that checks for platform used and adjust to the default one if not provided explicitly."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import TYPE_CHECKING

import attr
from voluptuous import Required
from voluptuous import Schema

from ..boot import Boot
from ..exceptions import NotAcceptable

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PlatformBoot(Boot):
    """A boot that checks for platform used and adjust to the default one if not provided explicitly."""

    CONFIGURATION_DEFAULT = {"default_platform": "linux-x86_64"}
    CONFIGURATION_SCHEMA = Schema({Required("default_platform"): str,})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, always."""
        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self) -> None:
        """Check for platform configured and adjust to the default one if not provided by user."""
        if self.context.project.runtime_environment.platform is None:
            _LOGGER.warning(
                "No platform provided in the configuration, setting to %r implicitly",
                self.configuration["default_platform"],
            )
            self.context.project.runtime_environment.platform = self.configuration["default_platform"]

        platform = self.context.project.runtime_environment.platform
        if not self.context.graph.python_package_version_depends_on_platform_exists(platform):
            raise NotAcceptable(f"No platform conforming to {platform!r} found in the database")
