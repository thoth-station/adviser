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

"""A step that removes SciPy dependency from the dependency listing for TensorFlow>=2.1<=2.3."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

import logging

import attr
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from ...enums import RecommendationType
from ...exceptions import SkipPackage
from ...state import State
from ...step import Step

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class TensorFlowRemoveSciPyStep(Step):
    """A step that removes SciPy dependency from a TensorFlow>2.1<=2.3 stack.

    https://github.com/tensorflow/tensorflow/pull/41866
    https://github.com/tensorflow/tensorflow/issues/40884
    https://github.com/tensorflow/tensorflow/issues/35709
    https://github.com/tensorflow/tensorflow/issues/41941
    https://github.com/tensorflow/tensorflow/pull/40789
    """

    CONFIGURATION_DEFAULT = {"package_name": "scipy", "multi_package_resolution": False}

    _message_logged = attr.ib(type=bool, default=False, init=False)

    _MESSAGE = "TensorFlow in versions >=2.1<=2.3 stated SciPy as a dependency but it is not used in the codebase"
    _LINK = jl("tf_rm_scipy")

    _RECOMMENDATION_TYPES = {RecommendationType.LATEST, RecommendationType.TESTING}

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[Any, Any]]:
        """Include this unit in adviser, except for latest recommendations."""
        if (
            not builder_context.is_adviser_pipeline()
            or builder_context.recommendation_type in cls._RECOMMENDATION_TYPES
        ):
            return None

        if "scipy" in builder_context.project.pipfile.packages.packages:
            # scipy is a direct dependency, it should be always present in the stack.
            return None

        if not builder_context.is_included(cls):
            return {}

        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._message_logged = False
        super().pre_run()

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Remove SciPy dependency from a TensorFlow>2.1<=2.3 stack."""
        tensorflow_any = (
            state.resolved_dependencies.get("tensorflow")
            or state.resolved_dependencies.get("tensorflow-cpu")
            or state.resolved_dependencies.get("tensorflow-gpu")
        )

        if not tensorflow_any:
            return None

        tf_package_version = self.context.get_package_version(tensorflow_any)
        if not tf_package_version:
            return None

        tf_release = tf_package_version.semantic_version.release[:2]
        if tf_release < (2, 1) or tf_release >= (2, 3):
            return None

        # Now check what package introduced the SciPy dependency. If it is solely TensorFlow, we can
        # safely remove SciPy from dependencies.
        scipy_dependents = {i[0] for i in self.context.dependents["scipy"][package_version.to_tuple()]}
        introduced_by = scipy_dependents & set(state.resolved_dependencies.values())
        if len(introduced_by) == 1 and next(iter(introduced_by)) == tensorflow_any:
            if not self._message_logged:
                self._message_logged = True
                _LOGGER.warning("%s - see %s", self._MESSAGE, self._LINK)
                self.context.stack_info.append({"type": "WARNING", "message": self._MESSAGE, "link": self._LINK})

            raise SkipPackage

        return None
