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

"""A step to prioritize releases from AICoE."""

import logging

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion

from ..enums import RecommendationType
from ..step import Step
from ..state import State

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class AICoEReleasesStep(Step):
    """Prioritize releases from AICoE."""

    _SCORE_ADDITION = 0.1
    _JUSTIFICATION = [{"type": "INFO", "message": "Builds produced by AICoE are optimized for performance"}]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, for non-latest adviser runs."""
        if not builder_context.is_adviser_pipeline():
            return None

        if builder_context.recommendation_type == RecommendationType.LATEST:
            return None

        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self, _: State, package_version: PackageVersion) -> Optional[Tuple[float, List[Dict[str, str]]]]:
        """Prioritize releases from AICoE."""
        if self.is_aicoe_release(package_version):
            return self._SCORE_ADDITION, self._JUSTIFICATION

        return None
