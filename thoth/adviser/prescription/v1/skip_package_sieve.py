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

"""A prescription sieve implementing skipping a package in a dependency graph."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING
import logging

import attr
from thoth.python import PackageVersion
from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required

from .unit import UnitPrescription
from .schema import PRESCRIPTION_SKIP_PACKAGE_SIEVE_RUN_ENTRY_SCHEMA
from .schema import PRESCRIPTION_SKIP_PACKAGE_SIEVE_MATCH_ENTRY_SCHEMA

from ...exceptions import SkipPackage

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SkipPackageSievePrescription(UnitPrescription):
    """Skip package sieve prescription unit implementation."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): SchemaAny(str, None),
            Required("run"): SchemaAny(PRESCRIPTION_SKIP_PACKAGE_SIEVE_RUN_ENTRY_SCHEMA, None),
            Required("match"): PRESCRIPTION_SKIP_PACKAGE_SIEVE_MATCH_ENTRY_SCHEMA,
            Required("prescription"): Schema({"run": bool}),
        }
    )

    @staticmethod
    def is_sieve_unit_type() -> bool:
        """Check if this unit is of type sieve."""
        return True

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if the given pipeline unit should be included in the given pipeline configuration."""
        if cls._should_include_base(builder_context):
            prescription: Dict[str, Any] = cls._PRESCRIPTION  # type: ignore
            prescription_conf = {"run": False}
            if isinstance(prescription["match"], list):
                for item in prescription["match"]:
                    yield {
                        "package_name": item["package_name"],
                        "run": prescription.get("run"),
                        "match": item,
                        "prescription": prescription_conf,
                    }
            else:
                yield {
                    "package_name": prescription["match"]["package_name"],
                    "run": prescription.get("run"),
                    "match": prescription["match"],
                    "prescription": prescription_conf,
                }
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize this unit before each run."""
        super().pre_run()

    def run(self, _: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Run main entry-point for sieves to filter and score packages."""
        prescription_conf = self._configuration["prescription"]
        if not prescription_conf["run"]:
            self._run_log()
            self._run_stack_info()
            prescription_conf["run"] = True

        raise SkipPackage
