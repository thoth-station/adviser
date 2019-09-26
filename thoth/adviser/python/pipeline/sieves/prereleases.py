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

"""A sieve to filter out pre-releases in direct dependencies."""

import logging

from ..sieve import Sieve
from ..sieve_context import SieveContext

_LOGGER = logging.getLogger(__name__)


class CutPreReleasesSieve(Sieve):
    """Cut-off pre-releases if project does not explicitly allows them."""

    def run(self, sieve_context: SieveContext) -> None:
        """Cut-off pre-releases if project does not explicitly allows them."""
        if self.project.prereleases_allowed:
            _LOGGER.info(
                "Project accepts pre-releases, skipping cutting pre-releases step"
            )
            return

        for package_version in list(sieve_context.iter_direct_dependencies()):
            if package_version.semantic_version.prerelease:
                package_tuple = package_version.to_tuple()
                _LOGGER.debug(
                    "Removing package %r - pre-releases are disabled", package_tuple
                )
                sieve_context.remove_package_tuple(package_tuple)
