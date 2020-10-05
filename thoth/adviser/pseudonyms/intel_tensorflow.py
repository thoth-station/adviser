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

"""A TensorFlow pseudonym."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Tuple
from typing import FrozenSet
from typing import TYPE_CHECKING

import attr
from thoth.adviser.enums import RecommendationType
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from ..pseudonym import Pseudonym

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class IntelTensorFlowPseudonym(Pseudonym):
    """A TensorFlow pseudonym to map intel-tensorflow to tensorflow packages."""

    CONFIGURATION_DEFAULT = {"package_name": "tensorflow"}
    _LINK = jl("tf_intel")

    _pseudonyms = attr.ib(type=Optional[FrozenSet[str]], default=None, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self."""
        if builder_context.project.runtime_environment.cuda_version is not None:
            # No intel-tensorflow in GPU enabled environments.
            return None

        if builder_context.is_adviser_pipeline() and builder_context.recommendation_type != RecommendationType.LATEST:
            # Register self for tensorflow and tensorflow-cpu.
            included_units = builder_context.get_included_pseudonyms(cls)
            if len(included_units) == 2:
                return None
            elif len(included_units) == 0:
                return {"package_name": "tensorflow"}
            elif len(included_units) == 1:
                return {"package_name": "tensorflow-cpu"}

        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._pseudonyms = None
        super().pre_run()

    def run(self, package_version: PackageVersion) -> Generator[Tuple[str, str, str], None, None]:
        """Map TensorFlow packages to their alternatives."""
        if package_version.index.url != "https://pypi.org/simple":
            return None

        if self._pseudonyms is None:
            # Be lazy with queries to the database.
            _LOGGER.warning(
                "Considering also intel-tensorflow package as an alternative to TensorFlow - see %s", self._LINK
            )
            runtime_environment = self.context.project.runtime_environment
            self._pseudonyms = frozenset(
                {
                    i[1]
                    for i in self.context.graph.get_solved_python_package_versions_all(
                        package_name="intel-tensorflow",
                        package_version=None,
                        index_url="https://pypi.org/simple",
                        count=None,
                        os_name=runtime_environment.operating_system.name,
                        os_version=runtime_environment.operating_system.version,
                        python_version=runtime_environment.python_version,
                        distinct=True,
                        is_missing=False,
                    )
                }
            )

        if package_version.locked_version in self._pseudonyms:
            yield "intel-tensorflow", package_version.locked_version, "https://pypi.org/simple"
