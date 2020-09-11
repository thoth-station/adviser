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

"""A wrap that notifies about adjusting environment variables when Intel's MKL is used.

https://software.intel.com/en-us/mkl-linux-developer-guide-setting-the-number-of-openmp-threads
"""

from typing import TYPE_CHECKING
from typing import Optional, Dict, Any

from ..state import State
from ..wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


class MKLThreadsWrap(Wrap):
    """A wrap that notifies about Intel's MKL thread configuration for containerized deployments.

    https://software.intel.com/en-us/mkl-linux-developer-guide-setting-the-number-of-openmp-threads
    """

    _JUSTIFICATION = [
        {
            "type": "WARNING",
            "message": "Consider adjusting OMP_NUM_THREADS environment variable for containerized deployments, "
            "one or more libraries use Intel's MKL that does not detect correctly "
            "resource allocation in the cluster",
        }
    ]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[Any, Any]]:
        """Include this wrap in adviser, once."""
        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self, state: State) -> None:
        """Check for libraries using PyTorch."""
        if (
            "torch" in state.resolved_dependencies
            or "pytorch" in state.resolved_dependencies
            or "intel-tensorflow" in state.resolved_dependencies
        ):
            state.add_justification(self._JUSTIFICATION)
