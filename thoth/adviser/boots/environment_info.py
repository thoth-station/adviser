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

"""A boot to notify about environment used."""

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
class EnvironmentInfoBoot(Boot):
    """A boot to notify about environment used."""

    _JUSTIFICATION_LINK_ENV = jl("env")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, always."""
        if not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Notify about environment used."""
        runtime_environment = self.context.project.runtime_environment
        base_image = self.context.project.runtime_environment.base_image
        hardware = self.context.project.runtime_environment.hardware
        recommendation_type = (
            self.context.recommendation_type.name.lower() if self.context.recommendation_type else "UNKNOWN"
        )

        self.context.stack_info.extend(
            [
                {
                    "message": f"Resolving for runtime environment named " f"{runtime_environment.name or 'UNKNOWN'!r}",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "type": "INFO",
                },
                {
                    "message": f"Resolving for operating system "
                    f"{runtime_environment.operating_system.name!r} "
                    f"in version {runtime_environment.operating_system.version!r}",
                    "link": self._JUSTIFICATION_LINK_ENV,
                },
                {
                    "message": f"Resolving for Python version {self.context.project.python_version!r}",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "type": "INFO",
                },
                {
                    "message": f"Using recommendation type {recommendation_type!r}",
                    "link": "https://thoth-station.ninja/recommendation-types/",
                    "type": "INFO",
                },
                {
                    "message": f"Using platform {(runtime_environment.platform or 'UNKNOWN')!r}",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "type": "INFO",
                },
                {
                    "message": f"Using constraints provided"
                    if self.context.project.constraints.package_versions
                    else "No constraints supplied to the resolution process",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "type": "INFO",
                },
                {
                    "message": f"Using supplied static source code analysis"
                    if self.context.library_usage
                    else "No static source code analysis supplied",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "type": "INFO",
                },
                {
                    "type": "INFO",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "message": f"Using containerized environment {base_image!r}"
                    if base_image
                    else "No containerized environment used",
                },
                {
                    "type": "INFO",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "message": f"Using CPU family {(hardware.cpu_family or 'UNKNWON')!r} "
                    f"model {(hardware.cpu_model or 'UNKNOWN')!r}",
                },
                {
                    "type": "INFO",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "message": f"Using CUDA {runtime_environment.cuda_version!r}"
                    if runtime_environment.cuda_version
                    else "No CUDA used",
                },
                {
                    "type": "INFO",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "message": f"Using cuDNN {runtime_environment.cudnn_version!r}"
                    if runtime_environment.cudnn_version
                    else "No cuDNN used",
                },
                {
                    "type": "INFO",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "message": f"Using OpenBLAS {runtime_environment.openblas_version!r}"
                    if runtime_environment.openblas_version
                    else "No OpenBLAS used",
                },
                {
                    "type": "INFO",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "message": f"Using OpenMPI {runtime_environment.openmpi_version!r}"
                    if runtime_environment.openmpi_version
                    else "No OpenMPI used",
                },
                {
                    "type": "INFO",
                    "link": self._JUSTIFICATION_LINK_ENV,
                    "message": f"Using MKL {runtime_environment.mkl_version!r}"
                    if runtime_environment.mkl_version
                    else "No MKL used",
                },
            ]
        )
