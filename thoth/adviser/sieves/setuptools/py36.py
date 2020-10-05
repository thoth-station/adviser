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

"""A sieve to filter out old setuptools that do not work with Python 3.6."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from ...sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Py36SetuptoolsSieve(Sieve):
    """Filter out old setuptools that do not work with Python 3.6.

    https://github.com/pypa/setuptools/issues/378
    https://github.com/thoth-station/solver/issues/350
    """

    CONFIGURATION_DEFAULT = {"package_name": "setuptools"}
    _MESSAGE = "Package setuptools in versions <=17 do not work with Python 3.6"
    _JUSTIFICATION_LINK = jl("setuptools_py38")

    _message_logged = attr.ib(type=bool, default=False, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Include for Python 3.6 and adviser/dependency monkey runs."""
        if builder_context.is_included(cls):
            return None

        if builder_context.project.runtime_environment.python_version == "3.6":
            return {}

        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._message_logged = False
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out old setuptools that do not work with Python 3.6."""
        for package_version in package_versions:
            if package_version.semantic_version.major >= 17:
                yield package_version
            elif package_version.name == "setuptools" and not self._message_logged:
                self._message_logged = True
                self.context.stack_info.append(
                    {"type": "WARNING", "message": self._MESSAGE, "link": self._JUSTIFICATION_LINK}
                )
