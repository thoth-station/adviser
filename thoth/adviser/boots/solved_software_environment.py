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

"""A boot to check for solved software environment before running any resolution."""

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
class SolvedSoftwareEnvironmentBoot(Boot):
    """A boot to check for solved software environment before running any resolution."""

    @classmethod
    def should_include(
        cls, builder_context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Register self, always."""
        if not builder_context.project.runtime_environment.is_fully_specified():
            return None

        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self) -> None:
        """Check for version clash in packages."""
        if self.context.graph.solved_software_environment_exists(
            os_name=self.context.project.runtime_environment.operating_system.name,
            os_version=self.context.project.runtime_environment.operating_system.version,
            python_version=self.context.project.runtime_environment.python_version,
        ):
            return

        runtime_environment = self.context.project.runtime_environment
        msg = (
            f"No observations found for {runtime_environment.operating_system.name!r} in "
            f"version {runtime_environment.operating_system.version!r} using "
            f"Python {runtime_environment.python_version!r}"
        )

        _LOGGER.warning(msg)
        _LOGGER.warning("Available configurations:")

        configurations = (
            self.context.graph.get_solved_python_package_versions_software_environment_all()
        )
        _LOGGER.warning(
            "{:<16} {:<16} {:<8}".format("OS name", "OS version", "Python version")
        )
        for conf in sorted(
            configurations,
            key=lambda i: (i["os_name"], i["os_version"], i["python_version"]),
        ):
            _LOGGER.warning(
                "{:<16} {:<16} {:<8}".format(
                    conf["os_name"], conf["os_version"], conf["python_version"]
                )
            )

        raise NotAcceptable(msg)
