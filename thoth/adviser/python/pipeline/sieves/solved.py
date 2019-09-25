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

from thoth.storages.exceptions import NotFoundError

from ..sieve import Sieve
from ..sieve_context import SieveContext

_LOGGER = logging.getLogger(__name__)


class SolvedSieve(Sieve):
    """Filter out build time/installation errors of Python packages."""

    PARAMETERS_DEFAULT = {"without_error": True}

    def run(self, sieve_context: SieveContext) -> None:
        """Filter out packages based on build time/installation issues.."""
        environment = {
            "os_name": self.project.runtime_environment.operating_system.name,
            "os_version": self.project.runtime_environment.operating_system.version,
            "python_version": self.project.runtime_environment.python_version,
        }

        for package_version in list(sieve_context.iter_direct_dependencies()):
            try:
                has_error = self.graph.has_python_solver_error(*package_version.to_tuple(), **environment)
            except NotFoundError as exc:
                _LOGGER.debug(
                    "Removing package %r as it was not by solver: %s",
                    package_version.to_tuple(), str(exc)
                )
                sieve_context.remove_package(package_version)
                continue

            if has_error and self.parameters["without_error"]:
                _LOGGER.debug(
                    "Removing package %r due to build time error on %r",
                    package_version.to_tuple(),
                    environment,
                )
                sieve_context.remove_package(package_version)
