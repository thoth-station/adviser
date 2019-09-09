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
from methodtools import lru_cache

import attr

from thoth.storages import GraphDatabase
from thoth.python import Project

_LOGGER = logging.getLogger(__name__)


@attr.s()
class PipelineProduct:
    """One product of stack generation pipeline."""

    project = attr.ib(type=Project)
    score = attr.ib(type=float)
    justification = attr.ib(type=typing.List[typing.Dict])
    graph = attr.ib(type=GraphDatabase)

    @lru_cache()
    def _do_get_python_package_version_hashes_sha256(
        self, package_name: str, package_version: str, index_url: str
    ) -> typing.List[str]:
        """A wrapper for ensuring cached results when querying graph database."""
        digests = self.graph.get_python_package_version_hashes_sha256(
            package_name, package_version, index_url
        )

        if not digests:
            _LOGGER.warning(
                "No hashes found for package %r in version %r from index %r",
                package_name,
                package_version,
                index_url,
            )

        return digests

    def _fill_package_digests(self) -> None:
        """Fill package digests stated in Pipfile.lock from graph database."""
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

            digests = self._do_get_python_package_version_hashes_sha256(
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
            )

            for digest in digests:
                package_version.hashes.append("sha256:" + digest)

    def finalize(self) -> None:
        """Finalize creation of a pipeline product."""
        self._fill_package_digests()
