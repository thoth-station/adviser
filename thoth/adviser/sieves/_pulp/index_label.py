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

"""A sieve that provides only packages available on Operate First Pulp instance."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion

from ...sieve import Sieve

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


class PulpIndexLabelSieve(Sieve):
    """A sieve that filters out packages that do not come from Operate First Pulp instance."""

    _stack_info_reported = attr.ib(type=bool, default=False, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[Any, Any], None, None]:
        """Include this wrap in adviser, if label pulp-index=solely is used."""
        if not builder_context.is_included(cls) and builder_context.labels.get("opf-pulp-indexes") == "solely":
            yield {}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Add information about Pulp use to stack information."""
        self._stack_info_reported = False
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Remove any packages that do not come from the Pulp instance."""
        from . import PULP_URL

        if not self._stack_info_reported:
            self.context.stack_info.append(
                {
                    "type": "INFO",
                    "message": "Using Operate First Pulp as a source of Python packages",
                    "link": PULP_URL,
                }
            )

        for package_version in package_versions:
            if package_version.index.url.startswith(PULP_URL):
                yield package_version
