#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""A boot to notify about runtime environments not supported by solvers enabled in a deployment."""

import os
import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.common import get_justification_link as jl
from thoth.common import OpenShift
from thoth.common.exceptions import SolverNameParseError

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SolversConfiguredBoot(Boot):
    """A boot to notify about runtime environments not supported by solvers enabled in a deployment."""

    _SOLVERS_CONFIGURED = os.getenv("THOTH_ADVISER_DEPLOYMENT_CONFIGURED_SOLVERS")
    _JUSTIFICATION = jl("eol_env")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self if users use runtime environments not matching solvers in the configmap."""
        if not cls._SOLVERS_CONFIGURED or builder_context.is_included(cls):
            yield from ()
            return None

        runtime_environment = (
            builder_context.project.runtime_environment.operating_system.name,
            builder_context.project.runtime_environment.operating_system.version,
            builder_context.project.python_version,
        )
        for solver_name in cls._SOLVERS_CONFIGURED.splitlines():
            solver_name = solver_name.strip()

            if not solver_name:
                continue

            try:
                solver_info = OpenShift.parse_python_solver_name(solver_name)
            except SolverNameParseError:
                _LOGGER.exception("Please report this error to Thoth service administrator")
                yield from ()
                return None

            if runtime_environment == (
                solver_info["os_name"],
                solver_info["os_version"],
                solver_info["python_version"],
            ):
                break
        else:
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Inform about runtime environment that is not backed up by a solver."""
        self.context.stack_info.append(
            {
                "type": "WARNING",
                "message": "Runtime environment used is no longer supported, it is "
                "recommended to switch to another runtime environment",
                "link": self._JUSTIFICATION,
            }
        )
