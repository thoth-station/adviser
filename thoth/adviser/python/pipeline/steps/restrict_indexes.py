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

"""A step which removes indexes which should not be taken into account."""

import logging

from ..step import Step
from ..step_context import StepContext

_LOGGER = logging.getLogger(__name__)


class RestrictIndexes(Step):
    """Remove indexes from which packages should not be present in generated stacks."""

    def run(self, step_context: StepContext):
        """Remove indexes from which packages should not be present in generated stacks."""
        index_urls = set()
        for source in self.project.pipfile.meta.sources.values():
            index_urls.add(source.url)

        if not index_urls:
            _LOGGER.info(
                "No index URLs configured, no restriction on indexes will be done"
            )
            return

        for package_version in step_context.iter_all_dependencies():
            if package_version.index.url not in index_urls:
                package_tuple = package_version.to_tuple()
                _LOGGER.warning(
                    "Removing package %r - not in restricted indexes", package_tuple
                )
                with step_context.remove_package_tuples(package_tuple) as txn:
                    txn.commit()
