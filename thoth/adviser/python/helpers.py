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

from thoth.adviser.python import Project


def fill_package_digests(generated_project: Project) -> Project:
    """Temporary fill package digests stated in Pipfile.lock."""
    from itertools import chain
    from thoth.adviser.configuration import config
    from thoth.adviser.python import Source

    # Pick the first warehouse for now.
    package_index = Source(config.warehouses[0])
    for package_version in chain(generated_project.pipfile_lock.packages,
                                 generated_project.pipfile_lock.dev_packages):
        if package_version.hashes:
            # Already filled from the last run.
            continue

        scanned_hashes = package_index.get_package_hashes(
            package_version.name,
            package_version.locked_version
        )

        for entry in scanned_hashes:
            package_version.hashes.append('sha256:' + entry['sha256'])

    return generated_project
