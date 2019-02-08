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

"""A base class for configuration entries."""

import logging

import click
import attr
from texttable import Texttable

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class ConfigEntryBase:
    """A base class for configuration entries."""

    _TYPE = None
    _TERMINAL_WIDTH = 80

    @classmethod
    def from_dict(cls, dict_: dict):
        """Instantiate hardware related information from its dictionary representation."""
        dict_ = dict(dict_)

        constructor_kwargs = {}
        for attribute in cls.__attrs_attrs__:
            constructor_kwargs[attribute.name] = dict_.pop(attribute.name, None)

        for key, value in dict_.items():
            _LOGGER.warning("Unsupported %s configuration option %r with value %r", cls._TYPE, key, value)

        instance = cls(**constructor_kwargs)
        return instance

    def to_dict(self) -> dict:
        """Convert runtime environment object representation to a dict."""
        return attr.asdict(self)

    def report(self) -> None:
        """Create report for this configuration entry."""
        click.echo("\n\t== %s ==\n" % self._TYPE.capitalize())
        table = Texttable(max_width=self._TERMINAL_WIDTH)
        table.set_deco(Texttable.HLINES | Texttable.VLINES)

        for key, value in self.to_dict().items():
            table.add_row([key, value])

        click.echo(table.draw())
