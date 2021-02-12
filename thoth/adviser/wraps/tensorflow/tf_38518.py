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

"""A wrap that notifies a bug that prevents from running TensorFlow if multiple processes are running on GPU."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from ...state import State
from ...wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


class TensorFlowMultipleProcessesGPUBug(Wrap):
    """A wrap that notifies a bug that prevents from running TensorFlow if multiple processes are running on GPU.

    https://github.com/tensorflow/tensorflow/issues/38518
    """

    CONFIGURATION_DEFAULT = {"package_name": "tensorflow"}
    _JUSTIFICATION = [
        {
            "type": "WARNING",
            "message": "TensorFlow in version 2.3 has a bug that prevents from running if multiple "
            "TensorFlow processes are running",
            "link": jl("tf_38518"),
        }
    ]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Include this wrap in adviser."""
        if (
            builder_context.is_adviser_pipeline()
            and not builder_context.is_included(cls)
            and builder_context.project.runtime_environment.cuda_version is not None
        ):
            yield {"package_name": "tensorflow"}
            yield {"package_name": "tensorflow-gpu"}
            return None

        yield from ()
        return None

    def run(self, state: State) -> None:
        """Notify about a bug when running multiple instances of TensorFlow."""
        tensorflow_any = state.resolved_dependencies.get("tensorflow") or state.resolved_dependencies.get(
            "tensorflow-gpu"
        )

        if tensorflow_any is None:
            return None

        tf_package_version: PackageVersion = self.context.get_package_version(tensorflow_any)
        if tf_package_version.semantic_version.release[:2] == (2, 3):
            state.add_justification(self._JUSTIFICATION)
