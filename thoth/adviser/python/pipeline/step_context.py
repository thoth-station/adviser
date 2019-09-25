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
from typing import Tuple
from typing import Callable
from typing import Union
from itertools import chain
import logging

import attr

from thoth.python import PackageVersion
from thoth.python import Source
from thoth.adviser.python.dependency_graph import DependencyGraphAdaptation
from thoth.adviser.python.dependency_graph import DependencyGraphTransaction

from .step_stats import StepStats
from .context_base import ContextBase
from .unsolved_package import UnsolvedPackage

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class StepContext(ContextBase):
    """A wrapper representing stack stack candidates."""

    packages = attr.ib(type=Dict[Tuple[str, str, str], PackageVersion])
    unsolved_packages = attr.ib(type=Dict[Tuple[str, str, None], UnsolvedPackage])
    dependency_graph_adaptation = attr.ib(type=DependencyGraphAdaptation, default=None)
    _stats = attr.ib(type=StepStats, default=attr.Factory(StepStats))

    @classmethod
    def from_paths(
        cls,
        direct_dependencies: Dict[Tuple[str, str, str], PackageVersion],
        paths: Dict[Tuple[str, str, str], List[Tuple[Tuple[str, str, str], Tuple[str, str, str]]]],
    ) -> "StepContext":
        """Instantiate step context from paths."""
        packages = dict(direct_dependencies)
        unsolved_packages = {}
        for direct_dependency_tuple, dependency_paths in paths.items():
            for package_tuples in dependency_paths:
                for package_tuple in package_tuples:
                    if package_tuple in packages:
                        continue

                    if cls.is_unsolved_package_tuple(package_tuple):
                        # Not fully resolved yet.
                        key = (package_tuple[0], package_tuple[1], None)
                        if key not in unsolved_packages:
                            unsolved_packages[key] = UnsolvedPackage(
                                package_name=package_tuple[0],
                                package_version=package_tuple[1],
                                develop=direct_dependencies[direct_dependency_tuple].develop,
                            )
                    else:
                        package_version = PackageVersion(
                            name=package_tuple[0],
                            version="==" + package_tuple[1],
                            develop=direct_dependencies[direct_dependency_tuple].develop,
                            index=Source(package_tuple[2]),
                        )
                        packages[package_tuple] = package_version

        path_tuples = []
        for dependency_paths in paths.values():
            for path in dependency_paths:
                path_tuples.append(path)

        _LOGGER.debug(
            "Total number of packages considered including all transitive dependencies: %d",
            len(packages)
        )
        _LOGGER.debug(
            "Total number of unsolved packages in the dependency graph: %d",
            len(unsolved_packages)
        )
        _LOGGER.info(
            "Instantiating step context and constructing dependency graph adaptation"
        )
        return cls(
            packages=packages,
            unsolved_packages=unsolved_packages,
            dependency_graph_adaptation=DependencyGraphAdaptation.from_paths(
                direct_dependencies=direct_dependencies.keys(),
                paths=path_tuples,
            ),
        )

    @property
    def stats(self) -> StepStats:
        """Retrieve statistics kept during steps computation."""
        return self._stats

    @staticmethod
    def is_unsolved_package_tuple(package_tuple: Tuple[str, Union[None, str], Union[None, str]]) -> bool:
        """Check if the given package tuple represents an unsolved package."""
        # We could just check for the third (index_url) entry, but to be verbose.
        return package_tuple[2] is None or package_tuple[1] is None

    def sort_paths(
        self,
        comparision_func: Callable[[PackageVersion, PackageVersion], int],
        reverse: bool = True,
    ) -> None:
        """Sort paths in the dependency graph."""
        self.dependency_graph_adaptation.sort_paths(comparision_func, reverse=reverse)

    def iter_direct_dependencies(self, develop: bool = None) -> Generator[PackageVersion, None, None]:
        """Iterate over direct dependencies, respect their ordering."""
        for package_tuple in self.iter_direct_dependencies_tuple():
            package_version = self.packages[package_tuple]
            if develop is not None:
                if package_version.develop == develop:
                    yield package_version
            else:
                yield package_version

    def iter_direct_dependencies_tuple(
        self,
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over direct dependencies, respect their ordering and return a package tuple."""
        # Cast to list is required due to possible removals which would
        # cause runtime errors for dictionary changed size during iteration
        yield from list(
            self.dependency_graph_adaptation.iter_direct_dependencies_tuple()
        )

    def iter_transitive_dependencies(
        self,
        develop: bool = None
    ) -> Generator[Union[PackageVersion, UnsolvedPackage], None, None]:
        """Iterate over indirect (transitive) dependencies, respect their ordering."""
        for package_tuple in self.iter_transitive_dependencies_tuple():
            if self.is_unsolved_package_tuple(package_tuple):
                to_yield = self.unsolved_packages[package_tuple]
            else:
                to_yield = self.packages[package_tuple]
            if develop is not None:
                if to_yield.develop == develop:
                    yield to_yield
            else:
                yield to_yield

    def iter_transitive_dependencies_tuple(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over indirect (transitive) dependencies, respect their ordering."""
        # Cast to list is required due to possible removals which would
        # cause runtime errors for dictionary changed size during iteration
        yield from list(
            self.dependency_graph_adaptation.iter_transitive_dependencies_tuple()
        )

    def iter_all_dependencies(self, develop: bool = None) -> Generator[PackageVersion, None, None]:
        """Iterate over all possible dependencies, make sure each dependency is returned once."""
        for package_tuple in self.iter_all_dependencies_tuple():
            package_version = self.packages[package_tuple]
            if develop is not None:
                if package_version.develop == develop:
                    yield package_version
            else:
                yield package_version

    def iter_all_dependencies_tuple(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over all the dependencies, return each as a tuple."""
        seen_tuples = set()
        for package_tuple in chain(
            self.iter_direct_dependencies_tuple(),
            self.iter_transitive_dependencies_tuple(),
        ):
            if package_tuple not in seen_tuples:
                seen_tuples.add(package_tuple)
                yield package_tuple

    def remove_package_tuples(
        self, *package_tuples: Tuple[str, str, str]
    ) -> DependencyGraphTransaction:
        """Remove all packages from all the resolution paths, transactional operation."""
        return self.dependency_graph_adaptation.remove_package_tuples(*package_tuples)

    def score_package_tuple(
        self, package_tuple: Tuple[str, str, str], score: float
    ) -> None:
        """Score positively or negatively the given package making sure it gets precedence/postponed in resolution."""
        self.dependency_graph_adaptation.score_package_tuple(package_tuple, score)
