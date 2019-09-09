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

"""A sieve for filtering out build time/installation errors of Python packages."""

import logging

from ..sieve import Sieve
from ..sieve_context import SieveContext
from ..exceptions import CannotRemovePackage

_LOGGER = logging.getLogger(__name__)


class BuildErrorSieve(Sieve):
    """Filter out build time/installation errors of Python packages."""

    def run(self, sieve_context: SieveContext) -> None:
        """Filter out packages based on build time/installation issues.."""
        for package_version in list(sieve_context.iter_direct_dependencies()):
            try:
                # TODO: implement
                sieve_context.remove_package(package_version)
            except CannotRemovePackage as exc:
                pass
