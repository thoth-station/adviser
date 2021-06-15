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

"""A base class for implementing steps."""

import abc

import attr
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from voluptuous import Schema
from voluptuous import Required
from voluptuous import Any as SchemaAny
from thoth.python import PackageVersion

from .state import State
from .unit import Unit


@attr.s(slots=True)
class Step(Unit):
    """Step base class implementation.

    Configuration option `multi_package_resolution` states whether a step should be run if package
    is resolved multiple times for the same stack.
    """

    CONFIGURATION_SCHEMA: Schema = Schema(
        {Required("package_name"): SchemaAny(str, None), Required("multi_package_resolution"): bool}
    )
    CONFIGURATION_DEFAULT: Dict[str, Any] = {"package_name": None, "multi_package_resolution": False}

    SCORE_MAX = 1.0
    SCORE_MIN = -1.0

    @staticmethod
    def is_step_unit_type() -> bool:
        """Check if this unit is of type step."""
        return True

    @abc.abstractmethod
    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Run main entry-point for steps to filter and score packages."""
