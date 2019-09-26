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

"""A sieve for filtering out disabled Python package indexes."""

import logging

from ..sieve import Sieve
from ..sieve_context import SieveContext
from ..exceptions import CannotRemovePackage

_LOGGER = logging.getLogger(__name__)


class PackageIndexSieve(Sieve):
    """Filter out disabled Python package indexes."""

    def run(self, sieve_context: SieveContext) -> None:
        """Filter out package versions based on disabled Python package index."""
        for package_version in list(sieve_context.iter_direct_dependencies()):
            if not self.graph.is_python_package_index_enabled(package_version.index.url):
                _LOGGER.debug(
                    "Removing Python package version %r as used index is not enabled",
                    package_version.to_tuple()
                )
                try:
                    sieve_context.remove_package(package_version)
                except CannotRemovePackage as exc:
                    _LOGGER.error(
                        "Cannot remove package %r due to Python package index filtering: %s",
                        package_version.to_tuple(),
                        str(exc)
                    )
                    raise
