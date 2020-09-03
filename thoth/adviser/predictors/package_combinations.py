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

"""Implementation of a predictor used for generating combinations of packages faster."""

from typing import Tuple
from typing import Set
import logging

import attr

from ..predictor import Predictor
from ..state import State

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PackageCombinations(Predictor):
    """A predictor used for generating combinations of packages faster."""

    package_combinations = attr.ib(type=Set[str], default=attr.Factory(set), kw_only=True, converter=set)

    def pre_run(self) -> None:
        """Check attributes set up."""
        if not self.package_combinations:
            raise ValueError("No package combinations supplied to the predictor")

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Run the predictor."""
        state = self.context.beam.get_last()
        if state is None:
            state = self.context.beam.get_random()

        # Expand while we do not have just all the package combinations to generate.
        for unresolved_dependency in state.unresolved_dependencies.keys():
            if unresolved_dependency not in self.package_combinations:
                return state, state.get_random_unresolved_dependency(unresolved_dependency)

        return state, state.get_random_unresolved_dependency()
