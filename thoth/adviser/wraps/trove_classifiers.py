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

"""A wrap that provides information derived from Python trove classifiers."""

import logging
from enum import Enum
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from ..state import State
from ..wrap import Wrap
from thoth.adviser.enums import RecommendationType
from thoth.common import get_justification_link as jl

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


class _DevelopmentStatusEnum(Enum):
    """Development status trove classifier representation."""

    PLANNING = 1
    PRE_ALPHA = 2
    ALPHA = 3
    BETA = 4
    STABLE = 5
    MATURE = 6
    INACTIVE = 7

    @classmethod
    def from_str(cls, trove_classifier: str) -> Optional["_DevelopmentStatusEnum"]:
        """Get development status enum from a string representation."""
        trove_classifier.strip()

        if trove_classifier == "Development Status:: 1 - Planning":
            return cls.PLANNING

        if trove_classifier == "Development Status:: 2 - Pre - Alpha":
            return cls.PRE_ALPHA

        if trove_classifier == "Development Status:: 3 - Alpha":
            return cls.ALPHA

        if trove_classifier == "Development Status:: 4 - Beta":
            return cls.BETA

        if trove_classifier == "Development Status:: 5 - Production / Stable":
            return cls.STABLE

        if trove_classifier == "Development Status:: 6 - Mature":
            return cls.MATURE

        if trove_classifier == "Development Status:: 7 - Inactive":
            return cls.INACTIVE

        return None


class TroveClassifiersWrap(Wrap):
    """A wrap that provides information derived from Python trove classifiers."""

    _ENVIRONMENT_GPU_CUDA_PREFIX = "Environment :: GPU :: NVIDIA CUDA :: "
    _PROGRAMMING_LANGUAGE_PYTHON_PREFIX = "Programming Language :: Python :: "
    _DEVELOPMENT_STATUS_PREFIX = "Development Status:: "

    _JUSTIFICATION_LINK_PYTHON_VERSION = jl("trove_py")
    _JUSTIFICATION_LINK_USING_UNSTABLE = jl("trove_unstable")
    _JUSTIFICATION_LINK_USING_INACTIVE = jl("trove_inactive")
    _JUSTIFICATION_LINK_CUDA_VERSION = jl("trove_cuda")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[Any, Any], None, None]:
        """Include this wrap in adviser, once."""
        if builder_context.is_adviser_pipeline() and not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def _environment_gpu_cuda_version(self, package_name: str, state: State, trove_classifiers: List[str]) -> None:
        """Add justifications relevant relevant information for GPU CUDA."""
        cuda_version = self.context.project.runtime_environment.cuda_version
        if not cuda_version:
            return None

        cuda_version_trove_classifiers = []
        for trove_classifier in trove_classifiers:
            if not trove_classifier.startswith(self._ENVIRONMENT_GPU_CUDA_PREFIX):
                continue

            cuda_version_trove_classifier = trove_classifier[len(self._ENVIRONMENT_GPU_CUDA_PREFIX) :].strip()

            cuda_version_trove_classifier_parts = cuda_version_trove_classifier.split(".")
            if len(cuda_version_trove_classifier_parts) != 2:
                _LOGGER.debug("Unknown CUDA trove classifier: %r", cuda_version_trove_classifier)
                continue

            cuda_version_trove_classifiers.append(cuda_version_trove_classifier)

        if cuda_version_trove_classifiers and cuda_version not in cuda_version_trove_classifiers:
            state.justification.append(
                {
                    "type": "WARNING",
                    "link": self._JUSTIFICATION_LINK_CUDA_VERSION,
                    "message": f"No CUDA specific trove classifier matching CUDA version used {cuda_version!r}",
                    "package_name": package_name,
                }
            )

    def _development_status(self, package_name: str, state: State, trove_classifiers: List[str]) -> None:
        """Add justifications relevant for development status."""
        for trove_classifier in trove_classifiers:
            development_status = _DevelopmentStatusEnum.from_str(trove_classifier)
            if development_status is None:
                continue

            recommendation_type: RecommendationType = self.context.recommendation_type
            if self.context.recommendation_type not in (RecommendationType.TESTING, RecommendationType.LATEST):
                if development_status is not None and development_status.value < _DevelopmentStatusEnum.STABLE.value:
                    state.justification.append(
                        {
                            "type": "WARNING",
                            "link": self._JUSTIFICATION_LINK_USING_UNSTABLE,
                            "message": f"Development status stated in trove classifiers is "
                            f"{development_status.name.lower().replace('_', '-')!r} which might "
                            f"be not suitable to be used with recommendation type {recommendation_type.name.lower()!r}",
                            "package_name": package_name,
                        }
                    )

            if development_status == _DevelopmentStatusEnum.INACTIVE:
                state.justification.append(
                    {
                        "type": "WARNING",
                        "link": self._JUSTIFICATION_LINK_USING_INACTIVE,
                        "message": f"Inactive development status of {package_name!r} stated in trove classifiers",
                        "package_name": package_name,
                    }
                )

    def _programming_language_python(self, package_name: str, state: State, trove_classifiers: List[str]) -> None:
        """Add justification relevant for Python programming language."""
        python_version = self.context.project.runtime_environment.python_version
        if not python_version:
            return None

        py_trove_classifiers = []
        for trove_classifier in trove_classifiers:
            if not trove_classifier.startswith(self._PROGRAMMING_LANGUAGE_PYTHON_PREFIX):
                continue

            trove_python_version = trove_classifier[len(self._PROGRAMMING_LANGUAGE_PYTHON_PREFIX) :].strip()

            trove_python_version_parts = trove_python_version.split(".")
            if len(trove_python_version_parts) != 2:
                continue

            py_trove_classifiers.append(trove_python_version)

        if py_trove_classifiers and python_version not in py_trove_classifiers:
            state.justification.append(
                {
                    "type": "WARNING",
                    "link": self._JUSTIFICATION_LINK_PYTHON_VERSION,
                    "message": f"No Python specific trove classifier matching Python version used {python_version!r}",
                    "package_name": package_name,
                }
            )

    def run(self, state: State) -> None:
        """Add information derived from Python trove classifiers."""
        runtime_environment = self.context.project.runtime_environment
        operating_system = runtime_environment.operating_system
        os_name = operating_system.name
        os_version = operating_system.version
        python_version = runtime_environment.python_version

        for package_version_tuple in state.resolved_dependencies.values():
            package_name = package_version_tuple[0]

            trove_classifiers = [
                i.strip()
                for i in self.context.graph.get_python_package_version_trove_classifiers_all(
                    package_name=package_name,
                    package_version=package_version_tuple[1],
                    index_url=package_version_tuple[2],
                    os_name=os_name,
                    os_version=os_version,
                    python_version=python_version,
                )
            ]

            if not trove_classifiers:
                continue

            self._environment_gpu_cuda_version(package_name, state, trove_classifiers)
            self._development_status(package_name, state, trove_classifiers)
            self._programming_language_python(package_name, state, trove_classifiers)
