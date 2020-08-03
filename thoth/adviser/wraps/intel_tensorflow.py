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

"""A wrap that notifies about Intel TensorFlow builds."""

from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

from ..state import State
from ..wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


class IntelTensorFlowWrap(Wrap):
    """A wrap that recommends using Intel TensorFlow if TensorFlow is in resolved dependencies.

    https://software.intel.com/content/www/us/en/develop/articles/intel-optimization-for-tensorflow-installation-guide.html#pip_wheels
    """

    # Sandy bridge CPUID taken from https://en.wikipedia.org/wiki/Sandy_Bridge
    # Ivy bridge CPUID taken from https://en.wikipedia.org/wiki/Ivy_Bridge_(microarchitecture)
    #
    # As CPUID encodes family (bits 8 - 11 with mask 0xF00) and model (bits 4 - 7 with mask 0xF0) we got these
    # numbers from CPUID.
    _CPU_TABLE = frozenset(
        {
            # tuple (model, family)
            # Sandy Bridge-HE-4, Sandy Bridge-H-2, Sandy Bridge-M-2
            # ((0x0206A7 & 0xF0) >> 4, (0x0206A7 & 0xF00) >> 8),
            # Sandy Bridge - EP - 8
            # ((0x0206D6 & 0xF0) >> 4, (0x0206D6 & 0xF00) >> 8),
            # ((0x0206D7 & 0xF0) >> 4, (0x0206D7 & 0xF00) >> 8),
            # Sandy Bridge - EP - 4
            # ((0x0206D6 & 0xF0) >> 4, (0x0206D6 & 0xF00) >> 8),
            # ((0x0206D7 & 0xF0) >> 4, (0x0206D7 & 0xF00) >> 8),
            # Ivy Bridge-M-2, Ivy Bridge-H-2, Ivy Bridge-HM-4, Ivy Bridge-HE-4
            # ((0x000306A9 & 0xF0) >> 4, (0x000306A9 & 0xF00) >> 8),
            # All maps to the following values:
            (13, 6),
            (10, 6),
        }
    )
    _JUSTIFICATION = [
        {
            "type": "INFO",
            "message": "Consider using intel-tensorflow which is optimized for CPU detected in your environment",
        }
    ]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include this wrap for x86_64 architecture on CPU models with Ivy/Sandy bridge."""
        if builder_context.is_included(cls):
            return None

        if not builder_context.is_adviser_pipeline():
            return None

        runtime_environment = builder_context.project.runtime_environment
        cpu_tuple = (runtime_environment.hardware.cpu_model, runtime_environment.hardware.cpu_family)
        if runtime_environment.platform == "linux-x86_64" and cpu_tuple in cls._CPU_TABLE:
            return {}

        return None

    def run(self, state: State) -> None:
        """Recommend using intel-tensorflow if tensorflow is resolved."""
        if "tensorflow" in state.resolved_dependencies and "intel-tensorflow" not in state.resolved_dependencies:
            state.add_justification(self._JUSTIFICATION)
