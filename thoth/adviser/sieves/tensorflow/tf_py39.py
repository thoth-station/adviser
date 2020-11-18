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

"""A sieve that makes sure the right TensorFlow version is used when running on Python 3.9."""

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
class TensorFlowPython39Sieve(Sieve):
    """A sieve that makes sure the right TensorFlow version is used when running on Python 3.9."""

    CONFIGURATION_DEFAULT = {"package_name": "tensorflow"}
    _MESSAGE = "TensorFlow releases that do not support Python 3.9 filtered out"
    _LINK = jl("tf_py39")

    _message_logged = attr.ib(type=bool, default=False, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register this pipeline unit for adviser when CUDA is present."""
        if not builder_context.is_adviser_pipeline():
            return None

        if builder_context.recommendation_type in (RecommendationType.LATEST, RecommendationType.TESTING):
            # Use any TensorFlow for testing purposes or when resolving latest stack.
            return None

        python_version = builder_context.project.runtime_environment.python_version
        if python_version != "3.9":
            return None

        # Include this pipeline units in different configurations for tensorflow, intel-tensorflow and tensorflow-gpu.
        included_units = builder_context.get_included_sieves(cls)
        if len(included_units) == 3:
            return None
        if len(included_units) == 0:
            return {"package_name": "tensorflow"}
        elif len(included_units) == 1:
            return {"package_name": "tensorflow-gpu"}
        elif len(included_units) == 2:
            return {"package_name": "intel-tensorflow"}

        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._message_logged = False
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Use specific TensorFlow release based on Python version present in the runtime environment."""
        for package_version in package_versions:
            if package_version.semantic_version.release[:2] <= (2, 4):
                if not self._message_logged:
                    _LOGGER.warning("%s - %s", self._MESSAGE, self._LINK)
                    self.context.stack_info.append(
                        {
                            "type": "WARNING",
                            "message": self._MESSAGE,
                            "link": self._LINK,
                        }
                    )
                continue

            yield package_version
