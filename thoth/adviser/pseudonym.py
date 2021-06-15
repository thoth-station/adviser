#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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

"""A base class for implementing package pseudonyms."""

import abc
from typing import Generator
from typing import Tuple

from thoth.python import PackageVersion
from voluptuous import Schema
from voluptuous import Required
import attr

from .unit import Unit


@attr.s(slots=True)
class Pseudonym(Unit):
    """Pseudonym base class implementation."""

    # Pseudonym is always specific to a package.
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): str})

    @staticmethod
    def is_pseudonym_unit_type() -> bool:
        """Check if this unit is of type pseudonym."""
        return True

    @abc.abstractmethod
    def run(self, package_version: PackageVersion) -> Generator[Tuple[str, str, str], None, None]:
        """Run main entry-point for pseudonyms to map packages to their counterparts."""
