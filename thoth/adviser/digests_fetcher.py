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

"""Fetcher for fetching digests from the graph database."""

import logging
from typing import List
from typing import Dict

import attr
from thoth.storages import GraphDatabase
from thoth.python import DigestsFetcherBase


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class GraphDigestsFetcher(DigestsFetcherBase):  # type: ignore
    """Fetch digests from the graph database."""

    graph = attr.ib(type=GraphDatabase)

    @graph.default
    def _graph_default(self) -> GraphDatabase:
        """Get default graph instance if no explicitly provided."""
        graph = GraphDatabase()
        graph.connect()
        return graph

    def fetch_digests(
        self, package_name: str, package_version: str
    ) -> Dict[str, List[Dict[str, str]]]:
        """Fetch digests for the given package in specified version, consider only enabled indexes."""
        _LOGGER.debug(
            "Querying graph database for digests for package %r in version %r",
            package_name,
            package_version,
        )

        result = {}
        for index_url in self.graph.get_python_package_index_urls_all(enabled=True):
            query_result = self.graph.get_python_package_hashes_sha256(
                package_name, package_version, index_url, distinct=True
            )
            result[index_url] = [{"sha256": digest} for digest in query_result]

        return result
