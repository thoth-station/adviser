#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""A boot that traces memory consumption of the adviser/dependency-monkey run.

This pipeline unit was designed to trace memory consumption of an adviser
or dependency-monkey run to spot possible unwanted memory usages. The pipeline
unit adds additional overhead so it is never registered implicitly and *must* be
explicitly turned on by a user (e.g. by providing explicit pipeline configuration).
"""

import linecache
import logging
import tracemalloc
from typing import Optional
from typing import Dict
from typing import Any
from typing import TYPE_CHECKING

import attr
from voluptuous import Optional as SchemaOptional
from voluptuous import Schema

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class MemTraceBoot(Boot):
    """A boot that traces memory consumption of the adviser/dependency-monkey run."""

    CONFIGURATION_DEFAULT = {
        "frame_count": 100,  # Number of frames traced.
        "top_limit": 100,  # Number of top mem usage consumers printed.
    }
    CONFIGURATION_SCHEMA = Schema({SchemaOptional("frame_count"): int,})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, never."""
        # Uncomment this to release the beast.
        # if not builder_context.is_included(cls):
        #     return {}
        return None

    def pre_run(self) -> None:
        """Initialize memory tracing."""
        _LOGGER.warning("Enabling memory tracing, this has negative impact on the overall pipeline performance")
        tracemalloc.start(self.configuration["frame_count"])

    @staticmethod
    def _display_top(snapshot: tracemalloc.Snapshot, *, key_type: str = "lineno", limit: int = 10) -> None:
        """Print top consumers.

        Inspired by Python docs:
          https://docs.python.org/3/library/tracemalloc.html#get-the-traceback-of-a-memory-block
        """
        snapshot = snapshot.filter_traces(
            (tracemalloc.Filter(False, "<frozen importlib._bootstrap>"), tracemalloc.Filter(False, "<unknown>"),)
        )
        top_stats = snapshot.statistics(key_type)

        print("Top %s lines" % limit)
        for index, stat in enumerate(top_stats[:limit], 1):
            frame = stat.traceback[0]
            print("#%s: %s:%s: %.1f KiB" % (index, frame.filename, frame.lineno, stat.size / 1024))
            line = linecache.getline(frame.filename, frame.lineno).strip()
            if line:
                print("    %s" % line)

        other = top_stats[limit:]
        if other:
            size = sum(stat.size for stat in other)
            print("%s other: %.1f KiB" % (len(other), size / 1024))
        total = sum(stat.size for stat in top_stats)
        print("Total allocated size: %.1f KiB" % (total / 1024))

    def post_run(self) -> None:
        """De-initialize memory tracing and print the stats."""
        _LOGGER.warning("Turning memory consumption tracing off and aggregating statistics; this might take a while...")
        snapshot = tracemalloc.take_snapshot()
        self._display_top(snapshot, limit=self.configuration["top_limit"])
        tracemalloc.stop()

    def run(self) -> None:
        """Do not perform anything valuable in the actual implementation."""
