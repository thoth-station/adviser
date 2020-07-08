#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""A sieve for filtering out disabled Python package indexes."""

import logging
from typing import Any
from typing import Optional
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from thoth.storages.exceptions import NotFoundError

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PackageIndexSieve(Sieve):
    """Filter out disabled Python package indexes."""

    _cached_records: Dict[str, Optional[bool]] = attr.ib(default=attr.Factory(dict), kw_only=True)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Remove indexes which are not enabled in pipeline configuration."""
        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out package versions based on disabled Python package index."""
        for package_version in package_versions:
            if package_version.index.url in self._cached_records:
                is_enabled = self._cached_records[package_version.index.url]
            else:
                try:
                    is_enabled = self.context.graph.is_python_package_index_enabled(package_version.index.url)
                except NotFoundError:
                    # A special value of None marks non-existing index in thoth's knowledge base.
                    is_enabled = None

            self._cached_records[package_version.index.url] = is_enabled
            if is_enabled is None:
                _LOGGER.debug(
                    "Removing Python package version %r as used index is not registered", package_version.to_tuple(),
                )
                continue

            if not is_enabled:
                _LOGGER.debug(
                    "Removing Python package version %r as used index is not enabled", package_version.to_tuple(),
                )
                continue

            yield package_version
