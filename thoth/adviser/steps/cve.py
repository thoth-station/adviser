#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from thoth.storages.exceptions import NotFoundError

from ..step import Step
from ..state import State

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class CvePenalizationStep(Step):
    """Penalization based on CVE being present in stack."""

    CONFIGURATION_DEFAULT = {"cve_penalization": -0.2}

    @classmethod
    def should_include(
        cls, builder_context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Remove CVEs only for advised stacks."""
        if builder_context.is_adviser_pipeline() and not builder_context.is_included(
            cls
        ):
            return {}

        return None

    def run(
        self, _: State, package_version: PackageVersion
    ) -> Optional[Tuple[float, List[Dict[str, str]]]]:
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
            _LOGGER.debug(
                "Found a CVEs for %r: %r", package_version.to_tuple(), cve_records
            )
            penalization = len(cve_records) * self.configuration["cve_penalization"]
            return penalization, cve_records

        return None
