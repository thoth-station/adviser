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

"""An object wrapping stack candidates used to generate stacks from in pipeline."""

from typing import List
from typing import Generator
from typing import Tuple
from typing import Dict
from typing import Callable
from typing import Set
from functools import cmp_to_key
from contextlib import ContextDecorator
from itertools import chain
import logging
from collections import deque
import copy

from thoth.python import PackageVersion
from thoth.python import Source

import attr

from .step_stats import StepStats
from .context_base import ContextBase
from .exceptions import CannotRemovePackage

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class _StepChangeContext(ContextDecorator):

    step_context = attr.ib(type="StepContext")
    graceful = attr.ib(type=bool, default=False)
    _to_remove_tuples = attr.ib(
        type=Set[Tuple[str, str, str]], default=attr.Factory(set)
    )
    _to_remove_tuples_list = attr.ib(
        type=List[Tuple[str, str, str]], default=attr.Factory(list)
    )

    def __enter__(self):
        """Enter context and keep track of changes being made to stacks."""
        return self

    def __exit__(self, *exc):
        """Remove paths or tuples which were requested to be removed."""
        for package_tuple in self._to_remove_tuples_list:
            if (
                not any(package_tuple in path for path in self.step_context.raw_paths)
                and package_tuple
                not in self.step_context.iter_direct_dependencies_tuple()
            ):
                _LOGGER.debug(
                    "No need to remove package %r, it was already removed",
                    package_tuple,
                )
                continue

            _LOGGER.debug("Removing %r", package_tuple)
            try:
                self.step_context.remove_package_tuple(package_tuple)
            except CannotRemovePackage as exc:
                _LOGGER.debug("Failed to remove package %r", package_tuple)
                if not self.graceful:
                    raise

    def remove_package_tuple(self, package_tuple: Tuple[str, str, str]) -> None:
        """Mark the given package tuple for removal."""
        if package_tuple not in self._to_remove_tuples:
            self._to_remove_tuples.add(package_tuple)
            self._to_remove_tuples_list.append(package_tuple)


