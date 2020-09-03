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

"""Implementation of predictors used with resolver.."""

from .annealing import AdaptiveSimulatedAnnealing
from .hill_climbing import HillClimbing
from .latest import ApproximatingLatest
from .mcts import MCTS
from .package_combinations import PackageCombinations
from .random_walk import RandomWalk
from .sampling import Sampling
from .td import TemporalDifference


__all__ = [
    "AdaptiveSimulatedAnnealing",
    "ApproximatingLatest",
    "HillClimbing",
    "MCTS",
    "PackageCombinations",
    "RandomWalk",
    "Sampling",
    "TemporalDifference",
]
