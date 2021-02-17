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

"""A step that prevents resolving NumPy==1.19.5 with TensorFlow==2.4."""

import attr
from typing import Any
from typing import Optional
from typing import Generator
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
class TensorFlow24NumPyStep(Step):
    """A step that prevents resolving NumPy==1.19.5 with TensorFlow==2.4."""

    _message_logged = attr.ib(type=bool, default=False, init=False)

    CONFIGURATION_DEFAULT = {"package_name": "numpy", "multi_package_resolution": True}
    _MESSAGE = "NumPy==1.19.5 is causing issues when used with TensorFlow 2.4"
    _JUSTIFICATION_LINK = jl("tf_24_np")
    _JUSTIFICATION = [
        {
            "message": _MESSAGE,
            "link": _JUSTIFICATION_LINK,
            "type": "WARNING",
        }
    ]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register this pipeline unit for adviser if not using latest recommendations."""
        if (
            builder_context.is_adviser_pipeline()
            and builder_context.recommendation_type != RecommendationType.LATEST
            and not builder_context.is_included(cls)
        ):
            yield {}
            return None

        yield from ()
        return None

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Suggest not to use NumP==1.19.5 with TensorFlow 2.4."""
        if package_version.semantic_version.release[:3] != (1, 19, 5):
            return None

        tensorflow_any = (
            state.resolved_dependencies.get("tensorflow")
            or state.resolved_dependencies.get("tensorflow-cpu")
            or state.resolved_dependencies.get("tensorflow-gpu")
            or state.resolved_dependencies.get("intel-tensorflow")
        )

        if not tensorflow_any or not tensorflow_any[1].startswith("2.4."):
            return None

        if not self._message_logged:
            self._message_logged = True
            _LOGGER.warning("%s - see %s", self._MESSAGE, self._JUSTIFICATION_LINK)
            self.context.stack_info.append(
                {"type": "WARNING", "message": self._MESSAGE, "link": self._JUSTIFICATION_LINK}
            )

        raise NotAcceptable
