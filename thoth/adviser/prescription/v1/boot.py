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

"""A prescription for boot units."""

import attr

from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING
from voluptuous import Schema
from voluptuous import Any as SchemaAny
from voluptuous import Required

from .unit import UnitPrescription
from .schema import PRESCRIPTION_BOOT_RUN_SCHEMA
from .schema import PRESCRIPTION_BOOT_MATCH_ENTRY_SCHEMA


if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext


@attr.s(slots=True)
class BootPrescription(UnitPrescription):
    """Boot prescription implementation."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): SchemaAny(str, None),
            Required("match"): SchemaAny(PRESCRIPTION_BOOT_MATCH_ENTRY_SCHEMA, None),
            Required("run"): PRESCRIPTION_BOOT_RUN_SCHEMA,
            Required("prescription"): Schema({"run": bool}),
        }
    )

    @staticmethod
    def is_boot_unit_type() -> bool:
        """Check if this unit is of type boot."""
        return True

    @staticmethod
    def _yield_should_include(unit_prescription: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Yield for every entry stated in the match field."""
        match = unit_prescription.get("match", {})
        run = unit_prescription.get("run", {})
        prescription_conf = {"run": False}
        if isinstance(match, list):
            for item in match:
                yield {
                    "package_name": item.get("package_name"),
                    "match": item,
                    "run": run,
                    "prescription": prescription_conf,
                }
        else:
            yield {
                "package_name": match.get("package_name") if match else None,
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

    def run(self) -> None:
        """Run main entry-point for boot units."""
        try:
            super()._run_base()
        finally:
            self._configuration["prescription"]["run"] = True
