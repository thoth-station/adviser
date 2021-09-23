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

"""GitHub release notes pipeline unit."""

import attr

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Union
from typing import TYPE_CHECKING
from packaging.specifiers import SpecifierSet

from thoth.adviser.state import State
from voluptuous import Schema
from voluptuous import Required

from .unit import UnitPrescription
from .schema import PRESCRIPTION_GH_RELEASE_NOTES_WRAP_RUN_ENTRY_SCHEMA
from .schema import PACKAGE_VERSION_REQUIRED_NAME_SCHEMA

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class GHReleaseNotesWrapPrescription(UnitPrescription):
    """GitHub release notes pipeline unit."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): str,
            Required("release_notes"): PRESCRIPTION_GH_RELEASE_NOTES_WRAP_RUN_ENTRY_SCHEMA,
            Required("package_version"): PACKAGE_VERSION_REQUIRED_NAME_SCHEMA,
            Required("prescription"): Schema({"run": bool}),
        }
    )

    CONFIGURATION_DEFAULT: Dict[str, Any] = {"package_name": None, "release_notes": None, "package_version": None}

    _configuration = attr.ib(type=Dict[str, Any], kw_only=True, factory=CONFIGURATION_DEFAULT.copy)

    @staticmethod
    def is_wrap_unit_type() -> bool:
        """Check if this unit is of type wrap."""
        return True

    @staticmethod
    def _construct_release_notes_url(
        organization: str, repository: str, tag_version_prefix: Optional[str], locked_version: str
    ) -> str:
        prefix = tag_version_prefix if tag_version_prefix is not None else ""
        return f"https://github.com/{organization}/{repository}/releases/tag/{prefix}{locked_version}"

    @staticmethod
    def _yield_from_resolved_dependencies(
        run_prescription: Dict[str, Any],
        resolved_dependencies_prescription: Union[Dict[str, Any], List[Dict[str, Any]]],
        prescription_conf: Dict[str, Any],
    ) -> Generator[Dict[str, Any], None, None]:
        """Yield configuration based on resolved dependencies prescribed."""
        if isinstance(resolved_dependencies_prescription, list):
            for item in resolved_dependencies_prescription:
                yield {
                    "package_name": item["name"],
                    "release_notes": run_prescription["release_notes"],
                    "package_version": item,
                    "prescription": prescription_conf,
                }
        else:
            yield {
                "package_name": resolved_dependencies_prescription["name"],
                "release_notes": run_prescription["release_notes"],
                "package_version": resolved_dependencies_prescription,
                "prescription": prescription_conf,
            }

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Include this pipeline unit."""
        if not builder_context.is_included(cls):
            prescription: Dict[str, Any] = cls._PRESCRIPTION  # type: ignore

            prescription_conf = {"run": False}
            match = prescription["match"]
            run = prescription["run"]
            if isinstance(match, list):
                for item in match:
                    yield from cls._yield_from_resolved_dependencies(
                        run, item["state"]["resolved_dependencies"], prescription_conf
                    )
            else:
                yield from cls._yield_from_resolved_dependencies(
                    run, match["state"]["resolved_dependencies"], prescription_conf
                )
                return None

        yield from ()
        return None

    def run(self, state: State) -> None:
        """Add release information to justification for selected packages."""
        justification_addition = []
        for resolved_package_tuple in state.resolved_dependencies.values():
            conf_package_version = self.configuration["package_version"]
            if not conf_package_version or resolved_package_tuple[0] != conf_package_version["name"]:
                continue

            version = conf_package_version.get("version")
            if version is not None and resolved_package_tuple[1] not in SpecifierSet(version):
                continue

            develop = conf_package_version.get("develop")
            if develop is not None:
                package_version = self.context.get_package_version(resolved_package_tuple)
                if not package_version:
                    # This is a programming error as the give dependency has to be registered in the context.
                    _LOGGER.error(
                        "No matching package version for %r registered in the context", resolved_package_tuple
                    )
                    continue

                if package_version.develop != develop:
                    continue

            index_url = conf_package_version.get("index_url")
            if not self._index_url_check(index_url, resolved_package_tuple[2]):
                continue

            if self._configuration["prescription"]["run"]:
                # Can happen if prescription states criteria that match multiple times. We add
                # justification only once in such cases.
                continue

            self._configuration["prescription"]["run"] = True

            release_notes_conf = self.configuration["release_notes"]
            justification_addition.append(
                {
                    "type": "INFO",
                    "message": f"Release notes for package {resolved_package_tuple[0]!r}",
                    "link": self._construct_release_notes_url(
                        organization=release_notes_conf["organization"],
                        repository=release_notes_conf["repository"],
                        tag_version_prefix=release_notes_conf.get("tag_version_prefix"),
                        locked_version=resolved_package_tuple[1],
                    ),
                    "package_name": resolved_package_tuple[0],
                }
            )

        state.add_justification(justification_addition)
