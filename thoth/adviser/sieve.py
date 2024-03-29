#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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

"""A base class for implementing sieves."""

import abc
from typing import Generator

import attr
from thoth.python import PackageVersion

from .unit import Unit


@attr.s(slots=True)
class Sieve(Unit):
    """Sieve base class implementation."""

    @staticmethod
    def is_sieve_unit_type() -> bool:
        """Check if this unit is of type sieve."""
        return True

    @abc.abstractmethod
    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Run main entry-point for sieves to filter and score packages."""
