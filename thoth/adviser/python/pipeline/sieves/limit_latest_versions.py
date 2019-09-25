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

"""Limit latest versions occurring in the software stack."""

import logging

from ..sieve import Sieve
from ..sieve_context import SieveContext

_LOGGER = logging.getLogger(__name__)


class LimitLatestVersionsSieve(Sieve):
    """Limit latest versions occurring in the software stack."""

    PARAMETERS_DEFAULT = {"limit_latest_versions": 5}

    def run(self, sieve_context: SieveContext) -> None:
        """Limit latest versions occurring in the software stack."""
        limit_latest_versions = self._parameters["limit_latest_versions"]

        if limit_latest_versions is None:
            _LOGGER.info("All versions considered")
            return

        if limit_latest_versions < 1:
            raise ValueError(
                "Number of latest versions has to be non-negative number bigger than 0, got %d",
                limit_latest_versions,
            )

        packages_seen_count = dict.fromkeys(sieve_context.packages.keys(), 0)
        for package_version in reversed(list(sieve_context.iter_direct_dependencies())):
            if packages_seen_count[package_version.name] >= self.parameters["limit_latest_versions"]:
                sieve_context.remove_package(package_version)
                continue

            packages_seen_count[package_version.name] += 1
