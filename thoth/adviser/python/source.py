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

"""Representation of source (index) for Python packages."""

import logging
import typing
import hashlib
from functools import lru_cache

import attr
import requests
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


@attr.s(frozen=True, slots=True)
class Source:
    """Representation of source (Python index) for Python packages."""

    name = attr.ib(type=str)
    url = attr.ib(type=str)
    verify_ssl = attr.ib(type=bool)
    warehouse = attr.ib(type=bool)
    warehouse_api_url = attr.ib(default=None, type=str)

    def get_api_url(self):
        """Construct URL to Warehouse instance."""
        if self.warehouse_api_url:
            return self.warehouse_api_url

        return self.url[:-len('/simple')] + '/pypi'

    @classmethod
    def from_dict(cls, dict_: dict):
        """Parse source from its dictionary representation."""
        _LOGGER.debug("Parsing package source to dict representation")
        dict_ = dict(dict_)
        instance = cls(
            name=dict_.pop('name'),
            url=dict_.pop('url'),
            verify_ssl=dict_.pop('verify_ssl'),
            warehouse=dict_.pop('warehouse', False)
        )

        if dict_:
            _LOGGER.warning("Ignored source configuration entries: %s", dict_)

        return instance

    def to_dict(self, include_warehouse: bool = False) -> dict:
        """Convert source definition to its dict representation."""
        _LOGGER.debug("Converting package source to dict representation")
        result = {
            'url': self.url,
            'verify_ssl': self.verify_ssl,
            'name': self.name,
        }

        if include_warehouse:
            result['warehouse'] = self.warehouse

        return result

    def _warehouse_get_api_package_info(self, package_name: str, package_version: str) -> dict:
        """Use API of the deployed Warehouse to gather package information."""
        url = self.get_api_url() + f'/{package_name}/{package_version}/json'
        _LOGGER.debug("Gathering information from Warehouse API: %r", url)
        response = requests.get(url, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()

    def _warehouse_get_package_hashes(self, package_name: str, package_version: str) -> typing.List[dict]:
        """Gather information about SHA hashes available for the given package-version release."""
        package_info = self._warehouse_get_api_package_info(package_name, package_version)

        result = []
        for item in package_info['urls']:
            result.append({
                'name': item['filename'],
                'sha256': item['digests']['sha256']
            })

        return result

    def _download_artifacts_sha(self, package_name: str, package_version: str) -> typing.Generator[tuple, None, None]:
        """Download the given artifact from Warehouse and compute its SHA."""
        # TODO: uncomment once AICoE index will be fixed
        # url = self.url + f'{package_name}'
        url = self.url

        _LOGGER.debug(f"Discovering package %r artifacts from %r", package_name, url)
        response = requests.get(url, verify=self.verify_ssl)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        links = soup.find_all('a')
        for link in links:
            artifact_name = str(link['href']).rsplit('/', maxsplit=1)
            if len(artifact_name) == 2:
                # If full URL provided by index.
                artifact_name = artifact_name[1]
            else:
                artifact_name = artifact_name[0]

            if not artifact_name.startswith(package_name) or not artifact_name.endswith(('.tar.gz', '.whl')):
                _LOGGER.debug("Link does not look like a package for %r: %r", package_name, link['href'])
                continue

            if not artifact_name.startswith(f"{package_name}-{package_version}"):
                # TODO: this logic has to be improved as package version can be a suffix of another package version:
                #   mypackage-1.0.whl, mypackage-1.0.0.whl, ...
                # This will require parsing based on PEP or some better logic.
                _LOGGER.debug("Skipping link based on prefix (not artifact name?): %r", link['href'])
                continue

            artifact_url = f"{url}/{artifact_name}"
            _LOGGER.debug("Downloading artifact from url %r", artifact_url)
            response = requests.get(artifact_url, verify=self.verify_ssl, stream=True)
            response.raise_for_status()

            digest = hashlib.sha256()
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    digest.update(chunk)

            digest = digest.hexdigest()
            _LOGGER.debug("Computed artifact sha256 digest for %r: %s", artifact_url, digest)
            yield artifact_name, digest

    @lru_cache(maxsize=10)
    def get_package_hashes(self, package_name: str, package_version: str) -> list:
        """Get information about release hashes available in this source index."""
        if self.warehouse:
            return self._warehouse_get_package_hashes(package_name, package_version)

        return [
            {
                'name': name,
                'sha56': digest
            } for name, digest in self._download_artifacts_sha(package_name, package_version)
        ]
