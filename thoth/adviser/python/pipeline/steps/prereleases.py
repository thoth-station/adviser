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

"""A step which cuts down pre-releases in paths if user does not want them."""

import logging

from thoth.adviser.python.dependency_graph import CannotRemovePackage

from ..step import Step
from ..step_context import StepContext

_LOGGER = logging.getLogger(__name__)


class CutPreReleases(Step):
    """Cut-off pre-releases if project does not explicitly allows them."""

    _DEBUG_SKIP_REPORTED = False

    def run(self, step_context: StepContext):
        """Cut-off pre-releases if project does not explicitly allows them."""
        if self.project.prereleases_allowed:
            if self._DEBUG_SKIP_REPORTED is False:
                _LOGGER.info(
                    "Project accepts pre-releases, skipping cutting pre-releases step"
                )
                self._DEBUG_SKIP_REPORTED = True
            return
        else:
            # Keep this branch so we reset flag if another project is used.
            self._DEBUG_SKIP_REPORTED = False

        for package_version in step_context.iter_all_dependencies():
            if package_version.semantic_version.prerelease:
                package_tuple = package_version.to_tuple()
                _LOGGER.debug(
                    "Removing package %r - pre-releases are disabled", package_tuple
                )
                try:
                    with step_context.remove_package_tuples(package_tuple) as txn:
                        txn.commit()
                except CannotRemovePackage as exc:
                    _LOGGER.error("Cannot produce stack: %s", str(exc))
                    raise
