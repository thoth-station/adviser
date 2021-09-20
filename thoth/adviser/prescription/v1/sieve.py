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

"""A base class for implementing sieves."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import TYPE_CHECKING
import logging

import attr
from thoth.python import PackageVersion
from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required

from packaging.specifiers import SpecifierSet
from .unit import UnitPrescription
from .schema import PRESCRIPTION_SIEVE_MATCH_ENTRY_SCHEMA
from .schema import PRESCRIPTION_SIEVE_RUN_SCHEMA

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SievePrescription(UnitPrescription):
    """Sieve base class implementation."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): SchemaAny(str, None),
            Required("match"): PRESCRIPTION_SIEVE_MATCH_ENTRY_SCHEMA,
            Required("run"): SchemaAny(PRESCRIPTION_SIEVE_RUN_SCHEMA, None),
            Required("prescription"): Schema({"run": bool}),
        }
    )

    _specifier = attr.ib(type=Optional[SpecifierSet], kw_only=True, init=False, default=None)
    _index_url = attr.ib(type=Optional[str], kw_only=True, init=False, default=None)
    _develop = attr.ib(type=Optional[str], kw_only=True, init=False, default=None)

    @staticmethod
    def is_sieve_unit_type() -> bool:
        """Check if this unit is of type sieve."""
        return True

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
            self._specifier.prereleases = True

        self._index_url = package_version.get("index_url")
        self._develop = package_version.get("develop")
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Run main entry-point for sieves to filter and score packages."""
        prescription_conf = self._configuration["prescription"]
        for package_version in package_versions:
            if (
                (not self._specifier or package_version.locked_version in self._specifier)
                and self._index_url_check(self._index_url, package_version.index.url)
                and (self._develop is None or self._develop == package_version.develop)
            ):

                if not prescription_conf["run"]:
                    self._run_log()
                    self._run_stack_info()
                    prescription_conf["run"] = True

                continue

            yield package_version
