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

"""A base class for implementing package pseudonyms."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

from thoth.python import PackageVersion
from voluptuous import Schema
from voluptuous import Required
import attr

from packaging.specifiers import SpecifierSet
from .unit import UnitPrescription
from .schema import PRESCRIPTION_PSEUDONYM_MATCH_ENTRY_SCHEMA
from .schema import PRESCRIPTION_PSEUDONYM_RUN_SCHEMA

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PseudonymPrescription(UnitPrescription):
    """Pseudonym base class implementation."""

    # Pseudonym is always specific to a package.
    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): str,
            Required("match"): PRESCRIPTION_PSEUDONYM_MATCH_ENTRY_SCHEMA,
            Required("run"): PRESCRIPTION_PSEUDONYM_RUN_SCHEMA,
            Required("prescription"): Schema({"run": bool}),
        }
    )

    _logged = attr.ib(type=bool, kw_only=True, init=False, default=False)
    _specifier = attr.ib(type=Optional[SpecifierSet], kw_only=True, init=False, default=None)
    _index_url = attr.ib(type=Optional[str], kw_only=True, init=False, default=None)

    @staticmethod
    def is_pseudonym_unit_type() -> bool:
        """Check if this unit is of type pseudonym."""
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
        self._logged = False
        super().pre_run()

    def run(self, package_version: PackageVersion) -> Generator[Tuple[str, str, str], None, None]:
        """Run main entry-point for pseudonyms to map packages to their counterparts."""
        if (not self._index_url_check(self._index_url, package_version.index.url)) or (
            self._specifier is not None and package_version.locked_version not in self._specifier
        ):
            yield from ()
            return None

        to_yield = self.run_prescription["yield"]
        to_yield_package_version = to_yield.get("package_version") or {}
        if to_yield.get("yield_matched_version"):
            pseudonym_package_version = package_version.locked_version
        else:
            pseudonym_package_version = to_yield_package_version.get("locked_version")
            if pseudonym_package_version:
                pseudonym_package_version = pseudonym_package_version[2:]

        runtime_environment = self.context.project.runtime_environment
        pseudonyms = self.context.graph.get_solved_python_package_versions_all(
            package_name=to_yield_package_version.get("name"),
            package_version=pseudonym_package_version,
            index_url=to_yield_package_version.get("index_url"),
            count=None,
            os_name=runtime_environment.operating_system.name,
            os_version=runtime_environment.operating_system.version,
            python_version=runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        )

        prescription_conf = self._configuration["prescription"]
        if pseudonyms and not prescription_conf["run"]:
            self._run_stack_info()
            self._run_log()
            prescription_conf["run"] = True

        for pseudonym in pseudonyms:
            _LOGGER.info(
                "%s: Considering package %r as a pseudonym of %r",
                self.get_unit_name(),
                pseudonym,
                package_version.to_tuple(),
            )
            yield pseudonym[0], pseudonym[1], pseudonym[2]
