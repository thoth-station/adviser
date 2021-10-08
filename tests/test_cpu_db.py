#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""Tests related to CPU database."""

import pytest

from thoth.adviser.cpu_db import CPUDatabase

from .base import AdviserTestCase


class TestCPUDatabase(AdviserTestCase):
    """Test CPU database."""

    def test_init(self) -> None:
        """Test initializing the database."""
        assert "avx2" in CPUDatabase.get_known_flags()
        assert "avx512" in CPUDatabase.get_known_flags()

    @pytest.mark.parametrize(
        "cpu_family,cpu_model,flag,is_provided",
        [
            (6, int("0x5", base=16), "avx2", True),
            (6, int("0xC", base=16), "avx512", True),
            (999, 0xBAAAAAAD, "avx512", False),
            (12345, 0x8BADF00D, "avx2", False),
            (98765, 0xDEAD10CC, "UNKNOWN_FLAG", False),
        ],
    )
    def test_provides_flag(self, cpu_family: int, cpu_model: int, flag: str, is_provided: bool) -> None:
        """Test if the given CPU provides a flag."""
        assert CPUDatabase.provides_flag(cpu_family, cpu_model, flag) == is_provided
