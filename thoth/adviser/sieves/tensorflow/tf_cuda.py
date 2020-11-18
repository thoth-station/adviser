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

"""Recommend specific TensorFlow release based on CUDA version present in the runtime environment."""

import attr
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Generator
from typing import Dict
from typing import Set
from typing import FrozenSet
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
class TensorFlowCUDASieve(Sieve):
    """A sieve that makes sure the right TensorFlow version is used when CUDA is present in the runtime environment.

    See supported matrix at https://www.tensorflow.org/install/source#linux
    """

    CONFIGURATION_DEFAULT = {"package_name": "tensorflow"}
    _MESSAGE = f"Recommended TensorFlow that supports CUDA present in the runtime environment - see {jl('tf_cuda')}"

    _EMPTY: FrozenSet[Tuple[int, int]] = frozenset()
    _TF_1_CUDA_8_SUPPORT = frozenset({(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)})
    _TF_1_CUDA_9_SUPPORT = frozenset({(1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12)})
    _TF_1_CUDA_10_0_SUPPORT = frozenset({(1, 13), (1, 14), (1, 15)})
    _TF_2_CUDA_10_0_SUPPORT = frozenset({(2, 0)})
    _TF_2_CUDA_10_1_SUPPORT = frozenset({(2, 1), (2, 2), (2, 3)})
    _KNOWN_CUDA = frozenset({"8", "9", "10.0", "10.1"})

    # Holds tensorflow version for which a message was printed to logs.
    _messages_logged = attr.ib(type=Set[str], default=attr.Factory(set), init=False)
    # Holds a frozen set with versions of TensorFlow supported.
    _tf_1_cuda_support = attr.ib(type=FrozenSet[Tuple[int, int]], default=_EMPTY, init=False)
    _tf_2_cuda_support = attr.ib(type=FrozenSet[Tuple[int, int]], default=_EMPTY, init=False)

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._messages_logged.clear()
        cuda_version = self.context.project.runtime_environment.cuda_version

        if cuda_version == "8":
            self._tf_1_cuda_support = self._TF_1_CUDA_8_SUPPORT
            self._tf_2_cuda_support = self._EMPTY
        elif cuda_version == "9":
            self._tf_1_cuda_support = self._TF_1_CUDA_9_SUPPORT
            self._tf_2_cuda_support = self._EMPTY
        elif cuda_version == "10.0":
            self._tf_1_cuda_support = self._TF_1_CUDA_10_0_SUPPORT
            self._tf_2_cuda_support = self._TF_2_CUDA_10_0_SUPPORT
        elif cuda_version == "10.1":
            self._tf_1_cuda_support = self._EMPTY
            self._tf_2_cuda_support = self._TF_2_CUDA_10_1_SUPPORT
        else:
            _LOGGER.error("Unsupported CUDA version, cannot provide recommendations for TensorFlow")
            self._tf_1_cuda_support = self._EMPTY
            self._tf_2_cuda_support = self._EMPTY

        super().pre_run()

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register this pipeline unit for adviser when CUDA is present."""
        if not builder_context.is_adviser_pipeline():
            return None

        if builder_context.recommendation_type in (RecommendationType.LATEST, RecommendationType.TESTING):
            # Use any TensorFlow for testing purposes or when resolving latest stack.
            return None

        cuda_version = builder_context.project.runtime_environment.cuda_version
        if cuda_version is None:
            # No CUDA available in the given runtime environment.
            return None

        if cuda_version not in cls._KNOWN_CUDA:
            _LOGGER.warning(
                "Unable to perform recommendations for TensorFlow based on CUDA version: "
                "unknown CUDA version supplied - see %s",
                jl("tf_unknown_cuda"),
            )
            return None

        # Include this pipeline units in two configurations for tensorflow and tensorflow-gpu.
        included_units = builder_context.get_included_sieves(cls)
        if len(included_units) == 2:
            return None
        if len(included_units) == 0:
            return {"package_name": "tensorflow"}
        elif len(included_units) == 1:
            return {"package_name": "tensorflow-gpu"}

        return None

    def _log_unknown_tf_version(self, package_version: PackageVersion) -> None:
        """Log an unhandled TensorFlow release, this pipeline unit needs an update in such cases."""
        message = (
            f"Unhandled TensorFlow release {package_version.to_tuple()}, gracefully giving up recommending "
            f"TensorFlow based on CUDA version {self.context.project.runtime_environment.cuda_version!r}"
        )
        _LOGGER.error("%s - see %s", message, jl("cuda_unknown_tf"))
        self.context.stack_info.append(
            {
                "type": "ERROR",
                "message": message,
                "link": jl("cuda_unknown_tf"),
            }
        )

    def _maybe_log_no_recommendations(self, package_version: PackageVersion) -> None:
        """Log no recommendations are given for the given configuration."""
        if package_version.locked_version not in self._messages_logged:
            message = (
                f"Not recommending TensorFlow in version {package_version.locked_version!r} as this version "
                f"is not supported on CUDA in version {self.context.project.runtime_environment.cuda_version!r}"
            )
            link = jl("tf_no_cuda")
            _LOGGER.warning("%s - see %s", message, link)
            self._messages_logged.add(package_version.locked_version)
            self.context.stack_info.append({"type": "ERROR", "message": message, "link": link})

    def _yield_tensorflow(self, package_version: PackageVersion) -> bool:
        """Handle a tensorflow release."""
        tf_semantic_version = package_version.semantic_version.release[:2]

        if tf_semantic_version[0] == 1:
            self._maybe_log_no_recommendations(package_version)
            return False
        elif tf_semantic_version <= (2, 3):
            if tf_semantic_version in self._tf_2_cuda_support:
                return True

            self._maybe_log_no_recommendations(package_version)
            return False

        self._log_unknown_tf_version(package_version)
        return True

    def _yield_tensorflow_gpu(self, package_version: PackageVersion) -> bool:
        """Handle a tensorflow-gpu release."""
        if package_version.semantic_version.release[0] == 1:
            if package_version.semantic_version.release[:2] in self._tf_1_cuda_support:
                return True

            self._maybe_log_no_recommendations(package_version)
            return False
        elif package_version.semantic_version.release[0] == 2:
            # tensorflow-gpu>=2 acts as tensorflow>=2
            return self._yield_tensorflow(package_version)

        self._log_unknown_tf_version(package_version)
        return True

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Use specific TensorFlow release based on CUDA version present in the runtime environment."""
        for package_version in package_versions:
            if package_version.name == "tensorflow":
                if self._yield_tensorflow(package_version):
                    yield package_version
            elif package_version.name == "tensorflow-gpu":
                if self._yield_tensorflow_gpu(package_version):
                    yield package_version
