#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""A wrap that links Python package version to Thoth Search UI."""

import os
from typing import TYPE_CHECKING
from typing import Generator
from typing import Dict
from typing import Any
from urllib.parse import quote

import attr
from ..state import State
from ..wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_THOTH_SEARCH_PACKAGE_URL = os.getenv(
    "THOTH_SEARCH_PACKAGE_URL",
    "https://thoth-station.ninja/search/package/{package_name}/"
    "{package_version}/{index_url}/{os_name}/{os_version}/{python_version}",
)


@attr.s(slots=True)
class ThothSearchPackageWrap(Wrap):
    """A wrap that links Python package to Thoth Search UI."""

    _search_package_url = attr.ib(type=str, default=_THOTH_SEARCH_PACKAGE_URL, kw_only=True)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[Any, Any], None, None]:
        """Include this wrap in adviser, once."""
        if not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def run(self, state: State) -> None:
        """Add a link to Thoth Search UI for each resolved package."""
        runtime_environment = self.context.project.runtime_environment
        for package_version_tuple in state.resolved_dependencies.values():
            state.justification.append(
                {
                    "type": "INFO",
                    "link": self._search_package_url.format(
                        package_name=quote(package_version_tuple[0]),
                        package_version=quote(package_version_tuple[1], safe=""),
                        index_url=quote(package_version_tuple[2], safe=""),
                        os_name=quote(runtime_environment.operating_system.name),
                        os_version=quote(runtime_environment.operating_system.version),
                        python_version=quote(runtime_environment.python_version),
                    ),
                    "message": f"Browse Thoth Search UI for '{package_version_tuple[0]}=={package_version_tuple[1]}'",
                    "package_name": package_version_tuple[0],
                }
            )
