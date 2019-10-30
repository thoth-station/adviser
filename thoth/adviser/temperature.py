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

"""Implementation of Adaptive Simulated Annealing (ASA) used to resolve software stacks."""

import logging
from typing import Any
from typing import Callable
from typing import Type
from typing import TYPE_CHECKING

import attr

_LOGGER = logging.getLogger(__name__)


ASATemperatureFunctionType = Callable[[int, float, int, int], float]
x_runtime: Type[Any]
if not TYPE_CHECKING:
    x_runtime = ASATemperatureFunctionType


@attr.s(slots=True)
class ASATemperatureFunction:
    """Temperature function used in simulated annealing.

    Some of the functions were picked from:

      https://www.mathworks.com/help/gads/how-simulated-annealing-works.html
    """

    @classmethod
    def exp(cls, iteration: int, t0: float, count: int, limit: int) -> float:
        """Exponential temperature function."""
        k = count / limit
        temperature = t0 * (0.95 ** k)
        _LOGGER.debug(
            "New temperature for (iteration=%d, t0=%d, count=%d, limit=%d, k=%f) = %g",
            iteration,
            t0,
            count,
            limit,
            k,
            temperature,
        )
        return temperature
