#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Penalize stacks with a CVE."""

import logging

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion
from thoth.storages.exceptions import NotFoundError
from voluptuous import Required
from voluptuous import Schema

from ..exceptions import NotAcceptable
from ..enums import RecommendationType
from ..step import Step
from ..state import State

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class CvePenalizationStep(Step):
    """Penalization based on CVE being present in stack."""

    CONFIGURATION_DEFAULT = {"package_name": None, "cve_penalization": -0.2, "multi_package_resolution": False}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): None,
            Required("cve_penalization"): float,
            Required("multi_package_resolution"): False,
        }
    )
    _JUSTIFICATION_LINK = jl("cve")

    _messages_logged = attr.ib(type=Set[Tuple[str, str, str]], factory=set, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Remove CVEs only for advised stacks."""
        if not builder_context.is_adviser_pipeline():
            return None

        if builder_context.recommendation_type == RecommendationType.LATEST:
            return None

        if not builder_context.is_included(cls):
            return {}

        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before running."""
        self._messages_logged.clear()
        super().pre_run()

    def run(self, _: State, package_version: PackageVersion) -> Optional[Tuple[float, List[Dict[str, str]]]]:
        """Penalize stacks with a CVE."""
        try:
            cve_records = self.context.graph.get_python_cve_records_all(
                package_name=package_version.name,
                package_version=package_version.locked_version,
            )
        except NotFoundError as exc:
            _LOGGER.warning("Package %r in version %r not found: %r", str(exc))
            return None

        if cve_records:
            package_version_tuple = package_version.to_tuple()
            _LOGGER.debug("Found a CVEs for %r: %r", package_version_tuple, cve_records)

            if self.context.recommendation_type == RecommendationType.SECURITY:
                if package_version_tuple not in self._messages_logged:
                    self._messages_logged.add(package_version_tuple)
                    for cve_record in cve_records:
                        _LOGGER.warning(
                            "Skipping including package %r as a CVE %s was found: %s",
                            package_version_tuple,
                            cve_record.get("cve_name") or cve_record.get("cve_id"),
                            cve_record["advisory"],
                        )

                raise NotAcceptable

            penalization = len(cve_records) * self.configuration["cve_penalization"]

            # Note down package causing this CVE.
            for record in cve_records:
                record["package_name"] = package_version.name
                record["link"] = self._JUSTIFICATION_LINK

            return penalization, cve_records

        return None
