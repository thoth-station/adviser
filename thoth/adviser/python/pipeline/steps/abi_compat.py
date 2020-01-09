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

from thoth.adviser.python.exceptions import UnableLock
from thoth.adviser.python.dependency_graph import CannotRemovePackage

from ..step_context import StepContext
from ..step import Step

_LOGGER = logging.getLogger(__name__)

class AbiCompatability(Step):
    """Remove packages if the image being used doesn't have necessary ABI."""
    def run(self, step_context: StepContext):
        runtime_environment = self.project.runtime_environment
        image_symbols = self.graph.get_image_symbols(
                            # environment_name=runtime_environment.environment_name, 
                            os_name=runtime_environment.operating_system.name,
                            os_version=runtime_environment.operating_system.version,
                            cuda_version=runtime_environment.cuda_version,
                            python_version=runtime_environment.python_version
                        )

        for package_tuple in step_context.iter_all_dependencies_tuple():
            package_symbols = self.graph.get_python_package_required_symbols(
                                package_name=package_tuple[0], 
                                package_version=package_tuple[1], 
                                index_url=package_tuple[2])
            if(set(package_symbols) - set(image_symbols) == set()):
                _LOGGER.debug("Removing package %s because it requires ABI symbols not provided by the given image.")
                try:
                    with step_context.remove_package_tuples(package_tuple) as txn:
                        txn.commit()
                except CannotRemovePackage as exc:
                    _LOGGER.error("Cannot produce stack: %s", str(exc))
                    raise

