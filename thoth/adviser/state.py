#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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
from typing import Generator
import random
import weakref

import attr
from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
import termial_random


@attr.s(slots=True, order=False)
class State:
    """Implementation of an adviser's state in state space."""

    score = attr.ib(type=float, default=0.0)
    # Iteration in which the state was introduced.
    iteration = attr.ib(type=int, default=0)
    # States added in the given iteration.
    unresolved_dependencies = attr.ib(default=attr.Factory(dict))  # type: Dict[str, Dict[int, Tuple[str, str, str]]]
    resolved_dependencies = attr.ib(default=attr.Factory(dict))  # type: Dict[str, Tuple[str, str, str]]
    _parent = attr.ib(default=None)  # type: weakref.ReferenceType['State']
    advised_runtime_environment = attr.ib(type=Optional[RuntimeEnvironment], kw_only=True, default=None)
    # See RFC-6902:
    #   https://tools.ietf.org/html/rfc6902
    # An example entry for a manifest change:
    #   [
    #     {
    #       "apiVersion": "apps.openshift.io/v1",
    #       "kind": "DeploymentConfig",
    #       "patch": {
    #         "op": "add",
    #         "path": "spec.template.spec.containers[0].env",
    #         "value": {"name": "OMP_NUM_THREADS", "value": "1"},
    #       }
    #     }
    #   ]
    # See available yaml-patch operations at https://python-json-patch.readthedocs.io/en/latest/tutorial.html
    #
    # Each entry is a list of JSON patches to be applied. If any entry fails to
    # patch, the patching can continue with the subsequent JSON patch as each
    # entry corresponds to a list of atomic changes to be applied:
    #
    #  https://tools.ietf.org/html/rfc6902#section-5
    advised_manifest_changes = attr.ib(type=List[List[Dict[str, Any]]], kw_only=True, default=attr.Factory(list))
    justification = attr.ib(type=List[Dict[str, str]], default=attr.Factory(list), kw_only=True)

    _EPSILON = 0.1

    @property
    def parent(self):
        # type:('State') -> Optional['State']
        """Retrieve parent to this state.

        If None the state is top level state or parent is no longer maintained. Note the return
        value of None depends on actual gc runs.
        """
        if self._parent:
            return self._parent()

        return None

    @classmethod
    def from_direct_dependencies(cls, direct_dependencies: Dict[str, List[PackageVersion]]) -> "State":
        """Create an initial state out of direct dependencies."""
        unresolved_dependencies = {}  # type: Dict[str, Dict[int, Tuple[str, str, str]]]

        for dependency_name, dependency_versions in direct_dependencies.items():
            unresolved_dependencies[dependency_name] = {}
            for dependency_version in dependency_versions:
                dependency_tuple = dependency_version.to_strict_tuple()
                unresolved_dependencies[dependency_name][hash(dependency_tuple)] = dependency_tuple

        return cls(unresolved_dependencies=unresolved_dependencies)

    def __lt__(self, other: "State") -> bool:
        """Compare two objects, comparision protocol used in the beam."""
        return self.score < other.score

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a dict representation."""
        advised_runtime_environment = None
        if self.advised_runtime_environment:
            advised_runtime_environment = self.advised_runtime_environment.to_dict()

        # Parent is removed intentionally.
        return {
            "advised_manifest_changes": self.advised_manifest_changes,
            "advised_runtime_environment": advised_runtime_environment,
            "iteration": self.iteration,
            "justification": self.justification,
            "resolved_dependencies": self.resolved_dependencies,
            "score": self.score,
            "unresolved_dependencies": self.unresolved_dependencies,
        }

    def is_final(self) -> bool:
        """Check if the given state is a final state."""
        return len(self.unresolved_dependencies) == 0

    def add_justification(self, justification: List[Dict[str, str]]) -> None:
        """Add new entries to the justification field."""
        self.justification.extend(justification)

    def add_unresolved_dependency(self, package_tuple: Tuple[str, str, str]) -> None:
        """Add unresolved dependency into the state."""
        if package_tuple[0] not in self.unresolved_dependencies:
            self.unresolved_dependencies[package_tuple[0]] = {}

        self.unresolved_dependencies[package_tuple[0]][hash(package_tuple)] = package_tuple

    def set_unresolved_dependencies(self, dependencies: Dict[str, List[Tuple[str, str, str]]]) -> None:
        """Set unresolved dependencies - any unresolved dependencies will be overwritten."""
        for dependency_name, dependency_tuples in dependencies.items():
            self.unresolved_dependencies[dependency_name] = {hash(d): d for d in dependency_tuples}

    def update_unresolved_dependencies(self, dependencies: Dict[str, List[Tuple[str, str, str]]]) -> None:
        """Update unresolved dependencies respecting the ones passed in as parameters."""
        for dependency_name, dependency_tuples in dependencies.items():
            if not dependency_tuples:
                continue

            if dependency_name not in self.unresolved_dependencies:
                self.unresolved_dependencies[dependency_name] = {}

            for d in dependency_tuples:
                self.unresolved_dependencies[dependency_name][hash(d)] = d

    def remove_unresolved_dependency(self, package_tuple: Tuple[str, str, str]) -> None:
        """Remove the given unresolved dependency from state."""
        self.unresolved_dependencies[package_tuple[0]].pop(hash(package_tuple))
        if not self.unresolved_dependencies[package_tuple[0]]:
            # Last item, remove records about it.
            self.unresolved_dependencies.pop(package_tuple[0])

    def remove_unresolved_dependency_subtree(self, package_name: str) -> None:
        """Remove the whole dependency sub-tree from the state."""
        self.unresolved_dependencies.pop(package_name, None)

    def add_resolved_dependency(self, package_tuple: Tuple[str, str, str]) -> None:
        """Add a resolved dependency into the state."""
        if (
            package_tuple[0] in self.resolved_dependencies
            and package_tuple != self.resolved_dependencies[package_tuple[0]]
        ):
            raise ValueError(
                f"Package {package_tuple!r} is already present in the state "
                f"in different version {self.resolved_dependencies[package_tuple[0]]!r}"
            )
        self.resolved_dependencies[package_tuple[0]] = package_tuple

    def mark_dependency_resolved(self, package_tuple: Tuple[str, str, str]) -> None:
        """Mark the given dependency as resolved in the current state."""
        self.remove_unresolved_dependency(package_tuple)
        self.remove_unresolved_dependency_subtree(package_tuple[0])
        # The logic behind state manipulation makes sure there is no package version or package source clash.
        self.add_resolved_dependency(package_tuple)

    def get_first_unresolved_dependency(self, dependency_name: Optional[str] = None) -> Tuple[str, str, str]:
        """Get a very first unresolved dependency tuple."""
        try:
            dependency_name = dependency_name or next(iter(self.unresolved_dependencies))
            unresolved_dependency_id = next(iter(self.unresolved_dependencies[dependency_name]))
            return self.unresolved_dependencies[dependency_name][unresolved_dependency_id]
        except StopIteration as exc:
            raise ValueError(f"No unresolved dependency found in state: {self!r}") from exc

    def get_random_first_unresolved_dependency(self, dependency_name: Optional[str] = None) -> Tuple[str, str, str]:
        """Get a very first unresolved dependency tuple."""
        dependency_name = dependency_name or random.choice(list(self.unresolved_dependencies))
        try:
            unresolved_dependency_id = next(iter(self.unresolved_dependencies[dependency_name]))
            return self.unresolved_dependencies[dependency_name][unresolved_dependency_id]
        except StopIteration as exc:
            raise ValueError(f"No unresolved dependency found in state: {self!r}") from exc

    def get_random_unresolved_dependency(
        self, dependency_name: Optional[str] = None, prefer_recent: bool = True
    ) -> Tuple[str, str, str]:
        """Get a very first unresolved dependency tuple."""
        dependency_name = dependency_name or random.choice(list(self.unresolved_dependencies))

        choices = list(self.unresolved_dependencies[dependency_name])
        if prefer_recent:
            # perform multi-armed bandit - epsilon-greedy strategy
            unresolved_dependency_id = None
            if len(choices) > 1 and self._EPSILON >= random.random():
                unresolved_dependency_id = choices[termial_random.random(len(choices))]

            if unresolved_dependency_id is None:
                unresolved_dependency_id = choices[0]
        else:
            unresolved_dependency_id = random.choice(choices)

        return self.unresolved_dependencies[dependency_name][unresolved_dependency_id]

    def iter_unresolved_dependencies(self) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over unresolved dependencies."""
        for nested in self.unresolved_dependencies.values():
            yield from nested.values()

    def iter_resolved_dependencies(self) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over resolved dependencies."""
        yield from self.resolved_dependencies.values()

    def clone(self) -> "State":
        """Return a swallow copy of this state that can be used as a next state."""
        cloned_advised_environment = None
        if self.advised_runtime_environment:
            cloned_advised_environment = RuntimeEnvironment.from_dict(self.advised_runtime_environment.to_dict())

        unresolved_dependencies = self.unresolved_dependencies.copy()
        for dependency_name in unresolved_dependencies.keys():
            unresolved_dependencies[dependency_name] = unresolved_dependencies[dependency_name].copy()

        return self.__class__(
            score=self.score,
            iteration=self.iteration,
            unresolved_dependencies=unresolved_dependencies,
            resolved_dependencies=self.resolved_dependencies.copy(),
            advised_runtime_environment=cloned_advised_environment,
            advised_manifest_changes=self.advised_manifest_changes.copy(),
            justification=self.justification.copy(),
            parent=weakref.ref(self),
        )

    def __del__(self) -> None:
        """Destruct self."""
        # Destruct parts that are not eventually populated to the pipeline product abstraction.
        del self.unresolved_dependencies
        del self.resolved_dependencies
