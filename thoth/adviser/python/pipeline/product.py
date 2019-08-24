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

"""Product of stack generation pipeline."""

import os
import logging
import typing
from functools import lru_cache

import attr

from thoth.storages import GraphDatabase
from thoth.python import Project

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PipelineProduct:
    """One product of stack generation pipeline."""

    project = attr.ib(type=Project)
    score = attr.ib(type=float)
    justification = attr.ib(type=typing.List[typing.Dict])

    def _fill_package_digests(self, graph: GraphDatabase) -> None:
        """Fill package digests stated in Pipfile.lock from graph database."""
        @lru_cache()
        def _do_get_python_package_version_hashes_sha256(pn: str, pv: str, iu: str) -> typing.List[str]:
            """A wrapper for ensuring cached results when querying graph database."""
            return graph.get_python_package_version_hashes_sha256(pn, pv, iu)

        if bool(os.getenv("THOTH_ADVISER_NO_DIGESTS", 0)):
            _LOGGER.warning("No digests will be provided as per user request")
            return

        for package_version in self.project.iter_dependencies_locked(with_devel=True):
            if package_version.hashes:
                # Already filled from the last run.
                continue

            _LOGGER.debug(
                "Retrieving package digests from graph database for package %r in version %r from index %r",
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
            )

            digests = _do_get_python_package_version_hashes_sha256(
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
            )

            if not digests:
                _LOGGER.warning(
                    "No hashes found for package %r in version %r from index %r",
                    package_version.name,
                    package_version.locked_version,
                    package_version.index.url,
                )
                continue

            for digest in digests:
                package_version.hashes.append("sha256:" + digest)

    def finalize(self, graph: GraphDatabase) -> None:
        """Finalize creation of a pipeline product."""
        self._fill_package_digests(graph)
