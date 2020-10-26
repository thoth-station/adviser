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

"""Suggest not to use TensorFlow 2.1 with specific urllib3 versions that cause six import issues."""

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
class TensorFlow21Urllib3Step(Step):
    """A step that suggests not to use TensorFlow 2.1 with specific urllib3 versions that cause six import issues."""

    _message_logged = attr.ib(type=bool, default=False, init=False)

    CONFIGURATION_DEFAULT = {"package_name": "urllib3", "multi_package_resolution": False}

    _MESSAGE = (
        "TensorFlow in version 2.1 can cause runtime errors when imported, caused by "
        "incompatibility between urllib3 and six packages"
    )
    _LINK = jl("tf_21_urllib3")
    _AFFECTED_URLLIB3_VERSIONS = frozenset({(1, 2), (1, 3), (1, 4), (1, 5)})

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
        """Suggest not to use TensorFlow 2.1 with specific urllib3 as issues with six were spotted on imports."""
        if package_version.semantic_version.release[:2] not in self._AFFECTED_URLLIB3_VERSIONS:
            return None

        tensorflow_any = (
            state.resolved_dependencies.get("tensorflow")
            or state.resolved_dependencies.get("tensorflow-cpu")
            or state.resolved_dependencies.get("tensorflow-gpu")
            or state.resolved_dependencies.get("intel-tensorflow")
        )

        if not tensorflow_any or (tensorflow_any[1] != "2.1" and not tensorflow_any[1].startswith("2.1.")):
            return None

        if not self._message_logged:
            self._message_logged = True
            _LOGGER.warning("%s - see %s", self._MESSAGE, self._LINK)
            self.context.stack_info.append({"type": "WARNING", "message": self._MESSAGE, "link": self._LINK})

        raise NotAcceptable
