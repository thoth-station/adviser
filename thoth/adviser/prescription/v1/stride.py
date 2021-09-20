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

"""A base class for implementing strides."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr
from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required

from thoth.adviser.state import State
from .unit import UnitPrescription
from .schema import PRESCRIPTION_STRIDE_RUN_SCHEMA
from .schema import PRESCRIPTION_STRIDE_MATCH_ENTRY_SCHEMA

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext


@attr.s(slots=True)
class StridePrescription(UnitPrescription):
    """Stride base class implementation."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): SchemaAny(str, None),
            Required("match"): PRESCRIPTION_STRIDE_MATCH_ENTRY_SCHEMA,
            Required("run"): PRESCRIPTION_STRIDE_RUN_SCHEMA,
            Required("prescription"): Schema({"run": bool}),
        }
    )

    @staticmethod
    def is_stride_unit_type() -> bool:
        """Check if this unit is of type stride."""
        return True

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if the given pipeline unit should be included in the given pipeline configuration."""
        if cls._should_include_base(builder_context):
            prescription: Dict[str, Any] = cls._PRESCRIPTION  # type: ignore
            yield from cls._yield_should_include_with_state(prescription)
            return None

        yield from ()
        return None

    def run(self, state: State) -> None:
        """Run main entry-point for strides."""
        if not self._run_state(state):
            return None

        try:
            self._run_base()
        finally:
            self._configuration["prescription"]["run"] = True
