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

"""Representation of an unsolved package in dependency graph."""

from typing import Tuple

import attr


@attr.s(slots=True)
class UnsolvedPackage:
    """Representation of an unsolved package in the dependency graph."""

    package_name = attr.ib(type=str)
    package_version = attr.ib(type=str, default=None)
    develop = attr.ib(type=bool, default=False)

    def to_tuple(self) -> Tuple[str, str, None]:
        """Convert this package to a tuple representation.

        To be fully compliant with PackageVersion, provide None index explictly
        """
        return self.package_name, self.package_version, None
