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

from typing import Dict
from typing import Generator
from typing import List
from typing import Set
from typing import Tuple
from itertools import chain
import logging

import attr

from thoth.python import PackageVersion
from thoth.python import Source
from thoth.adviser.python.dependency_graph import DependencyGraphAdaptation
from thoth.adviser.python.dependency_graph import CannotRemovePackage

from .step_stats import StepStats
from .context_base import ContextBase

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class StepContext(ContextBase):
    """A wrapper representing stack stack candidates."""

    packages = attr.ib(type=Dict[Tuple[str, str, str], PackageVersion])
    dependency_graph_adaptation = attr.ib(type=DependencyGraphAdaptation, default=None)
    _stats = attr.ib(type=StepStats, default=attr.Factory(StepStats))

    @classmethod
    def from_paths(cls, direct_dependencies: List[PackageVersion], paths: List[List[Tuple[str, str, str]]]) -> "StepContext":
        """Instantiate step context from paths."""
        packages = {}
        for package_version in direct_dependencies:
            package_tuple = package_version.to_tuple()
            if package_tuple not in packages:
                packages[package_tuple] = package_version

        for path in paths:
            develop = packages[path[0]].develop
            for package_tuple in path:
                if package_tuple in packages:
                    continue

                package_version = PackageVersion(
                    name=package_tuple[0],
                    version="==" + package_tuple[1],
                    develop=develop,
                    index=Source(package_tuple[2]),
                )
                packages[package_tuple] = package_version

        # Explicitly assign paths to direct dependencies to have them present even if they do not have any dependency.
        for direct_dependency in direct_dependencies:
            paths.append([direct_dependency.to_tuple()])

        return cls(
            packages=packages,
            dependency_graph_adaptation=DependencyGraphAdaptation.from_paths(paths),
        )

    @property
    def stats(self) -> StepStats:
        """Retrieve statistics kept during steps computation."""
        return self._stats

    def iter_direct_dependencies(self) -> Generator[PackageVersion, None, None]:
        """Iterate over direct dependencies, respect their ordering."""
        for package_tuple in self.iter_direct_dependencies_tuple():
            yield self.packages[package_tuple]

    def iter_direct_dependencies_tuple(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over direct dependencies, respect their ordering and return a package tuple."""
        # Cast to list is required due to possible removals which would
        # cause runtime errors for dictionary changed size during iteration
        yield from list(self.dependency_graph_adaptation.iter_direct_dependencies_tuple())

    def iter_transitive_dependencies(self) -> Generator[PackageVersion, None, None]:
        """Iterate over indirect (transitive) dependencies, respect their ordering."""
        for package_tuple in self.iter_transitive_dependencies_tuple():
            yield self.packages[package_tuple]

    def iter_transitive_dependencies_tuple(self) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over indirect (transitive) dependencies, respect their ordering."""
        # Cast to list is required due to possible removals which would
        # cause runtime errors for dictionary changed size during iteration
        yield from list(self.dependency_graph_adaptation.iter_transitive_dependencies_tuple())

    def iter_all_dependencies(self) -> Generator[PackageVersion, None, None]:
        """Iterate over all possible dependencies, make sure each dependency is returned once."""
        for package_tuple in self.iter_all_dependencies_tuple():
            yield self.packages[package_tuple]

    def iter_all_dependencies_tuple(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over all the dependencies, return each as a tuple."""
        seen_tuples = set()
        for package_tuple in chain(self.iter_direct_dependencies_tuple(), self.iter_transitive_dependencies_tuple()):
            if package_tuple not in seen_tuples:
                seen_tuples.add(package_tuple)
                yield package_tuple

    def remove_package_tuple(self, package_tuple: Tuple[str, str, str], graceful: bool = False) -> bool:
        """Remove the given package from all the resolution paths, transactional operation."""
        try:
            self.dependency_graph_adaptation.remove_package_tuple(package_tuple)
        except CannotRemovePackage:
            if graceful:
                return False
            raise

        return True

    def remove_package_tuples(self, package_tuples: Set[Tuple[str, str, str]], graceful: bool = False) -> bool:
        """Remove all packages from all the resolution paths, transactional operation."""
        try:
            self.dependency_graph_adaptation.remove_package_tuple(package_tuples)
        except CannotRemovePackage:
            if graceful:
                return False
            raise

        return True

    def score_package_tuple(
        self, package_tuple: Tuple[str, str, str], score: float
    ) -> None:
        """Score positively or negatively the given package making sure it gets precedence/postponed in resolution."""
        self.dependency_graph_adaptation.score_package_tuple(package_tuple, score)
