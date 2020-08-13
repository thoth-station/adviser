#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Kevin Postlethwait
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

"""Score based on security indicators aggregated."""

from typing import Any
from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict
from typing import TYPE_CHECKING
import logging
import os

from thoth.python import PackageVersion

from ..enums import RecommendationType
from ..exceptions import NotAcceptable
from ..state import State
from ..step import Step


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


class SecurityIndicatorStep(Step):
    """A step that scores a state based on security info aggregated."""

    _JUSTIFICATION_ADDITION = [
        {"type": "WARNING", "message": ("Package has no gathered information regarding security."),}
    ]

    # Weights for Confidence
    HIGH_CONFIDENCE_WEIGHT = float(os.environ.get("SI_STEP_HIGH_CONFIDENCE_WEIGHT", 1))
    MEDIUM_CONFIDENCE_WEIGHT = float(os.environ.get("SI_STEP_MEDIUM_CONFIDENCE_WEIGHT", 0.5))
    LOW_CONFIDENCE_WEIGHT = float(os.environ.get("SI_STEP_LOW_CONFIDENCE_WEIGHT", 0.1))

    # Weights for Security
    HIGH_SEVERITY_WEIGHT = float(os.environ.get("SI_STEP_HIGH_SEVERITY_WEIGHT", 100))
    MEDIUM_SEVERITY_WEIGHT = float(os.environ.get("SI_STEP_MEDIUM_SEVERITY_WEIGHT", 10))
    LOW_SEVERITY_WEIGHT = float(os.environ.get("SI_STEP_LOW_SEVERITY_WEIGHT", 1))

    # Overall weight for security rewards
    SI_REWARD_WEIGHT = float(os.environ.get("SI_STEP_REWARD_WEIGHT", 0.5))

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register only if we are explicitly recommending secure stacks."""
        if (
            builder_context.recommendation_type == RecommendationType.SECURE
            or builder_context.recommendation_type == RecommendationType.STABLE
        ):
            return {}
        else:
            return None

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Score package based on security indicators gathered, do not include if not analyzed."""
        s_info = self.context.graph.get_si_aggregated_python_package_version(
            package_name=package_version.name,
            package_version=package_version.locked_version,
            index_url=package_version.index,
        )

        if s_info is None:
            if self.context.recommendation_type == RecommendationType.SECURE:
                raise NotAcceptable(
                    f"No security info for {package_version.name}==={package_version.locked_version} "
                    f"on {package_version.index}"
                )
            return 0, self._JUSTIFICATION_ADDITION

        s_score = (
            (
                s_info["severity_high_confidence_high"] * self.HIGH_CONFIDENCE_WEIGHT
                + s_info["severity_high_confidence_medium"] * self.MEDIUM_CONFIDENCE_WEIGHT
                + s_info["severity_high_confidence_low"] * self.LOW_CONFIDENCE_WEIGHT
            )
            * self.HIGH_SEVERITY_WEIGHT
            + (
                s_info["severity_medium_confidence_high"] * self.HIGH_CONFIDENCE_WEIGHT
                + s_info["severity_medium_confidence_medium"] * self.MEDIUM_CONFIDENCE_WEIGHT
                + s_info["severity_medium_confidence_low"] * self.LOW_CONFIDENCE_WEIGHT
            )
            * self.MEDIUM_SEVERITY_WEIGHT
            + (
                s_info["severity_low_confidence_high"] * self.HIGH_CONFIDENCE_WEIGHT
                + s_info["severity_low_confidence_medium"] * self.MEDIUM_CONFIDENCE_WEIGHT
                + s_info["severity_low_confidence_low"] * self.LOW_CONFIDENCE_WEIGHT
            )
            * self.LOW_SEVERITY_WEIGHT
        )

        s_score = s_score / s_info["number_of_lines_with_code_in_python_files"]
        if s_score < 1:
            return self.SI_REWARD_WEIGHT, None
        return self.SI_REWARD_WEIGHT / s_score, None
