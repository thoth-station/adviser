#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
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

"""Configuration used for computing recommendations."""

import os
import json

import attr


_DEFAULT_WAREHOUSE = {
    'name': 'pypi',
    'url': 'https://pypi.python.org/simple',
    'verify_ssl': True,
    'warehouse': True
}


@attr.s(slots=True)
class _Configuration:
    """Configuration representation for recommendation engine.

    Accepted environment variables:
      * THOTH_ADVISER_WAREHOUSES - a JSON describing warehouses
    """

    warehouses = attr.ib(type=list)

    @warehouses.default
    def warehouses_default(self):
        from thoth.adviser.python.source import Source

        warehouses = [dict(_DEFAULT_WAREHOUSE)]  # dict() for tests
        if 'THOTH_ADVISER_WAREHOUSES' in os.environ:
            warehouses = json.loads(os.environ['THOTH_ADVISER_WAREHOUSES'])

        return frozenset((Source.from_dict(warehouse) for warehouse in warehouses))


config = _Configuration()
