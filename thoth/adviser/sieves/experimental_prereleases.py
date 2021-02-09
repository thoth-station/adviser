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

"""A sieve to filter out pre-releases, selectively."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from voluptuous import Schema
from voluptuous import Required

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SelectiveCutPreReleasesSieve(Sieve):
    """Enable or disable specific pre-releases for the given set of packages.."""

    CONFIGURATION_DEFAULT = {"package_name": None, "allow_prereleases": None}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {Required("package_name"): None, Required("allow_prereleases"): Schema({str: bool})}
    )

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Enable or disable specific pre-releases for the given set of packages.."""
        if builder_context.project.prereleases_allowed:
            if builder_context.project.prereleases_allowed:
                msg = "Ignoring selective pre-releases in [thoth] section as global allow_prereleases flag is set"
                _LOGGER.warning(msg)

            return None

        if (
            builder_context.is_included(cls)
            or not builder_context.project.pipfile.thoth
            or not builder_context.project.pipfile.thoth.allow_prereleases
        ):
            return None

        return {
            "package_name": None,
            "allow_prereleases": builder_context.project.pipfile.thoth.allow_prereleases,
        }

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Cut-off pre-releases if project does not explicitly allows them."""
        for package_version in package_versions:
            if not self.configuration["allow_prereleases"].get(package_version.name, False):
                if package_version.semantic_version.is_prerelease:
                    _LOGGER.debug(
                        "Removing package %s - pre-releases are disabled",
                        package_version.to_tuple(),
                    )
                    continue

            yield package_version
