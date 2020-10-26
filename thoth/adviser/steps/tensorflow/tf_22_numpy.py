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

"""TensorFlow <2.3>=2.0 states NumPy<2.0.0 as a dependency, but is compatible with NumPy<1.19.0."""

import attr
from typing import Any
from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict
from typing import TYPE_CHECKING
import logging

from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from ...enums import RecommendationType
from ...exceptions import NotAcceptable
from ...state import State
from ...step import Step


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class TensorFlow22NumPyStep(Step):
    """Suggest to use TensorFlow <2.3>=2.0 with NumPy<1.19.0.

    https://github.com/numpy/numpy/pull/15355
    https://github.com/tensorflow/tensorflow/commit/79518facb4b857af9d9d5df2da463fdbf7eb0e3e
    https://github.com/tensorflow/tensorflow/issues/41902
    """

    CONFIGURATION_DEFAULT = {"package_name": "numpy", "multi_package_resolution": False}

    _MESSAGE = "TensorFlow <2.3>=2.0 states NumPy<2.0.0 as a dependency, but is compatible with NumPy<1.19.0"
    _LINK = jl("tf_41902")

    _message_logged = attr.ib(type=bool, default=False, init=False)

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._message_logged = False
        super().pre_run()

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register this pipeline unit for adviser if not using latest recommendations."""
        if (
            not builder_context.is_adviser_pipeline()
            or builder_context.recommendation_type == RecommendationType.LATEST
        ):
            return None

        if not builder_context.is_included(cls):
            return {}

        return None

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Suggest to use TensorFlow <2.3>=2.0 with NumPy<1.19.0."""
        if package_version.semantic_version.release[:2] < (1, 19):
            return None

        tensorflow_any = (
            state.resolved_dependencies.get("tensorflow")
            or state.resolved_dependencies.get("tensorflow-cpu")
            or state.resolved_dependencies.get("tensorflow-gpu")
            or state.resolved_dependencies.get("intel-tensorflow")
        )

        if not tensorflow_any:
            return None

        tf_package_version = self.context.get_package_version(tensorflow_any)
        if tf_package_version and (2, 0) <= tf_package_version.semantic_version.release[:2] < (2, 3):
            if not self._message_logged:
                self._message_logged = True
                _LOGGER.warning("%s - see %s", self._MESSAGE, self._LINK)
                self.context.stack_info.append({"type": "WARNING", "message": self._MESSAGE, "link": self._LINK})

            raise NotAcceptable

        return None
