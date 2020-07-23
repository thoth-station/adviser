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

"""Pipeline context carried during annealing."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Generator
from typing import Tuple
from typing import Set
import operator
import heapq

import attr

from thoth.python import PackageVersion
from thoth.python import Source
from thoth.python import Project
from thoth.storages import GraphDatabase

from .beam import Beam
from .exceptions import NotFound
from .enums import RecommendationType
from .enums import DecisionType
from .state import State


@attr.s(slots=True)
class Context:
    """Context carried during adviser's pipeline run.

    It's suitable to cache entries such as PackageVersion to optimize memory usage and optimize overhead
    needed - for example for parsing version strings (this is lazily pre-cached in PackageVersion).
    """

    project = attr.ib(type=Project, kw_only=True)
    graph = attr.ib(type=GraphDatabase, kw_only=True)
    library_usage = attr.ib(type=Optional[Dict[str, Any]], kw_only=True)
    limit = attr.ib(type=int, kw_only=True)
    count = attr.ib(type=int, kw_only=True)
    beam = attr.ib(type=Beam, kw_only=True)
    recommendation_type = attr.ib(type=Optional[RecommendationType], kw_only=True, default=None)
    decision_type = attr.ib(type=Optional[DecisionType], kw_only=True, default=None)
    package_versions = attr.ib(
        type=Dict[Tuple[str, str, str], PackageVersion], kw_only=True, default=attr.Factory(dict),
    )
    dependencies = attr.ib(
        type=Dict[str, Dict[Tuple[str, str, str], Set[Tuple[str, str, str]]]], kw_only=True, default=attr.Factory(dict),
    )
    dependents = attr.ib(
        type=Dict[
            str,
            Dict[Tuple[str, str, str], Set[Tuple[Tuple[str, str, str], Optional[str], Optional[str], Optional[str],]],],
        ],
        kw_only=True,
        default=attr.Factory(dict),
    )
    sources = attr.ib(type=Dict[str, Source], kw_only=True, default=attr.Factory(dict))
    iteration = attr.ib(type=int, default=0, kw_only=True)
    cli_parameters = attr.ib(type=Dict[str, Any], kw_only=True, default=attr.Factory(dict))
    stack_info = attr.ib(type=List[Dict[str, Any]], kw_only=True, default=attr.Factory(list))
    accepted_final_states_count = attr.ib(type=int, kw_only=True, default=0)
    discarded_final_states_count = attr.ib(type=int, kw_only=True, default=0)

    _accepted_states = attr.ib(type=List[Tuple[Tuple[float, int], State]], kw_only=True, default=attr.Factory(list),)
    _accepted_states_counter = attr.ib(type=int, kw_only=True, default=0)

    def __attrs_post_init__(self) -> None:
        """Verify we have only adviser or dependency monkey specific context."""
        if self.decision_type is not None and self.recommendation_type is not None:
            raise ValueError("Cannot instantiate context for adviser and dependency monkey at the same time")

        if self.decision_type is None and self.recommendation_type is None:
            raise ValueError("Cannot instantiate context not specific to adviser nor dependency monkey")

    def iter_accepted_final_states(self) -> Generator[State, None, None]:
        """Get accepted final states by resolution pipeline, states are not sorted."""
        return (item[1] for item in self._accepted_states)

    def iter_accepted_final_states_sorted(self, reverse: bool = True) -> Generator[State, None, None]:
        """Get accepted final states by resolution pipeline sorted by score and their precedence."""
        return (item[1] for item in sorted(self._accepted_states, key=operator.itemgetter(0), reverse=reverse))

    def get_package_version(
        self, package_tuple: Tuple[str, str, str], *, graceful: bool = False
    ) -> Optional[PackageVersion]:
        """Get the given package version registered to the context."""
        package_version = self.package_versions.get(package_tuple)
        if package_version is None and not graceful:
            raise NotFound(f"Package {package_tuple!r} not found in the pipeline context")

        return package_version

    def register_package_version(self, package_version: PackageVersion) -> bool:
        """Register the given package version to the context."""
        package_tuple = package_version.to_tuple()
        registered = self.package_versions.get(package_tuple)
        if registered:
            # If the given package is shared in develop and in the main part, make it main stack part.
            registered.develop = registered.develop or package_version.develop
            return True

        # Direct dependency, no dependency introduced this one.
        self._note_dependencies(package_tuple=None, dependency_tuple=package_tuple)
        self.package_versions[package_tuple] = package_version
        return False

    def register_accepted_final_state(self, state: State) -> None:
        """Register an accepted state by the resolution pipeline."""
        # We keep only `count' states as that was requested by pipeline caller.
        item = ((state.score, self._accepted_states_counter), state)
        self._accepted_states_counter -= 1

        if self.count is not None and len(self._accepted_states) >= self.count:
            heapq.heappushpop(self._accepted_states, item)
        else:
            heapq.heappush(self._accepted_states, item)

    def get_top_accepted_final_state(self) -> Optional[State]:
        """Get the best accepted final state so far computed by the resolution pipeline."""
        if not self._accepted_states:
            return None

        result = self._accepted_states[len(self._accepted_states) // 2]
        for item in self._accepted_states[1 + len(self._accepted_states) // 2 :]:
            if result[0] < item[0]:
                result = item

        return result[1]

    def register_package_tuple(
        self,
        package_tuple: Tuple[str, str, str],
        *,
        develop: bool,
        dependent_tuple: Optional[Tuple[str, str, str]] = None,
        extras: Optional[List[str]] = None,
        os_name: Optional[str],
        os_version: Optional[str],
        python_version: Optional[str],
    ) -> PackageVersion:
        """Register the given package tuple to pipeline context and return its package version representative."""
        registered = self.package_versions.get(package_tuple)

        if registered:
            # If the given package is shared in develop and in the main part, make it main stack part.
            registered.develop = registered.develop or develop
            self._note_dependencies(
                dependent_tuple, package_tuple, os_name=os_name, os_version=os_version, python_version=python_version,
            )
            # This method is called solely on transitive dependencies - for those we do not track
            # extras as extras are already resolved by solver runs (pre-computed). Keep extras untouched
            # in this function call.
            return registered

        source = self.sources.get(package_tuple[2])
        if not source:
            source = Source(package_tuple[2])
            self.sources[package_tuple[2]] = source

        package_version = PackageVersion(
            name=package_tuple[0], version="==" + package_tuple[1], index=source, extras=extras, develop=develop,
        )
        self.package_versions[package_tuple] = package_version
        self._note_dependencies(
            dependent_tuple, package_tuple, os_name=os_name, os_version=os_version, python_version=python_version,
        )
        return package_version

    def _note_dependencies(
        self,
        package_tuple: Optional[Tuple[str, str, str]],
        dependency_tuple: Tuple[str, str, str],
        os_name: Optional[str] = None,
        os_version: Optional[str] = None,
        python_version: Optional[str] = None,
    ) -> None:
        """Note down dependencies that were introduced."""
        # Mapping: package tuple -> dependency tuple
        if package_tuple is not None:
            if package_tuple[0] not in self.dependencies:
                self.dependencies[package_tuple[0]] = {}

            if package_tuple not in self.dependencies[package_tuple[0]]:
                self.dependencies[package_tuple[0]][package_tuple] = set()

            self.dependencies[package_tuple[0]][package_tuple].add(dependency_tuple)

        # Reverse mapping: dependency tuple -> package tuple
        if dependency_tuple[0] not in self.dependents:
            self.dependents[dependency_tuple[0]] = {}

        if dependency_tuple not in self.dependents[dependency_tuple[0]]:
            self.dependents[dependency_tuple[0]][dependency_tuple] = set()

        if package_tuple is not None:
            # Note down only if we have some dependency - otherwise dependency
            # tuple is a direct dependency. In that case we don't need to keep
            # track of environments for which the version was resolved.
            self.dependents[dependency_tuple[0]][dependency_tuple].add(
                (package_tuple, os_name, os_version, python_version)
            )

    def is_dependency_monkey(self) -> bool:
        """Check if the current context refers to a dependency monkey run."""
        return self.recommendation_type is None

    def is_adviser(self) -> bool:
        """Check if the current context refers to a dependency monkey run."""
        return self.decision_type is None
