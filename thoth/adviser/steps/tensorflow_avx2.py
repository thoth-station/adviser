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

"""Recommend TensorFlow builds optimized for AVX2 enabled CPU processors."""

from typing import Any
from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict
from typing import TYPE_CHECKING
import logging

from thoth.python import PackageVersion

from ..enums import RecommendationType
from ..state import State
from ..step import Step


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


class TensorFlowAVX2Step(Step):
    """A step that recommends AICoE TensorFlow builds optimized for AVX2 enabled CPU processors."""

    _SCORE_ADDITION = 0.2
    _JUSTIFICATION_ADDITION = [
        {
            "type": "INFO",
            "message": (
                "AICoE TensorFlow builds are optimized for AVX2 instruction sets supported in the CPU identified"
            ),
        }
    ]

    # A tuple (CPU_FAMILY, CPU_MODEL) of Intel processors supporting AVX2:
    #   https://en.wikipedia.org/wiki/Advanced_Vector_Extensions#CPUs_with_AVX2
    #   https://en.wikichip.org/wiki/intel/cpuid
    _AVX2_CPUS = frozenset(
        {
            (0x6, 0x5),  # Cascade Lake
            (0x6, 0x6),  # Broadwell, Cannon Lake
            (0x6, 0xA),  # Ice Lake
            (0x6, 0xC),  # Ice Lake, Tiger Lake
            (0x6, 0xD),  # Ice Lake
            (0x6, 0xE),  # Skylake, Keby Lake, Coffee Lake, Ice Lake, Comet Lake
            (0x6, 0xF),  # Haswell
        }
    )

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register this pipeline unit for adviser and stable/testing recommendation types."""
        if not builder_context.is_adviser_pipeline():
            return None

        if builder_context.recommendation_type == RecommendationType.LATEST:
            return None

        cpu_tuple = (
            builder_context.project.runtime_environment.hardware.cpu_family,
            builder_context.project.runtime_environment.hardware.cpu_model,
        )
        if cpu_tuple not in cls._AVX2_CPUS:
            # No AVX2 support for the given CPU or no CPU info.
            return None

        if not builder_context.is_included(cls):
            return {}

        return None

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Recommend TensorFlow builds optimized for AVX2 enabled CPU processors."""
        if package_version.name != "tensorflow":
            return None

        aicoe_config = self.get_aicoe_configuration(package_version)
        if not aicoe_config or aicoe_config["configuration"].lower() != "avx2":
            # Not an AICoE build or not an AVX2 build.
            return None

        return self._SCORE_ADDITION, self._JUSTIFICATION_ADDITION
