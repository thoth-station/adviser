#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019 Fridolin Pokorny
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

"""Adapter for communicating with Isis API (API exposing project2vec).

Isis is, as of now, a simple API service. We did not generate swagger client,
instead, use this adapter for transparent communication.
"""

import os
import logging
import asyncio
import typing
from itertools import chain
from urllib.parse import urljoin
from collections import ChainMap
from functools import lru_cache

import requests


_LOGGER = logging.getLogger(__name__)


class _Singleton(type):
    """A metaclass for managing singleton instances."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Call a singleton instance."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]


class Isis(metaclass=_Singleton):
    """An adapter for communicating with Isis API from within adviser."""

    _NOT_FOUND_PERFORMANCE_IMPACT = 1.0
    _NO_ISIS_PERFORMANCE_IMPACT = 1.0

    def __init__(self, isis_api_url: str = None):
        """Initialize adapter for communicating with Isis API."""
        self.isis_api_url = isis_api_url or os.getenv("ISIS_API_URL")

        _LOGGER.debug("Isis API URL set to %r", self.isis_api_url)
        if not self.isis_api_url:
            _LOGGER.warning(
                "No Isis API configured, all performance related requests will have value %f",
                self._NO_ISIS_PERFORMANCE_IMPACT,
            )

    @lru_cache(maxsize=2048)
    def get_python_project_performance_import(
        self, project_name: str
    ) -> typing.Optional[float]:
        """Get performance import for a Python project.

        This function uses cache to reduce number of calls to Isis API.
        """
        if not self.isis_api_url:
            return self._NO_ISIS_PERFORMANCE_IMPACT

        response = requests.get(
            urljoin(
                self.isis_api_url, f"/api/v1/python/performance-impact/{project_name}"
            )
        )
        if response.status_code == 404:
            _LOGGER.debug(f"No records for project {project_name} found on Isis API")
            return None

        response.raise_for_status()
        return float(response.json()["result"]["performance_impact"])

    async def _get_python_package_performance_impact(
        self, package_tuple: tuple
    ) -> dict:
        """Get performance impact for a Python project.

        This is an async method suitable for map-reduce style results gathering - this method accepts package
        tuples instead of project names as an optimization not to map project names to package tuples.
        """
        project_name = package_tuple[0]
        return {package_tuple: self.get_python_project_performance_import(project_name)}

    def get_python_package_performance_impact_all(
        self, package_tuples: typing.Iterable[typing.Tuple[str, str, str]]
    ) -> dict:
        """Get performance impact for a list of packages.

        This accepts directly uses package tuples even the Isis API uses projects (package names).
        This is due to result gathering - optimization as we do not need to map back project names to package tuples.
        """
        tasks = []
        for package_tuple in package_tuples:
            task = asyncio.ensure_future(
                self._get_python_package_performance_impact(package_tuple)
            )
            tasks.append(task)

        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(asyncio.gather(*tasks))
        results_dict = list(chain(results))
        return dict(ChainMap(*results_dict))
