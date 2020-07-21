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

"""A boot to remove backport of importlib-resources intended for older Python versions."""

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
class ImportlibResourcesBackportBoot(Boot):
    """Remove backport of importlib-resources, available in the standard library starting Python 3.8.

    https://pypi.org/project/importlib-resources/
    https://docs.python.org/3/library/importlib.html
    https://docs.python.org/3/library/importlib.metadata.html
    """

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include for Python 3.8 and above for adviser and dependency monkey runs."""
        if builder_context.is_included(cls) or builder_context.project.runtime_environment.python_version is None:
            return None

        python_version = tuple(map(int, builder_context.project.runtime_environment.python_version.split(".")))
        if python_version >= (3, 8) and (
            "importlib-resources" in builder_context.project.pipfile.packages.packages
            or "importlib-resources" in builder_context.project.pipfile.dev_packages.packages
        ):
            return {}

        return None

    def run(self) -> None:
        """Remove dependency importlib-resources for newer Python versions."""
        _LOGGER.warning(
            "Removing direct dependency 'importlib-resources': importlib.pkg_resources is available in Python standard "
            "library starting Python 3.8"
        )
        self.context.project.pipfile.packages.packages.pop("importlib-resources", None)
        self.context.project.pipfile.dev_packages.packages.pop("importlib-resources", None)
