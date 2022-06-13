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

"""A boot to provide a link to Thoth search showing results in a UI."""

import logging
import os
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)

_THOTH_SEARCH_URL = os.getenv(
    "THOTH_SEARCH_ADVISER_URL", "https://thoth-station.ninja/search/advise/{document_id}/summary"
)
_DOCUMENT_ID = os.getenv("THOTH_DOCUMENT_ID", "UNKNOWN")


@attr.s(slots=True)
class ThothSearchBoot(Boot):
    """A boot to provide a link to Thoth search showing results in a UI."""

    _search_url = attr.ib(type=str, default=_THOTH_SEARCH_URL, kw_only=True)
    _document_id = attr.ib(type=str, default=_DOCUMENT_ID, kw_only=True)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, once, always."""
        if builder_context.is_adviser_pipeline() and not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Provide a link to Thoth search visualizing results."""
        self.context.stack_info.append(
            {
                "type": "INFO",
                "message": "Results can be browsed in Thoth search",
                "link": self._search_url.format(document_id=self._document_id),
            }
        )
