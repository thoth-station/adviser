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

"""Filter out software stacks allowing the pipeline to produce just one software stack with specific package.

This stride will allow the pipeline to produce a stack with only a specific package-version just once - e.g. if
two or more software stacks could be resolved with tensorflow==2.0.0, this stride will allow the
pipeline to produce just one software stack with tensorflow==2.0.0, other software stacks will be filtered out.
"""

import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

import attr

from ..state import State
from ..stride import Stride
from ..exceptions import StrideError
from ..exceptions import NotAcceptable

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class OneVersionStride(Stride):
    """Filter out software stacks allowing the pipeline to produce just one software stack with specific package."""

    CONFIGURATION_DEFAULT = {
        "package_name": None,
        "only_once": True,
    }

    version_seen = attr.ib(type=Optional[str], default=None)

    @classmethod
    def should_include(
        cls, builder_context: "PipelineBuilderContext"
    ) -> Optional[Dict[str, Any]]:
        """Include this pipeline unit only if user asks for it explicitly."""
        return None

    def pre_run(self) -> None:
        """Initialize internal state of the unit."""
        self.version_seen = None

        if self.configuration["package_name"] is None:
            raise StrideError(f"No package name provided to the {self.__class__.__name__!r} pipeline unit")

    def run(self, state: State) -> None:
        """Filter out software stacks, allow only a package with specific version being produced just once."""
        package_tuple = state.resolved_dependencies.get(self.configuration["package_name"])
        if package_tuple is None:
            return

        if self.version_seen is None:
            # First time seen, mark and continue.
            self.version_seen = package_tuple[1]
            return

        if self.version_seen == package_tuple[1] and not self.configuration["only_once"]:
            return

        if self.version_seen == package_tuple[1]:
            raise NotAcceptable(
                f"Package {package_tuple[0]!r} in version {package_tuple[1]} was "
                "already seen and only_once flag was set"
            )

        raise NotAcceptable(
            f"Package {package_tuple[0]!r} was already seen in version {self.version_seen!r}, "
            f"not accepting stack that has the given package in version {package_tuple[1]!r}"
        )
