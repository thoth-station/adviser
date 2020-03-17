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

"""Test implementation of Monte-Carlo Tree Search (MCTS) based predictor with annealing schedule."""

import flexmock

from hypothesis import given
from hypothesis.strategies import integers
from hypothesis.strategies import floats

from thoth.adviser.predictors import TemporalDifference

from ..base import AdviserTestCase


class TestMCTS(AdviserTestCase):
    """Test implementation of MCTS based predictor with annealing schedule."""

    def test_pre_run(self) -> None:
        """Test initialization before running."""

    def test_set_reward_signal(self) -> None:
        """Test keeping the reward signal."""

    def test_run(self) -> None:
        """Test running the predictor."""
