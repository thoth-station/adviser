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
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING
import logging

import attr
from thoth.python import PackageVersion

from ..enums import RecommendationType
from ..exceptions import NotAcceptable
from ..state import State
from ..step import Step


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SecurityIndicatorStep(Step):
    """A step that scores a state based on security info aggregated."""

    _logged_packages = attr.ib(type=Set[Tuple[str, str, str]], default=attr.Factory(set), init=False)

    CONFIGURATION_DEFAULT = {
        "high_confidence_weight": 1,
        "medium_confidence_weight": 0.5,
        "low_confidence_weight": 0.1,
        "high_severity_weight": 100,
        "medium_severity_weight": 10,
        "low_severity_weight": 1,
        "si_reward_weight": 0.5,
    }

    def pre_run(self) -> None:
        """Initialize this pipeline step before running the pipeline."""
        self._logged_packages.clear()

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register only if we are explicitly recommending secure stacks."""
        if (
            builder_context.recommendation_type == RecommendationType.SECURITY
            or builder_context.recommendation_type == RecommendationType.STABLE
        ) and not builder_context.is_included(cls):
            return {}

        return None

    @staticmethod
    def _generate_justification(name: str, version: str, index: str) -> List[Dict[str, Any]]:
        return [
            {
                "type": "WARNING",
                "message": f"{name}==={version} on {index} has no gathered information regarding security.",
            }
        ]

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Score package based on security indicators gathered, do not include if not analyzed."""
        s_info = self.context.graph.get_si_aggregated_python_package_version(
            package_name=package_version.name,
            package_version=package_version.locked_version,
            index_url=package_version.index.url,
        )

        if s_info is None:
            if self.context.recommendation_type == RecommendationType.SECURITY:
                package_version_tuple = package_version.to_tuple_locked()
                if package_version_tuple not in self._logged_packages:
                    self._logged_packages.add(package_version_tuple)
                    _LOGGER.warning(
                        "No security info for %s===%s on %s",
                        package_version.name,
                        package_version.locked_version,
                        package_version.index.url,
                    )
                raise NotAcceptable
            return (
                0,
                self._generate_justification(
                    name=package_version.name, version=package_version.locked_version, index=package_version.index.url
                ),
            )

        s_score = (
            (
                s_info["severity_high_confidence_high"] * self.configuration["high_confidence_weight"]
                + s_info["severity_high_confidence_medium"] * self.configuration["medium_confidence_weight"]
                + s_info["severity_high_confidence_low"] * self.configuration["low_confidence_weight"]
            )
            * self.configuration["high_severity_weight"]
            + (
                s_info["severity_medium_confidence_high"] * self.configuration["high_confidence_weight"]
                + s_info["severity_medium_confidence_medium"] * self.configuration["medium_confidence_weight"]
                + s_info["severity_medium_confidence_low"] * self.configuration["low_confidence_weight"]
            )
            * self.configuration["medium_severity_weight"]
            + (
                s_info["severity_low_confidence_high"] * self.configuration["high_confidence_weight"]
                + s_info["severity_low_confidence_medium"] * self.configuration["medium_confidence_weight"]
                + s_info["severity_low_confidence_low"] * self.configuration["low_confidence_weight"]
            )
            * self.configuration["low_severity_weight"]
        )

        s_score = s_score / s_info["number_of_lines_with_code_in_python_files"]
        if s_score < 1:
            return self.configuration["si_reward_weight"], None
        return self.configuration["si_reward_weight"] / s_score, None
