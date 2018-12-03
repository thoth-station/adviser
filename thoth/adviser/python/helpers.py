#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
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


"""Helper functions and utilities."""

from itertools import chain
import logging

from thoth.adviser.configuration import config
from thoth.storages import GraphDatabase

from thoth.python import Project
from thoth.python import Source

_LOGGER = logging.getLogger(__name__)


def fill_package_digests(generated_project: Project) -> Project:
    """Temporary fill package digests stated in Pipfile.lock."""
    for package_version in chain(generated_project.pipfile_lock.packages,
                                 generated_project.pipfile_lock.dev_packages):
        if package_version.hashes:
            # Already filled from the last run.
            continue

        if package_version.index:
            scanned_hashes = package_version.index.get_package_hashes(
                package_version.name,
                package_version.locked_version
            )
        else:
            for source in generated_project.pipfile.meta.sources.values():
                try:
                    scanned_hashes = source.get_package_hashes(
                        package_version.name,
                        package_version.locked_version
                    )
                    break
                except Exception:
                    continue
            else:
                raise ValueError("Unable to find package hashes")

        for entry in scanned_hashes:
            package_version.hashes.append('sha256:' + entry['sha256'])

    return generated_project


def fill_package_digests_from_graph(generated_project: Project, graph: GraphDatabase = None) -> Project:
    """Fill package digests stated in Pipfile.lock from graph database."""
    return generated_project

    if not graph:
        graph = GraphDatabase()
        graph.connect()

    for package_version in chain(generated_project.pipfile_lock.packages,
                                 generated_project.pipfile_lock.dev_packages):
        if package_version.hashes:
            # Already filled from the last run.
            continue
        
        _LOGGER.info(
            "Retrieving package digests from graph database for package %r in version %r from index %r",
            package_version.name, package_version.locked_version, package_version.index.url
        )

        digests = graph.get_python_package_version_hashes_sha256(
            package_version.name,
            package_version.locked_version,
            package_version.index.url
        )

        for digest in digests:
            package_version.hashes.append('sha256:' + digest)

    return generated_project
