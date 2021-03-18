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

        times = should_include_dict.get("times", 1)  # XXX: We allow values 0 or 1 in the schema described.
        if times == 0 or builder_context.is_included(cls):
            return False

        adviser_pipeline = should_include_dict.get("adviser_pipeline", False)
        if not adviser_pipeline and builder_context.is_adviser_pipeline():
            _LOGGER.debug("%s: Not registering for adviser pipeline", unit_name)
            return False
        elif adviser_pipeline and builder_context.is_adviser_pipeline():
            allowed_recommendation_types = should_include_dict.get("recommendation_types")
            if (
                allowed_recommendation_types is not None
                and builder_context.recommendation_type is not None
                and builder_context.recommendation_type.name.lower() not in allowed_recommendation_types
            ):
                _LOGGER.debug(
                    "%s: Not registering for adviser pipeline with recommendation type %s",
                    unit_name,
                    builder_context.recommendation_type.name,
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
            if (
                allowed_decision_types is not None
                and builder_context.decision_type is not None
                and builder_context.decision_type.name.lower() not in allowed_decision_types
            ):
                _LOGGER.debug(
                    "%s: Not registering for dependency monkey pipeline with decision type %s",
                    unit_name,
                    builder_context.decision_type.name,
                )
                return False

        # Dependencies.
        dependencies = should_include_dict.get("dependencies", {})
        for boot_name in dependencies.get("boots", []):
            if boot_name not in builder_context.get_included_boot_names():
                _LOGGER.debug("%s: Not registering as dependency on boot %r is not satisfied", unit_name, boot_name)
                return False

        for pseudonym_name in dependencies.get("pseudonyms", []):
            if pseudonym_name not in builder_context.get_included_pseudonym_names():
                _LOGGER.debug(
                    "%s: Not registering as dependency on pseudonym %r is not satisfied", unit_name, pseudonym_name
                )
                return False

        for sieve_name in dependencies.get("sieves", []):
            if sieve_name not in builder_context.get_included_sieve_names():
                _LOGGER.debug("%s: Not registering as dependency on sieve %r is not satisfied", unit_name, sieve_name)
                return False

        for step_name in dependencies.get("steps", []):
            if step_name not in builder_context.get_included_step_names():
                _LOGGER.debug("%s: Not registering as dependency on step %r is not satisfied", unit_name, step_name)
                return False

        for stride_name in dependencies.get("strides", []):
            if stride_name not in builder_context.get_included_stride_names():
                _LOGGER.debug("%s: Not registering as dependency on stride %r is not satisfied", unit_name, stride_name)
                return False

        for wrap_name in dependencies.get("wraps", []):
            if wrap_name not in builder_context.get_included_wrap_names():
                _LOGGER.debug("%s: Not registering as dependency on stride %r is not satisfied", unit_name, wrap_name)
                return False

        runtime_environment_dict = should_include_dict.get("runtime_environments", {})

        # Operating system.
        operating_systems = runtime_environment_dict.get("operating_systems")
        os_used = builder_context.project.runtime_environment.operating_system
        os_used_name = os_used.name if os_used is not None else None
        os_used_version = os_used.version if os_used is not None else None

        if operating_systems is None and (os_used_name is not None or os_used_version is not None):
            _LOGGER.debug("%s: Unit is specific to operating system configuration that was not supplied", unit_name)
            return False

        if operating_systems:
            for item in operating_systems:
                os_name = item.get("name")
                os_version = item.get("version")
                if os_name == os_used_name and os_version == os_used_version:
                    _LOGGER.error("%s: Matching operating system %r in version %r", unit_name, os_name, os_version)
                    break
            else:
                _LOGGER.debug(
                    "%s: Not matching operating system (using %r in version %r)",
                    unit_name,
                    os_used_name,
                    os_used_version,
                )
                return False

        # Hardware.
        hw_used = builder_context.project.runtime_environment.hardware

        for hardware_dict in runtime_environment_dict.get("hardware", []):
            # CPU/GPU
            cpu_families = hardware_dict.get("cpu_families")
            cpu_models = hardware_dict.get("cpu_models")
            gpu_models = hardware_dict.get("gpu_models")
            if cpu_families is not None and hw_used.cpu_family not in cpu_families:
                _LOGGER.debug("%s: Not matching CPU family used (using %r)", unit_name, hw_used.cpu_family)
                return False

            if cpu_models is not None and hw_used.cpu_model not in cpu_models:
                _LOGGER.debug("%s: Not matching CPU model used (using %r)", unit_name, hw_used.cpu_model)
                return False

            if gpu_models is not None and hw_used.gpu_model not in gpu_models:
                _LOGGER.debug("%s: Not matching GPU model used (using %r)", unit_name, hw_used.gpu_model)
                return False

        # Software present.
        runtime_used = builder_context.project.runtime_environment

        python_versions = runtime_environment_dict.get("python_versions")
        if python_versions is not None and runtime_used.python_version not in python_versions:
            _LOGGER.debug("%s: Not matching Python version used (using %r)", unit_name, runtime_used.python_version)
            return False

        cuda_versions = runtime_environment_dict.get("cuda_versions")
        if cuda_versions is not None and runtime_used.cuda_version not in cuda_versions:
            _LOGGER.debug("%s: Not matching CUDA version used (using %r)", unit_name, runtime_used.cuda_version)
            return False

        platforms = runtime_environment_dict.get("platforms")
        if platforms is not None and runtime_used.platform not in platforms:
            _LOGGER.debug("%s: Not matching platform used (using %r)", unit_name, runtime_used.platform)
            return False

        openblas_versions = runtime_environment_dict.get("openblas_versions")
        if openblas_versions is not None and runtime_used.openblas_version not in openblas_versions:
            _LOGGER.debug("%s: Not matching openblas version used (using %r)", unit_name, runtime_used.openblas_version)
            return False

        openmpi_versions = runtime_environment_dict.get("openmpi_versions")
        if openmpi_versions is not None and runtime_used.openmpi_version not in openmpi_versions:
            _LOGGER.debug("%s: Not matching openmpi version used (using %r)", unit_name, runtime_used.openmpi_version)
            return False

        cudnn_versions = runtime_environment_dict.get("cudnn_versions")
        if cudnn_versions is not None and runtime_used.cudnn_version not in cudnn_versions:
            _LOGGER.debug("%s: Not matching cudnn version used (using %r)", unit_name, runtime_used.cudnn_version)
            return False

        mkl_versions = runtime_environment_dict.get("mkl_versions")
        if mkl_versions is not None and runtime_used.mkl_version not in mkl_versions:
            _LOGGER.debug("%s: Not matching mkl version used (using %r)", unit_name, runtime_used.mkl_version)
            return False

        base_images = runtime_environment_dict.get("base_images")
        if base_images is not None and runtime_used.base_image not in base_images:
            _LOGGER.debug("%s: Not matching base image used (using %r)", unit_name, runtime_used.base_image)
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
        state_prescription = self.run_prescription.get("match", {}).get("state")
        if state_prescription:
            for resolved_dependency in state_prescription.get("resolved_dependencies", []):
                resolved = state.resolved_dependencies.get(resolved_dependency["name"])
                if not resolved:
                    return False

                index_url = resolved_dependency.get("index_url")
                if index_url is not None and resolved[2] != resolved_dependency["index_url"]:
                    return False

                version = resolved_dependency.get("version")
                if version is not None:
                    specifier = SpecifierSet(version)  # XXX: this could be optimized out
                    if resolved[1] not in specifier:
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
