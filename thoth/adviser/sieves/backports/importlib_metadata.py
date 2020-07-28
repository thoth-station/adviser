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

"""A sieve to remove backport of importlib-metadata intended for older Python versions."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion

from ...exceptions import SkipPackage
from ...sieve import Sieve

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class ImportlibMetadataBackportSieve(Sieve):
    """Remove backport of importlib-metadata, available in the standard library starting Python 3.8.

    https://pypi.org/project/importlib-metadata/
    https://docs.python.org/3/library/importlib.metadata.html
    """

    _MESSAGE = (
        "Dependency 'importlib-metadata' removed: importlib.metadata is available in "
        "Python standard library starting Python 3.8"
    )

    _logged = attr.ib(default=False, type=bool, init=False)

    def pre_run(self) -> None:
        """Initialize self before running."""
        self._logged = False

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include for Python 3.8 and above for adviser and dependency monkey runs."""
        if builder_context.is_included(cls) or builder_context.project.runtime_environment.python_version is None:
            return None

        python_version = tuple(map(int, builder_context.project.runtime_environment.python_version.split(".")))
        if python_version >= (3, 8):
            return {}

        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Remove dependency importlib-metadata for newer Python versions."""
        for package_version in package_versions:
            if package_version.name == "importlib-metadata":
                if not self._logged:
                    self.context.stack_info.append({"type": "WARNING", "message": self._MESSAGE})
                    _LOGGER.warning(self._MESSAGE)
                    self._logged = True

                raise SkipPackage

            yield package_version
