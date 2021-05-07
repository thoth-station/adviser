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

"""A step prescription class implementing skipping a package in a dependency graph."""

import attr
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Generator
from typing import Tuple
from typing import TYPE_CHECKING
import logging

from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required
from thoth.python import PackageVersion

from thoth.adviser.state import State
from thoth.adviser.exceptions import SkipPackage
from .unit import UnitPrescription
from .schema import PRESCRIPTION_SKIP_PACKAGE_STEP_RUN_SCHEMA
from .schema import PRESCRIPTION_SKIP_PACKAGE_STEP_MATCH_ENTRY_SCHEMA

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SkipPackageStepPrescription(UnitPrescription):
    """A step prescription class implementing skipping a package in a dependency graph."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): SchemaAny(str, None),
            Required("multi_package_resolution"): bool,
            Required("run"): SchemaAny(PRESCRIPTION_SKIP_PACKAGE_STEP_RUN_SCHEMA, None),
            Required("match"): PRESCRIPTION_SKIP_PACKAGE_STEP_MATCH_ENTRY_SCHEMA,
        }
    )

    _logged = attr.ib(type=bool, default=False, init=False, kw_only=True)

    @staticmethod
    def is_step_unit_type() -> bool:
        """Check if this unit is of type step."""
        return True

    @staticmethod
    def _yield_should_include(unit_prescription: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Yield for every entry stated in the match field."""
        match = unit_prescription["match"]
        run = unit_prescription["run"]
        if isinstance(match, list):
            for item in match:
                yield {
                    "package_name": item["package_name"],
                    "multi_package_resolution": False,
                    "match": item,
                    "run": run,
                }
        else:
            yield {
                "package_name": match["package_name"],
                "multi_package_resolution": False,
                "match": match,
                "run": run,
            }

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if the given pipeline unit should be included in the given pipeline configuration."""
        if cls._should_include_base(builder_context):
            prescription: Dict[str, Any] = cls._PRESCRIPTION  # type: ignore
            yield from cls._yield_should_include(prescription)
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Prepare before running this pipeline unit."""
        self._logged = False
        super().pre_run()

    def run(self, state: State, _: PackageVersion) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Run main entry-point for steps to skip a package."""
        if not self._run_state(state):
            return None

        # XXX: we might want to do more sophisticated logic here - it would be great to check
        # if the package removed was introduced only by an expected package and such
        if not self._logged:
            self._logged = True
            self._run_log()
            self._run_stack_info()

        raise SkipPackage
