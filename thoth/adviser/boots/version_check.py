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

"""A boot to check for fully specified environment."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING
from itertools import chain
from packaging.version import Version
from packaging.specifiers import SpecifierSet

import attr
from thoth.common import get_justification_link as jl

from ..boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class VersionCheckBoot(Boot):
    """A boot that checks if versions are too lax."""

    _JUSTIFICATION_VERSION_TOO_LAX = jl("lax_version")

    # Some arbitrary large version to detect possibly version specifiers without any upper limit.
    _LARGE_VERSION = Version("9999999999")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, always."""
        if builder_context.is_adviser_pipeline() and not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def run(self) -> None:
        """Check if versions are not too lax."""
        for package_version in chain(
            self.context.project.pipfile.packages.packages.values(),
            self.context.project.pipfile.dev_packages.packages.values(),
        ):
            if not package_version.version or package_version.version == "*":
                self.context.stack_info.append(
                    {
                        "type": "WARNING",
                        "message": f"No version range specifier for {package_version.name!r} found, it is "
                        f"recommended to specify version ranges in requirements",
                        "link": self._JUSTIFICATION_VERSION_TOO_LAX,
                    }
                )
            elif self._LARGE_VERSION in SpecifierSet(package_version.version):
                self.context.stack_info.append(
                    {
                        "type": "WARNING",
                        "message": f"Version range specifier ({package_version.version!r}) for "
                        f"{package_version.name!r} might be too lax",
                        "link": self._JUSTIFICATION_VERSION_TOO_LAX,
                    }
                )
