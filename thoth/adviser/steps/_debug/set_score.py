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

"""A step that is setting score for packages."""

from typing import Any
from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict
from typing import TYPE_CHECKING
import logging

import attr
from thoth.python import PackageVersion
from voluptuous import Schema
from voluptuous import Required

from ...state import State
from ...step import Step


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SetScoreStep(Step):
    """A step that is setting score for packages."""

    # Assign probability is used to "assign" a score to the package to simulate knowledge
    # coverage for packages resolved - 0.75 means ~75% of packages will have a score.
    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): str,
            Required("package_version"): str,
            Required("index_url"): str,
            Required("score"): float,
        }
    )
    CONFIGURATION_DEFAULT: Dict[str, Any] = {
        "package_name": None,
        "package_version": None,
        "index_url": None,
        "score": 0.0,
    }

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, never."""
        return None

    def run(
        self, _: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Score the given package."""
        if (
            package_version.locked_version != self.configuration["package_version"]
            or package_version.index.url != self.configuration["index_url"]
        ):
            return None

        return self.configuration["score"], None
