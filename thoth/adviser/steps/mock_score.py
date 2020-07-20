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

"""A step designed to mock scoring - testing purposes."""

import operator
import random
import sys

from typing import Any
from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict
from typing import TYPE_CHECKING
import logging

import attr
from thoth.python import PackageVersion

from ..state import State
from ..step import Step


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class MockScoreStep(Step):
    """A step that is mocking scoring of packages."""

    _score_history = attr.ib(type=Dict[Tuple[str, str, str], float], factory=dict, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, never."""
        return None

    def pre_run(self) -> None:
        """Initialize self, before each run."""
        self._score_history.clear()

    def post_run(self) -> None:
        """Print the generated history after the run."""
        packages = {}  # type: Dict[Any, Any]
        for key, value in self._score_history.items():
            packages.setdefault(key[0], []).append((key, value))

        for key, value in packages.items():
            packages[key] = sorted(value, key=operator.itemgetter(1), reverse=True)  # type: ignore

        print("-" * 10, " Mock score report ", "-" * 10, file=sys.stderr)
        for key in sorted(packages):
            print(key, file=sys.stderr)
            for entry in packages[key]:
                print(f"{str((entry[0][1], entry[0][2])):>50} | {entry[1]:+f}", file=sys.stderr)
        print("-" * 40, file=sys.stderr)

    def run(
        self, _: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Score the given package regardless of the state."""
        # Using seed set to process on the adviser run affects this call - so adviser
        # with same seed set shared scores generated across runs.
        score = self._score_history.setdefault(package_version.to_tuple(), random.uniform(-1.0, 1.0))
        return score, None
