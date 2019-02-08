#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019 Fridolin Pokorny
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

"""Representation of a configuration entry collapsing hardware, runtime and other information."""

import logging

import attr
import click

from .hardware_information import HardwareInformation
from .operating_system import OperatingSystem
from .runtime_environment import RuntimeEnvironment

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class ConfigEntry:
    """An entry collapsing configuration options in the user configuration file."""

    hardware_information = attr.ib(type=HardwareInformation)
    operating_system = attr.ib(type=OperatingSystem)
    runtime_environment = attr.ib(type=RuntimeEnvironment)

    _TERMINAL_SIZE = 80

    @classmethod
    def from_dict(cls, dict_: dict):
        """Parse one configuration entry from a dictionary."""
        dict_ = dict(dict_)

        hardware_information = dict_.pop("hardware_information", {})
        operating_system = dict_.pop("operating_system", {})
        runtime_environment = dict_.pop("runtime_environment", {})

        for key, value in dict_.values():
            _LOGGER.warning(
                "Unknown configuration entry in the configuration file %s with value %s",
                key,
                value
            )

        instance = cls(
            hardware_information=HardwareInformation.from_dict(hardware_information),
            operating_system=OperatingSystem.from_dict(operating_system),
            runtime_environment=RuntimeEnvironment.from_dict(runtime_environment),
        )
        return instance

    def to_dict(self):
        """Convert configuration to a dict representation."""
        return attr.asdict(self)

    def report(self, message: str = None) -> None:
        """Report configuration to user."""
        if message is not None:
            click.echo(message)

        self.hardware_information.report()
        self.operating_system.report()
        self.runtime_environment.report()
