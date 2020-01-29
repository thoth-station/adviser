#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Kevin Postlehtwait
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

"""Filter out stacks which have buildtime errors."""

import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from thoth.storages.exceptions import NotFoundError

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


class AbiCompatabilitySieve(Sieve):
    """Remove packages if the image being used doesn't have necessary ABI."""

    @classmethod
    def should_include(
        cls, builder_context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Remove indexes which are not enabled in pipeline configuration."""
        if not builder_context.is_included(cls) and builder_context.project.runtime_environment.is_fully_specified():
            return {}

        return None

    def pre_run(self):
        """Initialize image_symbols."""
        runtime_environment = self.context.project.runtime_environment
        self.image_symbols = set(self.context.graph.get_analyzed_image_symbols_all(
                            os_name=runtime_environment.operating_system.name,
                            os_version=runtime_environment.operating_system.version,
                            cuda_version=runtime_environment.cuda_version,
                            python_version=runtime_environment.python_version
                        ))

        self.cache = {}

        _LOGGER.debug("Analyzed image has the following symbols: %r", self.image_symbols)

    def _cache_and_return(self, package_name: str, package_version: str, index_url: str):
        cache_key = f"{package_name}-{package_version}-{index_url}"
        if cache_key not in self.cache:
            self.cache[cache_key] = set(self.context.graph.get_python_package_required_symbols(
                                package_name=package_name,
                                package_version=package_version,
                                index_url=index_url))

        return self.cache[cache_key]

    def run(self, package_versions: Generator[PackageVersion, None, None]):
        """If package requires non-present symbols remove it."""
        for pkg_vers in package_versions:
            package_symbols = self._cache_and_return(pkg_vers.name, pkg_vers.locked_version, pkg_vers.index.url)

            # Shortcut if package requires no symbols
            if package_symbols == set():
                yield pkg_vers
                continue

            missing_symbols = package_symbols - self.image_symbols
            if missing_symbols == set():
                yield pkg_vers
            else:
                # Log removed package
                _LOGGER.debug("Removed package %r-%r due to missing symbols.",
                              pkg_vers.name, pkg_vers.version)
                _LOGGER.debug("The following symbols are not present: %r", str(missing_symbols))
                continue
