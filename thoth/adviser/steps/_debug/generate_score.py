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

"""A step that is assigning scores in a deterministic way."""

from typing import Any
from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict
from typing import TYPE_CHECKING
import logging
import random

import attr
from thoth.python import PackageVersion
from voluptuous import Any as SchemaAny
from voluptuous import Optional as SchemaOptional
from voluptuous import Schema

from ...state import State
from ...step import Step


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class GenerateScoreStep(Step):
    """A step that is assigning scores in a deterministic way.

    This unit can be used to measure assigning score in a deterministic way across multiple runs without
    a need to store all the score for packages.
    """

    # Assign probability is used to "assign" a score to the package to simulate knowledge
    # coverage for packages resolved - 0.75 means ~75% of packages will have a score.
    CONFIGURATION_SCHEMA: Schema = Schema(
        {SchemaOptional("package_name"): SchemaAny(str, None), SchemaOptional("assign_probability"): float}
    )
    CONFIGURATION_DEFAULT: Dict[str, Any] = {"package_name": None, "assign_probability": 0.75}

    _history = attr.ib(type=Dict[Tuple[str, str, str], float], factory=dict, init=False)

    def pre_run(self) -> None:
        """Initialize this pipeline units before each run."""
        self._history.clear()
        super().pre_run()

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, never."""
        return None

    def run(
        self, _: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Score the given package."""
        package_tuple = package_version.to_tuple()
        score = self._history.get(package_tuple)

        if score is not None:
            return score, None

        if random.random() < self.configuration["assign_probability"]:
            self._history[package_tuple] = 0.0
            return 0.0, None

        old_state = random.getstate()
        random.seed(",".join(package_tuple))
        score = random.uniform(self.SCORE_MIN, self.SCORE_MAX)
        random.setstate(old_state)
        return score, None
