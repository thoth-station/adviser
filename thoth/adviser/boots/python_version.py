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

"""A boot to check Python version configuration used in adviser."""

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
class PythonVersionBoot(Boot):
    """A boot that checks Python3 configuration used by user."""

    @classmethod
    def should_include(
        cls, builder_context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Register self, always for adviser."""
        if not builder_context.is_adviser_pipeline():
            return None

        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self) -> None:
        """Check Python configuration used by user."""
        python_version = self.context.project.runtime_environment.python_version
        pipfile_python_version = self.context.project.pipfile.meta.requires.get(
            "python_version"
        )
        if pipfile_python_version is not None and python_version is None:
            msg = (
                f"No version of Python specified in the configuration, using Python version "
                f"found in Pipfile: {pipfile_python_version!r}"
            )
            _LOGGER.warning(msg)
            self.context.project.runtime_environment.python_version = (
                pipfile_python_version
            )
            self.context.stack_info.append({"type": "WARNING", "Message": msg})
        elif python_version is not None and pipfile_python_version is None:
            msg = (
                f"No version of Python specified explicitly, assigning the one found in "
                f"Thoth's configuration: {python_version!r}"
            )
            _LOGGER.warning(msg)
            self.context.project.pipfile.meta.requires[
                "python_version"
            ] = python_version
            self.context.stack_info.append({"type": "WARNING", "Message": msg})
