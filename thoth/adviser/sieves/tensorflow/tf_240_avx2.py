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

"""A sieve that filters out TensorFlow==2.4.0 build as it requires AVX2 instruction set."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING
import logging

from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from ...enums import RecommendationType
from ...sieve import Sieve


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


class TensorFlow240AVX2IllegalInstructionSieve(Sieve):
    """A sieve that filters out TensorFlow==2.4.0 build as it requires AVX2 instruction set.

    See:
     * https://github.com/tensorflow/tensorflow/issues/45866
     * https://github.com/tensorflow/tensorflow/issues/45744
    """

    CONFIGURATION_DEFAULT = {"package_name": "tensorflow"}

    _JUSTIFICATION_ADDITION = {
        "type": "WARNING",
        "message": "Upstream TensorFlow=2.4.0 build filtered out as it requires AVX2 instruction "
        "set support which is not available.",
        "link": jl("tf_240_avx2"),
    }

    # A tuple (CPU_FAMILY, CPU_MODEL) of Intel processors supporting AVX2:
    #   https://en.wikipedia.org/wiki/Advanced_Vector_Extensions#CPUs_with_AVX2
    #   https://en.wikichip.org/wiki/intel/cpuid
    AVX2_CPUS = frozenset(
        {
            (0x6, 0x5),  # Cascade Lake
            (0x6, 0x6),  # Broadwell, Cannon Lake
            (0x6, 0xA),  # Ice Lake
            (0x6, 0xC),  # Ice Lake, Tiger Lake
            (0x6, 0xD),  # Ice Lake
            (0x6, 0xE),  # Skylake, Kaby Lake, Coffee Lake, Ice Lake, Comet Lake, Whiskey Lake
            (0x6, 0xF),  # Haswell
        }
    )

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register this pipeline unit for adviser and stable/testing recommendation types."""
        cpu_tuple = (
            builder_context.project.runtime_environment.hardware.cpu_family,
            builder_context.project.runtime_environment.hardware.cpu_model,
        )

        if (
            builder_context.is_adviser_pipeline()
            and not builder_context.is_included(cls)
            and builder_context.recommendation_type != RecommendationType.LATEST
            and all(i is not None for i in cpu_tuple)
            and cpu_tuple not in cls.AVX2_CPUS
        ):
            yield {}
            return None

        yield from ()
        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Recommend not to use TensorFlow==2.4.0 on non-AVX2 enabled CPU processors."""
        for package_version in package_versions:
            if (
                package_version.name == "tensorflow"
                and package_version.locked_version == "2.4.0"
                and package_version.index.url == "https://pypi.org/simple"
            ):
                self.context.stack_info.append(self._JUSTIFICATION_ADDITION)
                continue

            yield package_version
