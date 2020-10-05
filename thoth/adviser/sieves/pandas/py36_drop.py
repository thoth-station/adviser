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

"""Sieve Pandas>=1.2 on Python 3.6 as Pandas>=1.2 dropped Python 3.6 support."""

import attr
from typing import Any
from typing import Optional
from typing import Generator
from typing import Dict
from typing import TYPE_CHECKING
import logging

from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from ...enums import RecommendationType
from ...sieve import Sieve


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PandasPy36Sieve(Sieve):
    """A sieve that makes sure Pandas>=1.2 is not used on Python 3.6 or older.

    See https://github.com/pandas-dev/pandas/pull/35214
    """

    CONFIGURATION_DEFAULT = {"package_name": "pandas"}
    _MESSAGE = f"Pandas in versions >=1.2 dropped Python 3.6 support"
    _JUSTIFICATION_LINK = jl("pandas_py36_drop")

    _message_logged = attr.ib(type=bool, default=False, init=False)

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._message_logged = False
        super().pre_run()

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register this pipeline unit for adviser when Python 3.6 is used, not latest/testing recommendations."""
        if not builder_context.is_adviser_pipeline() or builder_context.is_included(cls):
            return None

        if builder_context.recommendation_type in (RecommendationType.LATEST, RecommendationType.TESTING):
            return None

        if builder_context.project.runtime_environment.get_python_version_tuple() > (3, 6):
            # Not a Python 3.6 or older environment.
            return None

        return {}

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Do not use Pandas>=1.2 on Python 3.6."""
        for package_version in package_versions:
            if package_version.semantic_version.release[:2] < (1, 2):
                yield package_version
            elif not self._message_logged:
                self._message_logged = True
                _LOGGER.warning("%s - see %s", self._MESSAGE, self._JUSTIFICATION_LINK)
                self.context.stack_info.append(
                    {"type": "WARNING", "message": self._MESSAGE, "link": self._JUSTIFICATION_LINK}
                )
