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

"""Sort direct dependencies based on semver."""

import logging

from ..sieve import Sieve
from ..sieve_context import SieveContext
from thoth.adviser.python.pipeline.units import semver_cmp_package_version

_LOGGER = logging.getLogger(__name__)


class SemverSortSieve(Sieve):
    """Sort direct dependencies based on semver."""

    def run(self, sieve_context: SieveContext) -> None:
        """Sort direct dependencies based on semantic version."""
        sieve_context.sort_packages(semver_cmp_package_version, reverse=False)
