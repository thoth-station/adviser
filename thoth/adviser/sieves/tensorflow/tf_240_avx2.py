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
from typing import Optional
from typing import TYPE_CHECKING
import logging

from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from ...enums import RecommendationType
from ...sieve import Sieve
from ...steps.tensorflow.tf_avx2 import TensorFlowAVX2Step


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

        if any(i is None for i in cpu_tuple):
            return None

        if cpu_tuple in TensorFlowAVX2Step.AVX2_CPUS:
            # AVX2 supported, TensorFlow will work.
            return None

        if not builder_context.is_included(cls):
            return {}

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
