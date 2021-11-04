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

"""Sieve packages with CVE when recommendation type is set to security."""

import logging

from typing import Any
from typing import Dict
from typing import Generator
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion
from thoth.storages.exceptions import NotFoundError
from voluptuous import Required
from voluptuous import Schema

from ..enums import RecommendationType
from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class CveSieve(Sieve):
    """Filter out packages with CVEs."""

    CONFIGURATION_DEFAULT = {"package_name": None}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): None,
        }
    )
    _JUSTIFICATION_LINK = jl("cve")

    _messages_logged = attr.ib(type=Set[Tuple[str, str, str]], factory=set, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Remove CVEs only secure stacks."""
        if (
            builder_context.is_adviser_pipeline()
            and not builder_context.is_included(cls)
            and builder_context.recommendation_type == RecommendationType.SECURITY
        ):
            yield {}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before running."""
        self._messages_logged.clear()
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out packages with a CVE."""
        for package_version in package_versions:
            try:
                cve_records = self.context.graph.get_python_cve_records_all(
                    package_name=package_version.name,
                    package_version=package_version.locked_version,
                )
            except NotFoundError as exc:
                _LOGGER.warning("Package %r in version %r not found: %r", exc)
                continue

            if not cve_records:
                yield package_version
                continue

            package_version_tuple = package_version.to_tuple()
            _LOGGER.debug("Found a CVEs for %r: %r", package_version_tuple, cve_records)

            if package_version_tuple not in self._messages_logged:
                self._messages_logged.add(package_version_tuple)
                for cve_record in cve_records:
                    message = (
                        f"Skipping including package {package_version_tuple!r} as a CVE "
                        f"{cve_record['cve_id']!r} was found"
                    )
                    _LOGGER.warning(message)
                    self.context.stack_info.append(
                        {
                            "type": "WARNING",
                            "message": message,
                            "link": cve_record.get("link") or self._JUSTIFICATION_LINK,
                        }
                    )
