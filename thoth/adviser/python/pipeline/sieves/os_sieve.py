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

"""A sieve for filtering out operating systems."""

import logging

from thoth.python import PackageVersion

from ..sieve import Sieve
from ..sieve_context import SieveContext
from ..exceptions import CannotRemovePackage

_LOGGER = logging.getLogger(__name__)


class OperatingSystemSieve(Sieve):
    """Filter out package versions based on operating system in which the given stack runs in."""

    @staticmethod
    def _do_try_exclude(sieve_context: SieveContext, package_version: PackageVersion, config: dict) -> None:
        """Try to exclude the given package, produce warning if exclusion was not successful."""
        try:
            sieve_context.remove_package(package_version)
        except CannotRemovePackage as exc:
            # TODO: this should go to sieve context and be reported to the user in final recommendations
            _LOGGER.warning(
                "Using package %r which was released for different operating system %r, package"
                "cannot be removed: %s",
                package_version.to_tuple(),
                config["os_version"],
                str(exc),
            )

    def run(self, sieve_context: SieveContext) -> None:
        """Filter out package versions based on operating system in which the given stack runs in."""
        if not self.project.runtime_environment.operating_system.name:
            _LOGGER.info("No specific operating system assigned in user's configuration")
            return

        for package_version in list(sieve_context.iter_direct_dependencies()):
            if not self.is_aicoe_release(package_version):
                _LOGGER.debug(
                    "Package %r is not AICoE release - no operating system detection can be done, keeping it",
                    package_version.to_tuple()
                )
                continue

            config = self.get_aicoe_configuration(package_version)
            if not config:
                continue

            if config["os_name"] is None:
                _LOGGER.debug("No specific operating system assigned to %r, keeping it", package_version.to_tuple())
                continue

            if self.project.runtime_environment.operating_system.name != config["os_name"]:
                _LOGGER.debug(
                    "Excluding package %r - package uses operating system %r but user uses %r",
                    package_version.to_tuple(),
                    config["os_name"],
                    self.project.runtime_environment.operating_system.name,
                )
                self._do_try_exclude(sieve_context, package_version, config)
                continue

            user_os_version = self.project.runtime_environment.operating_system.version
            if user_os_version is None:
                _LOGGER.debug(
                    "User version is not specified, keeping package %r",
                    package_version.to_tuple()
                )
                continue

            if user_os_version != config["os_version"]:
                _LOGGER.debug(
                    "Excluding package %r as it has different os version %r than the one expected by the user %r",
                    package_version.to_tuple(),
                    config["os_version"],
                    user_os_version,
                )
                self._do_try_exclude(sieve_context, package_version, config)
                continue

            _LOGGER.debug(
                "Keeping package %r as it has the same operating system configuration as user requested '%s:%s'",
                package_version.to_tuple(),
                config["os_name"],
                config["os_version"],
            )
