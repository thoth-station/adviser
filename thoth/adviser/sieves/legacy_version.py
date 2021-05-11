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

"""A sieve to filter out legacy versions."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class LegacyVersionSieve(Sieve):
    """A sieve to filter out legacy versions.

    This sieve assumes no recent projects use legacy versions hence we can
    simply skip them in the resolution process.
    """

    CONFIGURATION_DEFAULT = {"package_name": None}

    _messages_logged = attr.ib(type=Set[Tuple[str, str, str]], factory=set, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Include this sieve once, always."""
        if not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._messages_logged.clear()
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Cut-off legacy versions from the resolution process."""
        for package_version in package_versions:
            if package_version.semantic_version.is_legacy_version:
                package_tuple = package_version.to_tuple()
                if package_tuple not in self._messages_logged:
                    self._messages_logged.add(package_tuple)
                    _LOGGER.warning(
                        "Removing package %s as the version identifier is a legacy version string",
                        package_version.to_tuple(),
                    )
                continue

            yield package_version
