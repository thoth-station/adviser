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

"""Fetcher for fetching digests from the graph database."""

import logging

from thoth.storages import GraphDatabase
from thoth.python import DigestsFetcherBase
from thoth.python import Source


_LOGGER = logging.getLogger(__name__)


class GraphDigestsFetcher(DigestsFetcherBase):
    """Fetch digests from the graph database."""

    def __init__(self, graph: GraphDatabase = None):
        if not graph:
            graph = GraphDatabase()
            graph.connect()

        self.graph = graph

    def fetch_digests(self, package_name: str, package_version: str) -> dict:
        """Fetch digests for the given package in specified version as stored in the graph database."""
        _LOGGER.debug(
            "Querying graph database for digests for package %r in version %r",
            package_name,
            package_version,
        )
        query_result = self.graph.get_all_python_package_version_hashes_sha256(
            package_name, package_version
        )

        result = {}
        for index_url, digest in query_result:
            # First we create a set of digests that we later on convert so that
            # we are compatible with DigestsFetcherBase result
            if index_url not in result:
                result[index_url] = set()

            result[index_url].add(digest)

        for index_url, digests in result.items():
            result[index_url] = [{"sha256": digest} for digest in digests]

        return result
