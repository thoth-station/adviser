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

"""Sieves that filters packages available on Operate First Pulp instance."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

from thoth.python import PackageVersion
from .index_label import PulpIndexLabelSieve

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


class NoPulpIndexLabelSieve(PulpIndexLabelSieve):
    """A sieve that filters out packages that come from Operate First Pulp instance."""

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[Any, Any], None, None]:
        """Include this wrap in adviser, if label pulp-index=disabled is used."""
        if not builder_context.is_included(cls) and builder_context.labels.get("opf-pulp-indexes") == "disabled":
            yield {}
            return None

        yield from ()
        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Remove any packages that do not come from the Pulp instance."""
        from . import PULP_URL

        if not self._stack_info_reported:
            self.context.stack_info.append(
                {
                    "type": "INFO",
                    "message": "Ignoring packages provided by the Operate First Pulp instance",
                    "link": PULP_URL,
                }
            )

        for package_version in package_versions:
            if not package_version.index.url.startswith(PULP_URL):
                yield package_version
