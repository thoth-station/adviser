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

"""A wrap that notifies about accuracy bug on safe()/load_model() calls."""

from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

from thoth.common import get_justification_link as jl

from ...state import State
from ...wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


class TensorFlow23Accuracy(Wrap):
    """A wrap that notifies about accuracy bug on safe()/load_model() calls.

    https://github.com/tensorflow/tensorflow/issues/42045
    https://github.com/keras-team/keras/issues/14181
    https://github.com/tensorflow/tensorflow/commit/5adacc88077ef82f6c4a7f9bb65f9ed89f9d8947
    """

    _JUSTIFICATION = [
        {
            "type": "WARNING",
            "message": "TensorFlow in version 2.3 produces wrong model accuracy when the model is "
            "serialized using `accuracy`, use `sparse_categorical_accuracy` instead",
            "link": jl("tf_42045"),
        }
    ]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include this wrap in adviser."""
        if builder_context.is_included(cls) or not builder_context.is_adviser_pipeline():
            return None

        return {}

    def run(self, state: State) -> None:
        """Notify about accuracy bug in safe()/load_model() calls."""
        if "tensorflow" in state.resolved_dependencies and state.resolved_dependencies["tensorflow"][1][:3] == "2.3":
            state.add_justification(self._JUSTIFICATION)
