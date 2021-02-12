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

"""A wrap that notifies a bug in the tf.keras.Embedding layer."""

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


class TensorFlowSlowKerasEmbedding(Wrap):
    """A wrap that notifies a bug in the embedding layer.

    https://github.com/tensorflow/tensorflow/issues/42475
    """

    CONFIGURATION_DEFAULT = {"package_name": "tensorflow"}
    _JUSTIFICATION = [
        {
            "type": "WARNING",
            "message": "TensorFlow in version <=2.4 is slow when tf.keras.layers.Embedding is used",
            "link": jl("tf_42475"),
        }
    ]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Include this wrap in adviser."""
        if (
            builder_context.is_adviser_pipeline()
            and not builder_context.is_included(cls)
            and builder_context.library_usage is not None
            and "tensorflow.keras.layers.Embedding" in (builder_context.library_usage.get("tensorflow") or [])
        ):
            yield {"package_name": "tensorflow"}
            yield {"package_name": "tensorflow-cpu"}
            yield {"package_name": "tensorflow-gpu"}
            yield {"package_name": "intel-tensorflow"}
            return None

        yield from ()
        return None

    def run(self, state: State) -> None:
        """Notify about a bug in summary output spotted on TensorFlow 2.3."""
        tensorflow_any = (
            state.resolved_dependencies.get("tensorflow")
            or state.resolved_dependencies.get("tensorflow-cpu")
            or state.resolved_dependencies.get("tensorflow-gpu")
            or state.resolved_dependencies.get("intel-tensorflow")
        )

        if tensorflow_any is None:
            return None

        tf_package_version: PackageVersion = self.context.get_package_version(tensorflow_any)
        if tf_package_version.semantic_version.release[:2] <= (2, 4):
            state.add_justification(self._JUSTIFICATION)
