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

"""A base class for implementing steps."""

import attr
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING
import logging

from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required
from thoth.python import PackageVersion

from thoth.adviser.state import State
from packaging.specifiers import SpecifierSet
from .unit import UnitPrescription
from .schema import PRESCRIPTION_STEP_MATCH_ENTRY_SCHEMA
from .schema import PRESCRIPTION_STEP_RUN_SCHEMA

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class StepPrescription(UnitPrescription):
    """Step base class implementation.

    Configuration option `multi_package_resolution` states whether a step should be run if package
    is resolved multiple times for the same stack.
    """

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): SchemaAny(str, None),
            Required("match"): PRESCRIPTION_STEP_MATCH_ENTRY_SCHEMA,
            Required("multi_package_resolution"): bool,
            Required("run"): PRESCRIPTION_STEP_RUN_SCHEMA,
            Required("prescription"): Schema({"run": bool}),
        }
    )

    SCORE_MAX = 1.0
    SCORE_MIN = -1.0

    _specifier = attr.ib(type=Optional[SpecifierSet], kw_only=True, init=False, default=None)
    _index_url = attr.ib(type=Optional[str], kw_only=True, init=False, default=None)
    _develop = attr.ib(type=Optional[bool], kw_only=True, init=False, default=None)

    @staticmethod
    def is_step_unit_type() -> bool:
        """Check if this unit is of type step."""
        return True

    @staticmethod
    def _yield_should_include(unit_prescription: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Yield for every entry stated in the match field."""
        match = unit_prescription["match"]
        run = unit_prescription["run"]
        prescription_conf = {"run": False}
        if isinstance(match, list):
            for item in match:
                yield {
                    "package_name": item["package_version"].get("name"),
                    "multi_package_resolution": run.get("multi_package_resolution", False),
                    "match": item,
                    "run": run,
                    "prescription": prescription_conf,
                }
        else:
            yield {
                "package_name": match["package_version"].get("name"),
                "multi_package_resolution": run.get("multi_package_resolution", False),
                "match": match,
                "run": run,
                "prescription": prescription_conf,
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
        package_version = self.match_prescription.get("package_version", {})
        version_specifier = package_version.get("version")
        if version_specifier:
            self._specifier = SpecifierSet(version_specifier)

        self._index_url = package_version.get("index_url")
        self._prepare_justification_link(self.run_prescription.get("justification", []))
        self._develop = package_version.get("develop")
        super().pre_run()

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Run main entry-point for steps to filter and score packages."""
        if not self._index_url_check(self._index_url, package_version.index.url):
            return None

        if self._specifier and package_version.locked_version not in self._specifier:
            return None

        if self._develop is not None and package_version.develop != self._develop:
            return None

        if not self._run_state_with_initiator(state, package_version):
            return None

        prescription_conf = self._configuration["prescription"]

        try:
            self._run_base()

            score = self.run_prescription.get("score")
            if not prescription_conf["run"]:
                justification = self.run_prescription.get("justification")
                return score, justification

            # Provide justification just once per prescription.
            return score, None
        finally:
            prescription_conf["run"] = True
