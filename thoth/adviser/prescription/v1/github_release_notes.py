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

from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import TYPE_CHECKING
from packaging.specifiers import SpecifierSet

from thoth.adviser.state import State
from voluptuous import Schema
from voluptuous import Required

from .unit import UnitPrescription
from .schema import PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_RUN_ENTRIES_SCHEMA

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext


@attr.s(slots=True)
class GitHubReleaseNotesWrapPrescription(UnitPrescription):
    """GitHub release notes pipeline unit."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): None,
            Required("release_notes"): PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_RUN_ENTRIES_SCHEMA,
        }
    )

    _configuration = attr.ib(type=Dict[str, Any], kw_only=True)
    _conf_map = attr.ib(type=Dict[str, Dict[str, Any]], init=False, default=attr.Factory(dict))

    @_configuration.default
    def _initialize_default_configuration(self) -> Dict[str, Any]:
        """Initialize default unit configuration based on declared class' default configuration."""
        if self._PRESCRIPTION is None:
            raise ValueError("No assigned prescription on the class level to be set")

        return {
            "package_name": None,
            "release_notes": self._PRESCRIPTION["run"]["release_notes"],
        }

    @staticmethod
    def _construct_release_notes_url(
        organization: str, repository: str, tag_version_prefix: Optional[str], locked_version: str
    ) -> str:
        prefix = tag_version_prefix if tag_version_prefix is not None else ""
        return f"https://github.com/{organization}/{repository}/releases/tag/{prefix}{locked_version}"

    @staticmethod
    def is_wrap_unit_type() -> bool:
        """Check if this unit is of type wrap."""
        return True

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Include this pipeline unit."""
        if not builder_context.is_included(cls):
            prescription: Dict[str, Any] = cls._PRESCRIPTION  # type: ignore
            yield {"release_notes": prescription["run"]["release_notes"]}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize the hash map of the configuration."""
        self._conf_map.clear()
        for entry in self.configuration["release_notes"]:
            self._conf_map[entry["package_version"]["name"]] = entry

    def run(self, state: State) -> None:
        """Add release information to justification for selected packages."""
        justification_addition = []
        for resolved_package_tuple in state.resolved_dependencies.values():
            conf_matched = self._conf_map.get(resolved_package_tuple[0])
            if not conf_matched:
                continue

            version = conf_matched["package_version"].get("version")
            if version is not None and resolved_package_tuple[1] not in SpecifierSet(version):
                continue

            index_url = conf_matched["package_version"].get("index_url")
            if index_url is not None and resolved_package_tuple[2] != index_url:
                continue

            justification_addition.append(
                {
                    "type": "INFO",
                    "message": f"Release notes for package {resolved_package_tuple[0]!r}",
                    "link": self._construct_release_notes_url(
                        organization=conf_matched["organization"],
                        repository=conf_matched["repository"],
                        tag_version_prefix=conf_matched.get("tag_version_prefix"),
                        locked_version=resolved_package_tuple[1],
                    ),
                }
            )

        state.add_justification(justification_addition)
