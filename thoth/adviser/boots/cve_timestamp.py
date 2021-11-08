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

"""A boot to provide information about the last CVE update."""

import logging
import os
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.common import datetime2datetime_str
from thoth.common import get_justification_link as jl

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class CveTimestampBoot(Boot):
    """A boot to provide information about the last CVE update."""

    _CVE_TIMESTAMP_DAYS_WARNING = int(os.getenv("THOTH_ADVISER_CVE_TIMESTAMP_DAYS_WARNING", 7))

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, once, always."""
        if builder_context.is_adviser_pipeline() and not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Check CVE timestamp and provide it to users."""
        cve_timestamp = self.context.graph.get_cve_timestamp()
        if cve_timestamp is None:
            message = "No CVE timestamp information found in the database"
            self.context.stack_info.append(
                {
                    "message": message,
                    "type": "WARNING",
                    "link": jl("no_cve_timestamp"),
                }
            )
            return

        days = (datetime.utcnow() - cve_timestamp).days
        self.context.stack_info.append(
            {
                "type": "WARNING" if days > self._CVE_TIMESTAMP_DAYS_WARNING else "INFO",
                "message": f"CVE database of known vulnerabilities for Python packages was "
                f"updated at {datetime2datetime_str(cve_timestamp)!r}",
                "link": jl("cve_timestamp"),
            }
        )
