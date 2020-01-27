#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""Test core step routines."""

from thoth.adviser.step import Step
from .base import AdviserTestCase


class TestStep(AdviserTestCase):
    """Test core step routines."""

    def test_boundaries(self) -> None:
        """Test score boundaries of steps."""
        assert Step.SCORE_MAX > 0.0 > Step.SCORE_MIN

    def test_multi_package_resolution_default(self) -> None:
        """Test default value of multi package resolution."""
        assert Step.MULTI_PACKAGE_RESOLUTIONS is False
