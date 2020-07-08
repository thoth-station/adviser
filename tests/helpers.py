#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Helpers for the testsuite and adviser implementation."""

import sys
import functools
from typing import Any

import tests.units as units
import thoth.adviser


def use_test_units(func: Any) -> Any:
    """Substitute implemented units in adviser implementation with the ones provided by testsuite."""
    # noqa
    @functools.wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        """Substitute implemented units with the testing ones."""
        sys.modules["thoth.adviser"].boots = units.boots
        sys.modules["thoth.adviser.boots"] = units.boots
        sys.modules["thoth.adviser"].sieves = units.sieves
        sys.modules["thoth.adviser.sieves"] = units.sieves
        sys.modules["thoth.adviser"].steps = units.steps
        sys.modules["thoth.adviser.steps"] = units.steps
        sys.modules["thoth.adviser"].strides = units.strides
        sys.modules["thoth.adviser.strides"] = units.strides
        sys.modules["thoth.adviser"].wraps = units.wraps
        sys.modules["thoth.adviser.wraps"] = units.wraps
        try:
            return func(*args, **kwargs)
        finally:
            sys.modules["thoth.adviser"].boots = thoth.adviser.boots
            sys.modules["thoth.adviser.boots"] = thoth.adviser.boots
            sys.modules["thoth.adviser"].sieves = thoth.adviser.sieves
            sys.modules["thoth.adviser.sieves"] = thoth.adviser.sieves
            sys.modules["thoth.adviser"].steps = thoth.adviser.steps
            sys.modules["thoth.adviser.steps"] = thoth.adviser.steps
            sys.modules["thoth.adviser"].strides = thoth.adviser.strides
            sys.modules["thoth.adviser.strides"] = thoth.adviser.strides
            sys.modules["thoth.adviser"].wraps = thoth.adviser.wraps
            sys.modules["thoth.adviser.wraps"] = thoth.adviser.wraps

    return wrapped
