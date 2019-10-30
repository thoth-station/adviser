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

"""Pipeline context carried during annealing."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import attr

from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import Source

from .exceptions import NotFound


@attr.s(slots=True)
class Context:
    """Context carried during adviser's pipeline run.

    It's suitable to cache entries such as PackageVersion to optimize memory usage and optimize overhead
    needed - for example for parsing version strings (this is lazily pre-cached in PackageVersion).
    """

    package_versions = attr.ib(
        type=Dict[Tuple[str, str, str], PackageVersion],
        kw_only=True,
        default=attr.Factory(dict),
    )
    sources = attr.ib(type=Dict[str, Source], kw_only=True, default=attr.Factory(dict))
    # TODO: move to state?
    advised_runtime_environment = attr.ib(
        type=RuntimeEnvironment, kw_only=True, default=None
    )
    stack_info = attr.ib(
        type=Optional[List[Dict[str, Any]]], kw_only=True, default=attr.Factory(list)
    )
    _accepted_final_states_count = attr.ib(type=int, kw_only=True, default=0)
    _discarded_final_states_count = attr.ib(type=int, kw_only=True, default=0)

    @property
    def accepted_final_states_count(self) -> int:
        """Return number of accepted final states as produced by the pipeline."""
        return self._accepted_final_states_count

    @property
    def discarded_final_states_count(self) -> int:
        """Return number of discarded final states (discarded by strides) during the pipeline run."""
        return self._discarded_final_states_count

    def inc_accepted_final_states_count(self) -> None:
        """Increment counter of accepted final states count."""
        self._accepted_final_states_count += 1

    def inc_discarded_final_states_count(self) -> None:
        """Increment counter of discarded final states count."""
        self._discarded_final_states_count += 1

    def get_package_version(
        self, package_tuple: Tuple[str, str, str]
    ) -> PackageVersion:
        """Get the given package version registered to the context."""
        package_version = self.package_versions.get(package_tuple)
        if package_version is None:
            raise NotFound(
                f"Package {package_tuple!r} not found in the pipeline context"
            )

        return package_version

    def register_package_version(self, package_version: PackageVersion) -> bool:
        """Register the given package version to the context."""
        registered = self.package_versions.get(package_version.to_tuple())
        if registered:
            # If the given package is shared in develop and in the main part, make it main stack part.
            registered.develop = registered.develop or package_version.develop
            # TODO: check if it is the same entry
            return True

        self.package_versions[package_version.to_tuple()] = package_version
        return False

    def register_package_tuple(
        self,
        package_tuple: Tuple[str, str, str],
        *,
        develop: bool,
        markers: Optional[str] = None,
        extras: Optional[List[str]] = None,
    ) -> PackageVersion:
        """Register the given package tuple to pipeline context and return its package version representative."""
        registered = self.package_versions.get(package_tuple)

        if registered:
            # If the given package is shared in develop and in the main part, make it main stack part.
            registered.develop = registered.develop or develop
            # TODO: check for extras and markers?
            return registered

        source = self.sources.get(package_tuple[2])
        if not source:
            source = Source(package_tuple[2])
            self.sources[package_tuple[2]] = source

        package_version = PackageVersion(
            name=package_tuple[0],
            version="==" + package_tuple[1],
            index=source,
            markers=markers,
            extras=extras,
            develop=develop,
        )
        self.package_versions[package_tuple] = package_version
        return package_version
