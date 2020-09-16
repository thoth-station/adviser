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

"""Suggest not to use TensorFlow 2.2 with tensorflow-probability."""

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
class TensorFlow22ProbabilityStep(Step):
    """Suggest not to use TensorFlow 2.2 with tensorflow-probability.

    https://github.com/tensorflow/tensorflow/issues/40584
    """

    # Run this step each time, regardless of when tensorflow and tensorflow-probability are resolved.
    MULTI_PACKAGE_RESOLUTIONS = True

    _MESSAGE = f"TensorFlow in version 2.2 and tensorflow-probability cause runtime errors - see {jl('tf_40584')}"

    _message_logged = attr.ib(type=bool, default=False, init=False)

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._message_logged = False

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
        """Suggest not to use TensorFlow 2.2 with with tensorflow-probability."""
        if package_version.name != "tensorflow-probability":
            return None

        tensorflow_any = (
            state.resolved_dependencies.get("tensorflow")
            or state.resolved_dependencies.get("tensorflow-cpu")
            or state.resolved_dependencies.get("tensorflow-gpu")
        )

        if not tensorflow_any or (tensorflow_any[1] != "2.2" and not tensorflow_any[1].startswith("2.2.")):
            return None

        if not self._message_logged:
            _LOGGER.warning(self._MESSAGE)
            self._message_logged = True

        raise NotAcceptable
