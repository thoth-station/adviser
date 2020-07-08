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

"""Tests exceptions provided by thoth-adviser implementation."""


import inspect
from .base import AdviserTestCase

import thoth.adviser.exceptions as exceptions
from thoth.adviser.exceptions import AdviserException


class TestExceptions(AdviserTestCase):
    """Test exceptions provided by thoth-adviser."""

    def test_exception_hierarchy(self) -> None:
        """Test exception hierarchy in thoth-adviser implementation."""
        for name, item in exceptions.__dict__.items():
            if not inspect.isclass(item):
                continue

            if issubclass(item, AdviserException):
                assert issubclass(item, AdviserException), f"Exception {name!r} is not of type AdviserException"
