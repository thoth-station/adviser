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

"""Test randomly pickling up a stack coming out of pipeline.."""

import pytest

from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.state import State
from thoth.adviser.strides import ScoreFilteringStride

from ..base import AdviserTestCase


class TestScoreFiltering(AdviserTestCase):
    """Test randomly pickling up a stack coming out of pipeline.."""

    def test_accept_first(self) -> None:
        """Test accepting the very first result with a specific score."""
        stride = ScoreFilteringStride()
        assert stride.run(State(score=0.02)) is None

    def test_reject_second(self) -> None:
        """Test accepting the very first result and rejecting a second one with same score."""
        stride = ScoreFilteringStride()

        assert stride.run(State(score=0.02)) is None

        # Rejects second.
        with pytest.raises(NotAcceptable):
            stride.run(State(score=0.02))

        # Accepts a new one.
        assert stride.run(State(score=0.01)) is None
