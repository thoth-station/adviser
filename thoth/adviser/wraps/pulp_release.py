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

"""A wrap that links to a Pulp instance."""

import os
from typing import TYPE_CHECKING
from typing import Generator
from typing import Dict
from typing import Any

import attr
from ..state import State
from ..wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


@attr.s(slots=True)
class PulpReleaseWrap(Wrap):
    """A wrap that adds link to Red Hat's Pulp instance."""

    _PULP_URL = os.getenv("THOTH_ADVISER_DEPLOYMENT_PULP_URL_BASE", "https://pulp.operate-first.cloud/")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[Any, Any], None, None]:
        """Include this wrap in adviser, once."""
        if not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def run(self, state: State) -> None:
        """Add a link to Red Hat's Pulp instance."""
        for package_version_tuple in state.resolved_dependencies.values():
            if not package_version_tuple[2].startswith(self._PULP_URL):
                continue

            state.justification.append(
                {
                    "type": "INFO",
                    "link": package_version_tuple[2],
                    "message": f"Package {package_version_tuple[0]!r} is released on Operate First Pulp instance",
                    "package_name": package_version_tuple[0],
                }
            )
