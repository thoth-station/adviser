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

"""A boot to check for version clashes in packages and dev packages."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import TYPE_CHECKING

import attr

from ..boot import Boot
from ..exceptions import CannotProduceStack

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class VersionClashBoot(Boot):
    """Check for version clashes in packages and dev-packages.

    Note the implementation does not resolve, so just exact match is checked. Clashes
    during resolution are reported by resolver.
    """

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, always."""
        if not builder_context.is_included(cls):
            return {}

        return None

    def run(self) -> None:
        """Check for version clash in packages."""
        for package_version in self.context.project.pipfile.packages:
            if not package_version.is_locked():
                continue

            dev_package_version = self.context.project.pipfile.dev_packages.get(package_version.name)

            if dev_package_version is None or not dev_package_version.is_locked():
                continue

            if package_version.locked_version != dev_package_version.locked_version:
                raise CannotProduceStack(
                    f"Package {package_version.name!r} is locked to {package_version.locked_version!r} "
                    f"in packages section, but in dev section it is locked to {package_version.locked_version!r}"
                )
