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

"""A state of not fully resolved software stack in adviser's recommendations implementation."""

from typing import Any
from typing import Tuple
from typing import Dict
from typing import List
from typing import Optional
from collections import OrderedDict

import attr
from thoth.common import RuntimeEnvironment


@attr.s(slots=True, order=False)
class State:
    """Implementation of an adviser's state in state space."""

    score = attr.ib(type=float, default=0.0)
    # Python3.6 fails on OrderedDict subscription, use Dict instead.
    unresolved_dependencies = attr.ib(
        type=Dict[str, Tuple[str, str, str]], default=attr.Factory(OrderedDict)
    )
    resolved_dependencies = attr.ib(
        type=Dict[str, Tuple[str, str, str]], default=attr.Factory(OrderedDict)
    )
    advised_runtime_environment = attr.ib(
        type=Optional[RuntimeEnvironment], kw_only=True, default=None
    )
    _justification = attr.ib(
        type=List[Dict[str, str]], default=attr.Factory(list), kw_only=True
    )

    @property
    def justification(self) -> List[Dict[str, str]]:
        """Get justification for the current state."""
        return self._justification

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a dict representation."""
        advised_runtime_environment = None
        if self.advised_runtime_environment:
            advised_runtime_environment = self.advised_runtime_environment.to_dict()

        return {
            "score": self.score,
            "unresolved_dependencies": self.unresolved_dependencies,
            "resolved_dependencies": self.resolved_dependencies,
            "advised_runtime_environment": advised_runtime_environment,
            "justification": self._justification,
        }

    def is_final(self) -> bool:
        """Check if the given state is a final state."""
        return len(self.unresolved_dependencies) == 0

    def add_justification(self, justification: List[Dict[str, str]]) -> None:
        """Add new entries to the justification field."""
        self._justification.extend(justification)

    def add_unresolved_dependency(self, package_tuple: Tuple[str, str, str]) -> None:
        """Add unresolved dependency into the beam."""
        assert package_tuple[0] not in self.unresolved_dependencies, (
            f"Package {package_tuple!r} cannot be added to unresolved dependencies, "
            f"candidate {self.unresolved_dependencies[package_tuple[0]]!r} is already present"
        )
        self.unresolved_dependencies[package_tuple[0]] = package_tuple

    def __lt__(self, other: "State") -> bool:
        """Override operator to control insertions into beam based on the score."""
        return self.score < other.score

    def clone(self) -> "State":
        """Return a swallow copy of this state that can be used as a next state."""
        cloned_advised_environment = None
        if self.advised_runtime_environment:
            cloned_advised_environment = RuntimeEnvironment.from_dict(
                self.advised_runtime_environment.to_dict()
            )

        new_state = self.__class__(
            score=self.score,
            unresolved_dependencies=OrderedDict(self.unresolved_dependencies),
            resolved_dependencies=OrderedDict(self.resolved_dependencies),
            advised_runtime_environment=cloned_advised_environment,
        )
        new_state.add_justification(self.justification)
        return new_state
