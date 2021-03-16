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

from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import TYPE_CHECKING
import logging

import attr
from thoth.python import PackageVersion

from packaging.specifiers import SpecifierSet
from .unit import UnitPrescription

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SievePrescription(UnitPrescription):
    """Sieve base class implementation."""

    _logged = attr.ib(type=bool, kw_only=True, init=False, default=False)
    _specifier = attr.ib(type=Optional[SpecifierSet], kw_only=True, init=False, default=None)
    _index_url = attr.ib(type=Optional[str], kw_only=True, init=False, default=None)

    @staticmethod
    def is_sieve_unit_type() -> bool:
        """Check if this unit is of type sieve."""
        return True

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if the given pipeline unit should be included in the given pipeline configuration."""
        if cls._should_include_base(builder_context):
            run_prescription: Dict[str, Any] = cls._PRESCRIPTION["run"]  # type: ignore
            yield {"package_version": run_prescription["package_version"].get("name")}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Prepare before running this pipeline unit."""
        version_specifier = self.run_prescription["match"]["package_version"].get("version")
        if version_specifier:
            self._specifier = SpecifierSet(version_specifier)
            self._specifier.prereleases = True

        self._index_url = self.run_prescription["match"]["package_version"].get("index_url")
        self._logged = False
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Run main entry-point for sieves to filter and score packages."""
        for package_version in package_versions:
            if (not self._specifier or package_version.locked_version in self._specifier) and (
                not self._index_url or package_version.index.url == self._index_url
            ):
                if not self._logged:
                    self._logged = True
                    self._run_log()
                    self._run_stack_info()

                continue

            yield package_version
