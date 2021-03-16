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

"""A base class for prescription based pipeline units."""

import abc
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from packaging.specifiers import SpecifierSet

import attr

from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.exceptions import EagerStopPipeline
from thoth.adviser.state import State
from thoth.common import get_justification_link as jl

from ...unit import Unit

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class UnitPrescription(Unit, metaclass=abc.ABCMeta):
    """A base class for implementing pipeline units based on prescription supplied."""

    _PRESCRIPTION: Optional[Dict[str, Any]] = None

    prescription = attr.ib(type=Dict[str, Any], kw_only=True)
    run_prescription = attr.ib(type=Dict[str, Any], kw_only=True)

    @prescription.default
    def _prescription_default(self) -> Dict[str, Any]:
        """Initialize prescription property."""
        if self._PRESCRIPTION is None:
            raise ValueError("No assigned prescription on the class level to be set")

        return self._PRESCRIPTION

    @run_prescription.default
    def _run_prescription_default(self) -> Dict[str, Any]:
        """Initialize the run prescription property."""
        if self._PRESCRIPTION is None:
            raise ValueError("No assigned prescription on the class level to be set")

        result: Dict[str, Any] = self._PRESCRIPTION["run"]
        return result

    @classmethod
    def get_unit_name(cls) -> str:
        """Get the name of the currect prescription unit."""
        if cls._PRESCRIPTION is None:
            raise ValueError("No prescription defined")

        name: str = cls._PRESCRIPTION["name"]
        return name

    @classmethod
    def set_prescription(cls, prescription: Dict[str, Any]) -> None:
        """Set prescription to the unit."""
        cls._PRESCRIPTION = prescription

    @classmethod
    def _should_include_base(cls, builder_context: "PipelineBuilderContext") -> bool:
        """Determine if this unit should be included."""
        if cls._PRESCRIPTION is None:
            raise ValueError("No prescription defined")

        should_include_dict = cls._PRESCRIPTION["should_include"]
        unit_name = cls.get_unit_name()

        times = should_include_dict.get("times")  # XXX: We allow values 0 or 1 in the schema described.
        if times is not None and builder_context.is_included(cls):
            return False

        if not should_include_dict.get("adviser_pipeline", False) and builder_context.is_adviser_pipeline():
            _LOGGER.debug("%s: Not registering for adviser pipeline", unit_name)
            return False
        elif should_include_dict.get("adviser_pipeline", False) and builder_context.is_adviser_pipeline():
            allowed_recommendation_types = should_include_dict.get("recommendation_types")
            if allowed_recommendation_types and builder_context.recommendation_type not in allowed_recommendation_types:
                _LOGGER.debug(
                    "%s: Not registering for adviser pipeline with recommendation type %s",
                    unit_name,
                    builder_context.recommendation_type,
                )
                return False

        if (
            not should_include_dict.get("dependency_monkey_pipeline", False)
            and builder_context.is_dependency_monkey_pipeline()
        ):
            _LOGGER.debug("%s: Not registering for dependency monkey pipeline", unit_name)
            return False
        elif (
            should_include_dict.get("dependency_monkey_pipeline", False)
            and builder_context.is_dependency_monkey_pipeline()
        ):
            allowed_decision_types = should_include_dict.get("decision_types")
            if allowed_decision_types and builder_context.decision_type not in allowed_decision_types:
                _LOGGER.debug(
                    "%s: Not registering for dependency monkey pipeline with decision type %s",
                    unit_name,
                    builder_context.decision_type,
                )
                return False

        runtime_environment_dict = should_include_dict.get("runtime_environment_dict", {})

        # Operating system.
        operating_system_dict = should_include_dict.get("operating_system", {})
        os_name = operating_system_dict.get("name")
        os_version = operating_system_dict.get("version")
        if os_name is not None and os_name != builder_context.project.runtime_environment.operating_system.name:
            _LOGGER.debug("%s: Not matching operating system name used", unit_name)
            return False

        if (
            os_version is not None
            and os_version != builder_context.project.runtime_environment.operating_system.version
        ):
            _LOGGER.debug("%s: Not matching operating system version used", unit_name)
            return False

        # Hardware.
        hardware_dict = runtime_environment_dict.get("hardware", {})
        cpu_family = hardware_dict.get("cpu_family")
        cpu_model = hardware_dict.get("cpu_model")
        gpu_model = hardware_dict.get("gpu_model")
        if cpu_family is not None and cpu_family != builder_context.project.runtime_environment.hardware.cpu_family:
            _LOGGER.debug("%s: Not matching CPU family used", unit_name)
            return False

        if cpu_model is not None and cpu_model != builder_context.project.runtime_environment.hardware.cpu_model:
            _LOGGER.debug("%s: Not matching CPU model used", unit_name)
            return False

        if gpu_model is not None and gpu_model != builder_context.project.runtime_environment.hardware.gpu_model:
            _LOGGER.debug("%s: Not matching GPU model used", unit_name)
            return False

        # Software present.
        python_version = runtime_environment_dict.get("python_version")
        if python_version is not None and python_version != runtime_environment_dict.get("python_version"):
            _LOGGER.debug("%s: Not matching Python version used", unit_name)
            return False

        cuda_version = runtime_environment_dict.get("cuda_version")
        if cuda_version is not None and cuda_version != runtime_environment_dict.get("cuda_version"):
            _LOGGER.debug("%s: Not matching CUDA version used", unit_name)
            return False

        platform = runtime_environment_dict.get("platform")
        if platform is not None and platform != runtime_environment_dict.get("platfrom"):
            _LOGGER.debug("%s: Not matching platform used", unit_name)
            return False

        openblas_version = runtime_environment_dict.get("openblas_version")
        if openblas_version is not None and openblas_version != runtime_environment_dict.get("openblas_version"):
            _LOGGER.debug("%s: Not matching openblas version used", unit_name)
            return False

        openmpi_version = runtime_environment_dict.get("openmpi_version")
        if openmpi_version is not None and openmpi_version != runtime_environment_dict.get("openmpi_version"):
            _LOGGER.debug("%s: Not matching openmpi version used", unit_name)
            return False

        cudnn_version = runtime_environment_dict.get("cudnn_version")
        if cudnn_version is not None and cudnn_version != runtime_environment_dict.get("cudnn_version"):
            _LOGGER.debug("%s: Not matching cudnn version used", unit_name)
            return False

        mkl_version = runtime_environment_dict.get("mkl_version")
        if mkl_version is not None and mkl_version != runtime_environment_dict.get("mkl_version"):
            _LOGGER.debug("%s: Not matching mkl version used", unit_name)
            return False

        base_image = runtime_environment_dict.get("base_image")
        if base_image is not None and base_image != runtime_environment_dict.get("base_image"):
            _LOGGER.debug("%s: Not matching base image used", unit_name)
            return False

        return True

    @classmethod
    def _prepare_justification_link(cls, entries: List[Dict[str, Any]]) -> None:
        """Prepare justification links before using them."""
        for entry in entries:
            link = entry.get("link")
            if link and not link.startswith(("https://", "http://")):
                entry["link"] = jl(link)

    def pre_run(self) -> None:
        """Prepare this pipeline unit before running it."""
        self._prepare_justification_link(self.run_prescription.get("stack_info", []))
        super().pre_run()

    def _run_log(self) -> None:
        """Log message specified in the run prescription."""
        log = self.run_prescription.get("log")
        if log:
            _LOGGER.log(level=getattr(logging, log["type"]), msg=f"{self.get_unit_name()}: {log['message']}")

    def _run_stack_info(self) -> None:
        """Add stack info if any prescribed."""
        stack_info = self.run_prescription.get("stack_info")
        if stack_info:
            self.context.stack_info.extend(stack_info)

    def _run_state(self, state: State) -> bool:
        """Check state match."""
        state_prescription = self.run_prescription["match"].get("state")
        if state_prescription:
            for resolved_dependency in state_prescription.get("resolved_dependencies", []):
                resolved = state.resolved_dependencies.get(resolved_dependency["name"])
                if not resolved:
                    return False

                specifier = SpecifierSet(resolved_dependency["version"])
                if resolved[1] not in specifier or resolved[2] != resolved_dependency["index_url"]:
                    return False

        return True

    def _run_base(self) -> None:
        """Implement base routines for run part of the prescription."""
        self._run_log()
        self._run_stack_info()

        not_acceptable = self.run_prescription.get("not_acceptable")
        if not_acceptable:
            raise NotAcceptable(not_acceptable)

        eager_stop_pipeline = self.run_prescription.get("eager_stop_pipeline")
        if eager_stop_pipeline:
            raise EagerStopPipeline(eager_stop_pipeline)
