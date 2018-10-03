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

"""Mocking responses from the graph database."""

import os
import typing
from functools import wraps
from collections import deque

import yaml
import mock

from base import AdviserTestCase

from thoth.storages.graph import GraphDatabase


class _MockedGraphDatabase:
    """A mocked graph database using YAML files as data."""

    def __init__(self, database_file: str):
        with open(os.path.join(AdviserTestCase.data_dir, 'graph', database_file), 'r') as db_file:
            self.db = yaml.load(db_file)

    def get_all_versions_python_package(self, package_name: str) -> typing.List[str]:
        """Get all versions for the given Python package."""
        return list(self.db.get(package_name, {}).keys())

    def retrieve_transitive_dependencies_python(self, package_name: str, version: str,
                                                index: str) -> typing.List[list]:
        """Retrieve transitive dependencies for the given Python package."""
        # Cache for checking whether we have triplet (package_name, version, index) already seen
        # to avoid recursion.
        seen = {}
        result = []
        queue = deque()
        queue.append((package_name, version, index))

        while queue:
            package_name, package_version, index = queue.pop()

            if package_name not in self.db:
                raise ValueError(f"The given package {package_name!r} is not present in the database")

            version_entry = self.db[package_name].get(version)
            if not version_entry:
                raise ValueError(
                    f"The given package {package_name!r} has no record in the database for version {version!r}"
                )

            for depends_on_entry in version_entry.get('depends_on', []):
                for version in depends_on_entry['resolved']:
                    queue.append(
                        [depends_on_entry['package_name'], version, depends_on_entry['index']]
                    )
                    result.append((
                        {
                            'package_name': package_name, 'version': package_version, 'index': index
                        },
                        {'depends_on': depends_on_entry['version_range']},
                        {
                            'package_name': depends_on_entry['package_name'],
                            'version': version,
                            'index': depends_on_entry['index']
                        }
                    ))

        return result


def with_graph_db_mock(database_file: str) -> typing.Callable:
    """A wrapper for mocking responses from the database."""
    def wrapped(func: typing.Callable) -> typing.Callable:
        def wrapper(*args, **kwargs):
            with mock.patch('thoth.storages.graph.janusgraph.GraphDatabase') as MockClass:
                MockClass.return_value = _MockedGraphDatabase(database_file)
                return func(*args, **kwargs)

        return wrapper

    return wrapped
