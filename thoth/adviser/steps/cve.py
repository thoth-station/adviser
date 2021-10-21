#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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
from typing import Generator
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
    _JUSTIFICATION_LINK_NO_CVE = jl("no_cve")

    _messages_logged = attr.ib(type=Set[Tuple[str, str, str]], factory=set, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Remove CVEs only for advised stacks."""
        if builder_context.is_adviser_pipeline() and not builder_context.is_included(cls):
            if builder_context.recommendation_type in (RecommendationType.LATEST, RecommendationType.TESTING):
                # Report no cve penalization for latest and testing recommendation types.
                yield {"cve_penalization": 0.0}
            else:
                yield {}

            return None

        yield from ()
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
            _LOGGER.warning("Package %r in version %r not found: %r", exc)
            return None

        if cve_records:
            package_version_tuple = package_version.to_tuple()
            _LOGGER.debug("Found a CVEs for %r: %r", package_version_tuple, cve_records)

            if self.context.recommendation_type == RecommendationType.SECURITY:
                if package_version_tuple not in self._messages_logged:
                    self._messages_logged.add(package_version_tuple)
                    for cve_record in cve_records:
                        message = (
                            f"Skipping including package {package_version_tuple!r} as a CVE "
                            f"{cve_record['cve_id']!r} was found"
                        )
                        _LOGGER.warning(
                            "%s: %s",
                            message,
                            cve_record["details"],
                        )

                        self.context.stack_info.append(
                            {"type": "WARNING", "message": message, "link": self._JUSTIFICATION_LINK}
                        )

                raise NotAcceptable
            else:
                justification = []
                for cve_record in cve_records:
                    message = f"Package  {package_version_tuple!r} has a CVE {cve_record['cve_id']!r}"
                    justification.append(
                        {
                            "package_name": package_version.name,
                            "link": self._JUSTIFICATION_LINK,
                            "advisory": cve_record["details"],
                            "message": message,
                            "type": "WARNING",
                        }
                    )

                if self.context.recommendation_type not in (RecommendationType.LATEST, RecommendationType.TESTING):
                    # Penalize only if not latest/testing.
                    penalization = len(cve_records) * self.configuration["cve_penalization"]
                    return max(penalization, -1.0), justification

                return 0.0, justification
        else:
            justification = [
                {
                    "package_name": package_version.name,
                    "link": self._JUSTIFICATION_LINK_NO_CVE,
                    "type": "INFO",
                    "message": f"No known CVE known for {package_version.name!r} in "
                    f"version {package_version.locked_version!r}",
                }
            ]
            return 0.0, justification
