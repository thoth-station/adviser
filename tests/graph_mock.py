#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019, 2020 Fridolin Pokorny
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
# type: ignore

"""Mocking responses from the graph database."""

import os
import typing
from collections import deque

import yaml
from .base import AdviserTestCase


class MockedGraphDatabase:
    """A mocked graph database using YAML files as data."""

    DEFAULT_COUNT = 100

    def __init__(self, database_file: str):
        """Initialize mock database."""
        with open(os.path.join(AdviserTestCase.data_dir, "graph", database_file), "r") as db_file:
            self.db = yaml.safe_load(db_file)
        # A map mapping package id to its tuples - this map can be used after the retrieve
        # transitive_dependencies_python call which fills this dict.
        self._id_map = {}
        self._reverse_id_map = {}

    def connect(self):
        """Connect to fake database (does nothing)."""
        pass

    def get_solved_python_package_versions_all(
        self,
        package_name: str,
        os_name: str = None,
        os_version: str = None,
        python_version: str = None,
        without_error: bool = True,
        count: bool = DEFAULT_COUNT,
        start_offset: bool = 0,
        distinct: bool = True,
        is_missing: bool = False,
    ) -> typing.List[tuple]:
        """Get all versions for the given Python package."""
        result = []
        for version, info in self.db.get(package_name, {}).items():
            for entry in info:
                result.append((package_name, version, entry["index_url"]))

        return result

    def retrieve_transitive_dependencies_python(self, package_name: str, version: str, index: str) -> typing.List[list]:
        """Retrieve transitive dependencies for the given Python package."""
        # Cache for checking whether we have triplet (package_name, version, index) already seen
        # to avoid recursion.
        result = []
        queue = deque()
        queue.append((package_name, version, index))

        while queue:
            package_name, package_version, index = queue.pop()

            if package_name not in self.db:
                raise ValueError(f"The given package {package_name!r} is not present in the database")

            info_entry = self.db[package_name].get(package_version)
            if not info_entry:
                raise ValueError(
                    f"The given package {package_name!r} has no record in the database for version {version!r}"
                )

            for version_entry in info_entry:
                for depends_on_entry in version_entry.get("depends_on", []):
                    for version in depends_on_entry["resolved"]:
                        queue.append(
                            [depends_on_entry["package_name"], version, depends_on_entry["index_url"],]
                        )

                        source = (package_name, package_version, index)
                        if source in self._reverse_id_map:
                            source_id = self._reverse_id_map[source]
                        else:
                            source_id = id(source)
                            self._id_map[source_id] = source
                            self._reverse_id_map[source] = source_id

                        destination = (
                            depends_on_entry["package_name"],
                            version,
                            depends_on_entry["index_url"],
                        )
                        if destination in self._reverse_id_map:
                            destination_id = self._reverse_id_map[destination]
                        else:
                            destination_id = id(destination)
                            self._id_map[destination_id] = destination
                            self._reverse_id_map[destination] = destination_id

                        result.append((source_id, False, destination_id))

        return result

    def get_python_package_tuples(self, python_package_node_ids: typing.Set[int]) -> typing.Dict[int, tuple]:
        """Get package tuples from fake database."""
        result = {}
        for python_package_id in python_package_node_ids:
            package_tuple = self._id_map.get(python_package_id)
            if package_tuple is None:
                raise ValueError(f"The given id {python_package_id} was never retrieved from the graph")
            result[python_package_id] = package_tuple

        return result
