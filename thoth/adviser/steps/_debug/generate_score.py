#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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
from typing import Generator
from typing import Tuple
from typing import List
from typing import Dict
from typing import TYPE_CHECKING
import logging
import random
from pprint import pprint

import attr
from thoth.python import PackageVersion
from voluptuous import Any as SchemaAny
from voluptuous import Optional as SchemaOptional
from voluptuous import Required as SchemaRequired
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
        {
            SchemaOptional("assign_probability"): float,
            SchemaOptional("buffer_size"): int,
            SchemaOptional("package_name"): SchemaAny(str, None),
            SchemaOptional("seed"): int,
            SchemaRequired("multi_package_resolution"): bool,
        }
    )
    CONFIGURATION_DEFAULT: Dict[str, Any] = {
        "assign_probability": 0.75,
        "buffer_size": 1024,
        "multi_package_resolution": False,
        "package_name": None,
        "seed": 42,
    }

    _history = attr.ib(type=Dict[Tuple[str, str, str], float], factory=dict, init=False)
    _buffer = attr.ib(type=List[float], factory=list, init=False)
    _idx = attr.ib(type=int, default=0, init=False)

    def pre_run(self) -> None:
        """Initialize this pipeline units before each run."""
        self._history.clear()
        self._idx = 0

        if not self._buffer:
            state = random.getstate()
            random.seed(self.configuration["seed"])
            self._buffer = [0.0] * self.configuration["buffer_size"]
            for i in range(self.configuration["buffer_size"]):
                self._buffer[i] = (
                    random.uniform(self.SCORE_MIN, self.SCORE_MAX)
                    if random.random() <= self.configuration["assign_probability"]
                    else 0.0
                )
            random.setstate(state)

        super().pre_run()

    def post_run(self) -> None:
        """Print the generated scores on finish to stdout."""
        pprint(self._history)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, never."""
        yield from ()
        return None

    def run(
        self, _: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Score the given package."""
        package_tuple = package_version.to_tuple()
        score = self._history.get(package_tuple)

        if score is not None:
            return score, None

        idx = self._idx
        self._idx = (self._idx + 1) % self.configuration["buffer_size"]
        self._history[package_tuple] = self._buffer[idx]
        return self._buffer[idx], None
