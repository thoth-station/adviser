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

"""A boot to check if GPU specific recommendations should be done."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr

from thoth.common import get_justification_link as jl

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class GPUBoot(Boot):
    """A boot to check if GPU specific recommendations should be done."""

    _MESSAGE_NO_GPU = "CUDA version provided but no GPU model available, turning off GPU specific recommendations"
    _MESSAGE_NO_CUDA = "GPU model provided but no CUDA version available, turning off GPU specific recommendations"
    _JUSTIFICATION_LINK = jl("no_gpu")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, always."""
        if not builder_context.is_included(cls) and (
            builder_context.project.runtime_environment.cuda_version
            or builder_context.project.runtime_environment.hardware.gpu_model
        ):
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Check if GPU enabled recommendations should be done."""
        if (
            self.context.project.runtime_environment.cuda_version
            and not self.context.project.runtime_environment.hardware.gpu_model
        ):
            _LOGGER.warning(self._MESSAGE_NO_GPU)
            self.context.stack_info.append(
                {
                    "type": "WARNING",
                    "message": self._MESSAGE_NO_GPU,
                    "link": self._JUSTIFICATION_LINK,
                }
            )
            self.context.project.runtime_environment.cuda_version = None
        elif (
            not self.context.project.runtime_environment.cuda_version
            and self.context.project.runtime_environment.hardware.gpu_model
        ):
            _LOGGER.warning(self._MESSAGE_NO_CUDA)
            self.context.stack_info.append(
                {
                    "type": "WARNING",
                    "message": self._MESSAGE_NO_CUDA,
                    "link": self._JUSTIFICATION_LINK,
                }
            )
            self.context.project.runtime_environment.hardware.gpu_model = None