@attr.s(slots=True)
class StepContext(ContextBase):
    """A wrapper representing stack stack candidates."""

    _paths = attr.ib(
        type=List[Tuple[float, List[Tuple[str, str, str]]]], default=attr.Factory(list)
    )
    _stats = attr.ib(type=StepStats, default=attr.Factory(StepStats))
    _direct_dependencies = attr.ib(
        type=List[PackageVersion], default=attr.Factory(list)
    )
    _direct_dependencies_score = attr.ib(
        type=Dict[Tuple[str, str, str], float], default=attr.Factory(dict)
    )
    _direct_dependencies_map = attr.ib(
        type=Dict[str, Dict[str, Dict[str, PackageVersion]]], default=attr.Factory(dict)
    )
    _transitive_dependencies_map = attr.ib(
        type=Dict[str, Dict[str, Set[Dict[str, PackageVersion]]]],
        default=attr.Factory(dict),
    )
    # Associate map, queries to this map answer a question:
    #   What are dependencies of a package?
    # e.g. flask 0.12.1 from pypi depends on werkzeug 0.13 from pypi, the corresponding entry would be:
    #  {
    #    ("flask", "0.12.1", "https://pypi.org/simple"): {
    #        "werkzeug": {("werkzeug", "0.13", "https://pypi.org/simple")}  # A set of dependencies.
    #    }
    #  }
    # The name is used to optimize listing of dependencies of a same name to check for wrong dependency removals.
    _associate_dependency_map = attr.ib(
        type=Dict[Tuple[str, str, str], Dict[str, Tuple[str, str, str]]],
        default=attr.Factory(dict),
    )
    # Associate map, queries to this map answer a question:
    #  What are dependent packages to a package?
    # e.g. flask 0.12.1 from pypi depends on werkzeug 0.13 from pypi, the corresponding entry would be:
    #  {
    #    ("werkzeug", "0.13", "https://pypi.org/simple"): {
    #        ("flask", "0.12.1", "https://pypi.org/simple")   # An item in a set.
    #    }
    #  }
    _associate_dependent_map = attr.ib(
        type=Dict[Tuple[str, str, str], Set[Tuple[str, str, str]]],
        default=attr.Factory(dict),
    )
    # To reduce number of same indexes tracked - these indexes are checked when
    # there is created a new PackageVersion from a tuple.
    _indexes_used = attr.ib(type=Dict[str, Source], default=attr.Factory(dict))

    @property
    def direct_dependencies_map(
        self
    ) -> Dict[str, Dict[str, Dict[str, PackageVersion]]]:
        """Get direct dependencies map."""
        return self._direct_dependencies_map

    @property
    def stats(self) -> StepStats:
        """Retrieve statistics kept during steps computation."""
        return self._stats

    @property
    def raw_paths(self):
        """Return raw paths to packages, as kept internally."""
        return [path[1] for path in self._paths]

    @property
    def transitive_dependencies_map(
        self
    ) -> Dict[str, Dict[str, Dict[str, PackageVersion]]]:
        """Retrieve transitive dependencies map."""
        return self._transitive_dependencies_map

    def change(self, graceful: bool = False) -> _StepChangeContext:
        """Get stack context change."""
        return _StepChangeContext(self, graceful)

    def add_resolved_direct_dependency(self, package_version: PackageVersion) -> None:
        """Add a resolved (pinned down direct dependency)."""
        if package_version.name not in self._direct_dependencies_map:
            self._direct_dependencies_map[package_version.name] = {}

        it = self._direct_dependencies_map[package_version.name]
        if package_version.locked_version not in it:
            it[package_version.locked_version] = {}

        it = it[package_version.locked_version]
        if package_version.index.url not in it:
            it[package_version.index.url] = package_version
            self._direct_dependencies.append(package_version)
            self._direct_dependencies_score[package_version.to_tuple()] = 0.0

    def _add_transitive_dependency_tuple(
        self, package_name: str, package_version: str, index_url: str
    ) -> None:
        """Add a transitive dependency based on tuple."""
        if package_name not in self._transitive_dependencies_map:
            self._transitive_dependencies_map[package_name] = {}

        it = self._transitive_dependencies_map[package_name]
        if package_version not in it:
            it[package_version] = {}

        it = it[package_version]
        source = self._indexes_used.get(index_url)
        if not source:
            source = Source(index_url)
            self._indexes_used[index_url] = source

        if index_url not in it:
            it[index_url] = PackageVersion(
                name=package_name,
                version="==" + package_version,  # Always adding a locked version
                develop=False,
                index=source,
            )

    def iter_direct_dependencies(self) -> Generator[PackageVersion, None, None]:
        """Iterate over direct dependencies, respect their ordering."""
        yield from self._direct_dependencies

    def iter_direct_dependencies_tuple(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over direct dependencies, respect their ordering and return a package tuple."""
        yield from (item.to_tuple() for item in self._direct_dependencies)

    def iter_transitive_dependencies(self) -> Generator[PackageVersion, None, None]:
        """Iterate over indirect (transitive) dependencies, respect their ordering."""
        for indexes in self._transitive_dependencies_map.values():
            for versions in indexes.values():
                yield from versions.values()

    def iter_transitive_dependencies_tuple(self):
        """Iterate over indirect (transitive) dependencies, respect their ordering."""
        seen = set()
        for _, path in self._paths:
            for package_tuple in path[1:]:
                if package_tuple not in seen:
                    seen.add(package_tuple)
                    yield package_tuple

    def iter_all_dependencies(self) -> Generator[PackageVersion, None, None]:
        """Iterate over all possible dependencies, make sure each dependency is returned once."""
        seen = set()

        for package_version in chain(
            self.iter_direct_dependencies(), self.iter_transitive_dependencies()
        ):
            package_tuple = package_version.to_tuple()
            if package_tuple not in seen:
                seen.add(package_tuple)
                yield package_version

    def iter_all_dependencies_tuple(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over all the dependencies, return each as a tuple."""
        return (
            package_version.to_tuple()
            for package_version in self.iter_all_dependencies()
        )

    def add_paths(self, paths: List[List[Tuple[str, str, str]]]) -> None:
        """Add all the paths of transitive dependencies to this instance."""
        for path in paths:
            for idx, package_tuple in enumerate(path):
                if idx >= 1:
                    self._add_transitive_dependency_tuple(*package_tuple)

                # Fill in map for dependency tracking.
                if idx + 1 < len(path):
                    dependency = path[idx + 1]

                    if package_tuple not in self._associate_dependency_map:
                        self._associate_dependency_map[package_tuple] = {}

                    dependency_name = dependency[0]
                    if (
                        dependency[0]
                        not in self._associate_dependency_map[package_tuple]
                    ):
                        self._associate_dependency_map[package_tuple][
                            dependency_name
                        ] = set()

                    self._associate_dependency_map[package_tuple][dependency_name].add(
                        dependency
                    )

                # Fill in map for dependent tracking.
                if idx > 0:
                    dependent = path[idx - 1]

                    if package_tuple not in self._associate_dependent_map:
                        self._associate_dependent_map[package_tuple] = set()

                    self._associate_dependent_map[package_tuple].add(dependent)

        self._paths.extend((0.0, path) for path in paths)

    @staticmethod
    def _create_record(package_version: PackageVersion, dependency_map: dict):
        if package_version.name not in dependency_map:
            dependency_map[package_version.name] = {}

        it = dependency_map[package_version.name]
        if package_version.locked_version not in it:
            it[package_version.locked_version] = {}

        it = it[package_version.locked_version]
        if package_version.index.url not in it:
            it[package_version.index.url] = package_version

    def remove_package_tuple(self, package_tuple: Tuple[str, str, str]) -> None:
        """Remove the given package from all the resolution paths."""
        old_paths_length = len(self._paths)
        old_direct_length = len(self._direct_dependencies)

        new_paths = []
        stack = deque([package_tuple])
        removed = set()
        # Do not adjust it directly - it can lead to an invalid self._paths in case of an exception.
        paths = copy.copy(self._paths)
        # We update associate dependency map once we know the given package is actually removed.
        to_remove_associate_dependency_map = set()

        while stack:
            to_remove_tuple = stack.pop()
            removed.add(to_remove_tuple)

            for score, path in paths:
                if to_remove_tuple not in path:
                    new_paths.append((score, path))
                    continue

                # Check that if we remove this package, the removal of path does not
                # affect direct dependencies of application. If yes, the removal is invalid.
                dependents = self._associate_dependent_map.get(to_remove_tuple)
                last_dependent = to_remove_tuple

                if isinstance(dependents, set) and len(dependents) == 0:
                    # We have reached the marker.
                    continue
                elif dependents is None:
                    # Direct dependency, check we have another direct dependency candidate of a same type.
                    for direct_package_version in self._direct_dependencies:
                        if direct_package_version.name == last_dependent[0] and (
                            direct_package_version.locked_version != last_dependent[1]
                            or direct_package_version.index.url != last_dependent[2]
                        ):
                            break
                    else:
                        raise CannotRemovePackage(
                            f"Cannot remove package {package_tuple}, removing this package would lead "
                            f"to removal of all direct dependencies of package {last_dependent[0]!r}"
                        )
                else:
                    # Not direct dependency, check the current state and traverse up if necessary.
                    for dependent in dependents:
                        for dependency in self._associate_dependency_map[dependent][
                            to_remove_tuple[0]
                        ]:
                            # Now check if we have another package of a same type
                            # to the one we want to be removed (another candidate). If no, check we do not
                            # break any of the dependencies traversing up the dependency graph.
                            if dependency[0] == to_remove_tuple[0] and (
                                dependency[1] != to_remove_tuple[1]
                                or dependency[2] != to_remove_tuple[2]
                            ):
                                # An alternate package - package with same
                                # name but different version or index.
                                break
                        else:
                            # We cannot satisfy requirements for "dependent" by removing "dependency",
                            # we need to remove dependent as well.
                            stack.append(dependent)
                            # Delegate removal of this path to the next round as "dependent" introduced bad
                            # package which should be removed.
                            new_paths.append((score, path))

                    self._associate_dependent_map[to_remove_tuple] = set()
                    for dependent in dependents:
                        to_remove_associate_dependency_map.add(
                            (dependent, to_remove_tuple)
                        )

            # Filter out markers.
            self._associate_dependent_map = {
                k: v for k, v in self._associate_dependent_map.items() if v
            }

            # Assign new paths with removed packages, we iterate on this list to satisfy all the removals.
            paths = list(new_paths)
            new_paths = []

        # We need to check we construct direct dependency list from:
        #  1. All the direct dependencies stated in paths.
        #  2. All the direct dependencies which had no paths.
        #
        # Besides that we need to perform a check that no direct dependency
        # of a type was removed during cut off.
        #
        # PS: this will be much simpler if we would just maintain paths
        # with each direct dependency in place.
        new_direct_dependencies_from_paths = set()
        for _, path in paths:
            new_direct_dependencies_from_paths.add(path[0])

        old_direct_dependencies_from_paths = set()
        for _, path in self._paths:
            old_direct_dependencies_from_paths.add(path[0])

        direct_dependency_types = set()
        new_direct_dependencies_tuples = []
        new_direct_dependencies_types = set()
        for direct_dependency in self._direct_dependencies:
            direct_dependency_types.add(direct_dependency.name)
            direct_dependency_tuple = direct_dependency.to_tuple()
            if (direct_dependency_tuple in new_direct_dependencies_from_paths) or (
                direct_dependency_tuple not in removed
                and direct_dependency_tuple not in old_direct_dependencies_from_paths
            ):
                new_direct_dependencies_tuples.append(direct_dependency_tuple)
                new_direct_dependencies_types.add(direct_dependency_tuple[0])

        for direct_dependency_type in direct_dependency_types:
            if direct_dependency_type not in new_direct_dependencies_types:
                raise CannotRemovePackage(
                    f"Cannot remove package {package_tuple}, removing this package would lead "
                    f"to removal of all direct dependencies of package {direct_dependency_type!r}"
                )

        for removed_tuple in removed:
            self._transitive_dependencies_map.get(removed_tuple[0], {}).get(
                removed_tuple[1], {}
            ).pop(removed_tuple[2], None)
            self._stats.mark_removed_package_tuple(removed_tuple)

        for dependent, to_remove_tuple in to_remove_associate_dependency_map:
            self._associate_dependency_map[dependent][to_remove_tuple[0]].remove(
                to_remove_tuple
            )

        self._paths = paths
        self._direct_dependencies = [
            self.get_package_version_tuple(pt) for pt in new_direct_dependencies_tuples
        ]
        new_direct_dependencies_score = {}
        new_direct_dependencies_map = {}
        for package_version in self._direct_dependencies:
            adjust_package_tuple = package_version.to_tuple()
            new_direct_dependencies_score[
                adjust_package_tuple
            ] = self._direct_dependencies_score[adjust_package_tuple]
            self._create_record(package_version, new_direct_dependencies_map)

        self._direct_dependencies_score = new_direct_dependencies_score
        self._direct_dependencies_map = new_direct_dependencies_map

        if old_paths_length == len(self._paths) and old_direct_length == len(
            self._direct_dependencies
        ):
            _LOGGER.warning(
                "Requested to remove package %r, but no changes were made to paths",
                package_tuple,
            )

    def score_path_index(self, idx: int, score: float) -> None:
        """Score the given path based on its index."""
        self._paths[idx] = (self._paths[idx][0] + score, self._paths[idx][1])

    def score_package_tuple(
        self, package_tuple: Tuple[str, str, str], score: float
    ) -> None:
        """Score a path based on a package which is present in the path."""
        some_seen = False
        for idx, path in enumerate(self._paths):
            if package_tuple in path[1]:
                self.score_path_index(idx, score)
                some_seen = True

        if package_tuple in self._direct_dependencies_score:
            self._direct_dependencies_score[package_tuple] += score
            some_seen = True

        if not some_seen:
            _LOGGER.warning(
                "No paths were seen with package %r, no score adjustment was done",
                package_tuple,
            )

    def iter_paths_with_score(
        self
    ) -> Generator[Tuple[int, float, List[Tuple[str, str, str]]], None, None]:
        """Iterate over paths and return path with its score and index."""
        yield from self._paths

    def get_package_version_tuple(self, package_tuple: tuple) -> PackageVersion:
        """Get package version from the dependencies map based on tuple provided."""
        try:
            return self._transitive_dependencies_map[package_tuple[0]][
                package_tuple[1]
            ][package_tuple[2]]
        except KeyError:
            return self._direct_dependencies_map[package_tuple[0]][package_tuple[1]][
                package_tuple[2]
            ]

    def final_sort(self) -> None:
        """Perform sorting of paths and direct dependencies based on score.

        This sorting *HAS TO* be performed before the actual scoring if run un un-sorted paths as it does
        not take into account scoring.
        """
        def cmp_function(
            path1: Tuple[float, List[Tuple[str, str, str]]],
            path2: [Tuple[float, List[Tuple[str, str, str]]]],
        ) -> int:
            """Comparision based on score."""
            score1 = path1[0]
            score2 = path2[0]
            return score1 - score2

        self._paths.sort(key=cmp_to_key(cmp_function))
        self._direct_dependencies.sort(
            key=lambda x: self._direct_dependencies_score[x.to_tuple()]
        )

    def sort_direct_dependencies(
        self, cmp_function: Callable, reverse: bool = False
    ) -> None:
        """Perform sorting on direct dependencies."""
        self._direct_dependencies.sort(key=cmp_to_key(cmp_function), reverse=reverse)

    def sort_paths(self, cmp_function: Callable, reverse: bool = False) -> None:
        """Perform sorting of paths."""
        self._paths.sort(key=cmp_to_key(cmp_function), reverse=reverse)
