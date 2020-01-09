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

class AbiCompatability(Step):
    """Remove packages if the image being used doesn't have necessary ABI."""

    @classmethod
    def should_include(
        cls, builder_context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Remove indexes which are not enabled in pipeline configuration."""
        if not builder_context.is_included(cls):
            return {}

        return None

    def pre_run(self):
        runtime_environment = self.context.project.runtime_environment
        self.image_symbols = self.context.graph.get_image_symbols(
                            os_name=runtime_environment.operating_system.name,
                            os_version=runtime_environment.operating_system.version,
                            cuda_version=runtime_environment.cuda_version,
                            python_version=runtime_environment.python_version
                        )

    def run(self, package_versions: Generator[PackageVersion, None, None]):
        """If package requires non-present symbols remove it."""

        for package_version in package_versions:
            package_symbols = self.context.graph.get_python_package_required_symbols(
                                package_name=package_version.name,
                                package_version=package_version.version,
                                index_url=package_version.index)
            if(set(package_symbols) - set(self.image_symbols) == set()):
                # Say that package had correct symbols
                _LOGGER.debug("All symbols necessary for %r-%r are present.", package_version.name, package_version.version)
                yield package_version
            else:
                # Log removed package
                _LOGGER.debug("Removed package %r-%r due to missing symbols.", package_version.name, package_version.version)
                continue
