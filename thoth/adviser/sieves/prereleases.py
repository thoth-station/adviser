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

"""A sieve to filter out pre-releases in direct dependencies."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class CutPreReleasesSieve(Sieve):
    """Cut-off pre-releases if project does not explicitly allows them."""

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include cut-prereleases pipeline sieve for adviser or Dependency Monkey if pre-releases are not allowed."""
        if not builder_context.is_included(cls) and not builder_context.project.prereleases_allowed:
            return {}

        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Cut-off pre-releases if project does not explicitly allows them."""
        for package_version in package_versions:
            if self.context.project.prereleases_allowed:
                _LOGGER.info("Project accepts pre-releases, skipping cutting pre-releases step")
                yield package_version

            if package_version.semantic_version.is_prerelease:
                _LOGGER.debug(
                    "Removing package %s - pre-releases are disabled", package_version.to_tuple(),
                )
                continue

            yield package_version
