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

"""A step that is setting score for packages."""

from typing import Any
from typing import Generator
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
from voluptuous import Required
from voluptuous import Schema

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
            Required("multi_package_resolution"): bool,
            Required("package_name"): str,
            SchemaOptional("index_url"): SchemaAny(str, None),
            SchemaOptional("package_version"): SchemaAny(str, None),
            SchemaOptional("score"): SchemaAny(float, None),
        }
    )
    CONFIGURATION_DEFAULT: Dict[str, Any] = {
        "index_url": None,
        "multi_package_resolution": False,
        "package_name": None,
        "package_version": None,
        "score": None,
    }

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, never."""
        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        if self.configuration["score"] is None:
            self.configuration["score"] = random.uniform(self.SCORE_MIN, self.SCORE_MAX)

        super().pre_run()

    def run(
        self, _: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Score the given package."""
        if (
            self.configuration["package_version"] is not None
            and package_version.locked_version != self.configuration["package_version"]
        ) or (
            self.configuration["index_url"] is not None and package_version.index.url != self.configuration["index_url"]
        ):
            return None

        return self.configuration["score"], None
