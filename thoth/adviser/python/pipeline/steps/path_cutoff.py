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

"""A path based cut off optimization to reduce number of packages traversed."""

import logging

from ..step import Step
from ..step_context import StepContext
from ..exceptions import CannotRemovePackage

_LOGGER = logging.getLogger(__name__)


class PathCutoff(Step):
    """A path based cut off optimization.

    This step cuts off paths which do not have any positive score. The
    size of dependency graph is reduced this way making the resolution algorithm
    create results with positive score much faster.

    Run this path step after semver sort step to ensure as latest packages as
    possible are present in stacks.
    """

    def run(self, step_context: StepContext):
        """Run filtering of paths based on their score."""
        for score, path in step_context.iter_paths_with_score():
            if score > 0:
                continue

            try:
                with step_context.change(graceful=False) as change:
                    for package_tuple in path:
                        change.remove_package_tuple(package_tuple)
            except CannotRemovePackage as exc:
                _LOGGER.debug(
                    "Kept path with score %f - cannot be removed %s, path: %r",
                    score, str(exc), path
                )
