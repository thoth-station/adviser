#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""A sieve to filter out packages respecting desired combinations that should be computed."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Set
from typing import Tuple
from typing import Union
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from voluptuous import Required
from voluptuous import Schema

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PackageCombinationsSieve(Sieve):
    """A sieve to filter out packages respecting desired combinations that should be computed."""

    CONFIGURATION_DEFAULT: Dict[str, Union[None, List[str]]] = {"package_name": None, "package_combinations": []}
    CONFIGURATION_SCHEMA = Schema(
        {
            Required("package_name"): None,
            Required("package_combinations"): [str],
        }
    )

    _package_tuples_seen = attr.ib(
        type=Dict[str, Tuple[str, str, str]], default=attr.Factory(dict), kw_only=True, init=False
    )
    _package_combinations = attr.ib(type=Set[str], default=attr.Factory(set), kw_only=True, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, never."""
        yield from ()
        return None

    def pre_run(self) -> None:
        """Prepare for the actual run."""
        self._package_combinations = set(self.configuration["package_combinations"])
        if not self._package_combinations:
            raise NotImplementedError("No package packages to compute combinations supplied")

        self._package_tuples_seen.clear()
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out packages based on Python package index configured for the given package."""
        for package_version in package_versions:
            if package_version.name in self._package_combinations:
                # Yield any version of this package based on the configuration.
                yield package_version
                continue

            seen_package_tuple = self._package_tuples_seen.get(package_version.name)
            if seen_package_tuple is None:
                self._package_tuples_seen[package_version.name] = package_version.to_tuple()
                yield package_version
                continue

            if seen_package_tuple == package_version.to_tuple():
                # This version was already used in one of the previous runs.
                yield package_version
                continue
