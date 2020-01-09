#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019, 2020 Fridolin Pokorny
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

"""Routines for dependency monkey and its output handling."""

import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import attr

from .product import Product


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class DependencyMonkeyReport:
    """Report produced by a Dependency Monkey run."""

    skipped = attr.ib(type=int, default=0)
    _responses = attr.ib(
        type=List[Dict[str, Union[Dict[str, Any], str]]], default=attr.Factory(list)
    )

    def add_response(self, response: str, product: Product) -> None:
        """Add a new response to response listing."""
        self._responses.append({"response": response, "product": product.to_dict()})

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to a dict representation suitable for serialization."""
        return {"skipped": self.skipped, "responses": self._responses}
