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

"""A boot to remove backport of importlib-metadata intended for older Python versions."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import TYPE_CHECKING

import attr
from ...boot import Boot

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class ImportlibMetadataBackportBoot(Boot):
    """Remove backport of importlib-metadata, available in the standard library starting Python 3.8.

    https://pypi.org/project/importlib-metadata/
    https://docs.python.org/3/library/importlib.metadata.html
    """

    _MESSAGE = (
        "Direct dependency 'importlib-metadata' removed: importlib.metadata is available in "
        "Python standard library starting Python 3.8"
    )

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include for Python 3.8 and above for adviser and dependency monkey runs."""
        if builder_context.is_included(cls) or builder_context.project.runtime_environment.python_version is None:
            return None

        if builder_context.project.runtime_environment.get_python_version_tuple() >= (3, 8) and (
            "importlib-metadata" in builder_context.project.pipfile.packages.packages
            or "importlib-metadata" in builder_context.project.pipfile.dev_packages.packages
        ):
            return {}

        return None

    def run(self) -> None:
        """Remove dependency importlib-metadata for newer Python versions."""
        _LOGGER.warning(self._MESSAGE)
        self.context.stack_info.append({"type": "INFO", "message": self._MESSAGE})
        self.context.project.pipfile.packages.packages.pop("importlib-metadata", None)
        self.context.project.pipfile.dev_packages.packages.pop("importlib-metadata", None)
