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
import re
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from voluptuous import Schema
from voluptuous import Required

import attr

from thoth.adviser.cpu_db import CPUDatabase
from thoth.adviser.exceptions import EagerStopPipeline
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.state import State
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion

from .unit_cache import should_include_cache
from ...unit import Unit

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


class _ValueList:
    """A class that overrides `in` to transparently handle included and excluded values."""

    __slots__ = ["_list"]

    def __init__(self, obj: Union[List[object], Dict[str, List[object]]]) -> None:
        """Initialize self."""
        self._list = obj

    def __contains__(self, item: str) -> bool:
        """Override default in behavior based on the YAML definition."""
        if isinstance(self._list, list):
            return self._list.__contains__(item)

        return not self._list["not"].__contains__(item)


class _ValueListBaseImage:
    """A class that overrides `in` to transparently handle included and excluded base images."""

    # Image name mapped to image tag; the "_not" flag specifies if images were declared as part of "not".
    __slots__ = ["_images", "_not"]

    def __init__(self, obj: Union[List[Optional[str]], Dict[str, List[Optional[str]]]]) -> None:
        """Initialize self."""
        self._images: Dict[Optional[str], Set[str]] = {}

        if isinstance(obj, dict):
            image_listing = obj["not"]
            self._not = True
        else:
            image_listing = obj
            self._not = False

        images = []
        for item in image_listing:
            if item is None:
                self._images[None] = {"*"}
                continue

            images.append(item.rsplit(":", maxsplit=1))

        for image in images:
            tag_exp_set = self._images.get(image[0])
            if tag_exp_set is None:
                tag_exp_set = set()
                self._images[image[0]] = tag_exp_set

            if len(image) == 1:
                tag_exp_set.add("*")  # Means any tag.
                continue

            tag = image[1]
            tag_exp_set.add(tag)

    def __contains__(self, item: Optional[str]) -> bool:
        """Check if the given item (base image) is in the provided listing."""
        if item is None:
            # Match `None` image in the image listing.
            if item in self._images:
                return not self._not

            return self._not

        parts = item.rsplit(":", maxsplit=1)
        if len(parts) == 1:  # No tag specified.
            return parts[0] not in self._images if self._not else parts[0] in self._images

        image, tag = parts
        tag_expressions = self._images.get(image)
        if not tag_expressions:
            return self._not

        for tag_exp in tag_expressions:
            if tag_exp.endswith("*"):
                if tag.startswith(tag_exp[:-1]):
                    return not self._not
            elif tag_exp == tag:
                return not self._not

        return self._not


@attr.s(slots=True)
class UnitPrescription(Unit, metaclass=abc.ABCMeta):
    """A base class for implementing pipeline units based on prescription supplied."""

    # Each prescription unit defines these specifically.
    SHOULD_INCLUDE_CACHE: Dict[str, bool] = {}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): str,
            Required("match"): object,
            Required("run"): object,
            Required("prescription"): Schema({"run": bool}),
        }
    )

    _PRESCRIPTION: Optional[Dict[str, Any]] = None

    _stack_info_run = attr.ib(type=bool, kw_only=True, default=False)
    _configuration = attr.ib(type=Dict[str, Any], kw_only=True)
    prescription = attr.ib(type=Dict[str, Any], kw_only=True)

    @prescription.default
    def _prescription_default(self) -> Dict[str, Any]:
        """Initialize prescription property."""
        if self._PRESCRIPTION is None:
            raise ValueError("No assigned prescription on the class level to be set")

        return self._PRESCRIPTION

    @property
    def run_prescription(self) -> Dict[str, Any]:
        """Get run part of the prescription assigned."""
        return self._configuration.get("run", {})

    @property
    def match_prescription(self) -> Dict[str, Any]:
        """Get match part of the prescription assigned."""
        return self._configuration.get("match", {})

    @_configuration.default
    def _initialize_default_configuration(self) -> Dict[str, Any]:
        """Initialize default unit configuration based on declared class' default configuration."""
        if self._PRESCRIPTION is None:
            raise ValueError("No assigned prescription on the class level to be set")

        return {
            "package_name": None,
            "match": self._PRESCRIPTION.get("match", {}),
            "run": self._PRESCRIPTION.get("run", {}),
            "prescription": {"run": False},
        }

    @classmethod
    def get_unit_name(cls) -> str:
        """Get the name of the current prescription unit.

        This method is a class method and *MUST NOT* be used when obtaining unit name on an
        instance. As part of the memory optimization we use class to get the current name of
        a prescription unit with assigned prescription. This means that the prescription unit
        instance would have different names reported with this method based on the current
        class context.
        """
        if cls._PRESCRIPTION is None:
            raise ValueError("No prescription defined")

        name: str = cls._PRESCRIPTION["name"]
        return name

    @classmethod
    def set_prescription(cls, prescription: Dict[str, Any]) -> None:
        """Set prescription to the unit."""
        cls._PRESCRIPTION = prescription

    @classmethod
    def _check_symbols(
        cls, unit_name: str, library_name: str, symbols_expected: List[str], symbols_used: List[str]
    ) -> bool:
        """Check if symbols expected are available given the symbols used."""
        for symbol_expected in symbols_expected:
            for symbol_used in symbols_used:
                if symbol_expected.endswith(".*"):
                    if symbol_used.startswith(symbol_expected[:-2]):  # Discard ending ".*"
                        _LOGGER.debug(
                            "%s: Library symbol %r matching unit requirement on symbol %r for %r",
                            unit_name,
                            symbol_used,
                            symbol_expected,
                            library_name,
                        )
                        break
                elif symbol_used == symbol_expected:
                    _LOGGER.debug(
                        "%s: Library symbol %r matching unit requirement on symbol %r for %r",
                        unit_name,
                        symbol_used,
                        symbol_expected,
                        library_name,
                    )
                    break

                _LOGGER.debug(
                    "%s: Not registering as library symbol requested %r for %r is not used",
                    unit_name,
                    symbol_expected,
                    library_name,
                )
                return False

        _LOGGER.debug("%s: All library symbols required for %r unit are used", unit_name, library_name)
        return True

    @staticmethod
    def _check_version(version_present: Optional[str], version_spec_declared: Optional[str]) -> bool:
        """Check that version present matches version specification."""
        if version_present is None:
            if version_spec_declared is not None:
                return False
            else:
                return True
        else:
            if version_spec_declared is None:
                return True

            return Version(version_present) in SpecifierSet(version_spec_declared)

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

        if not cls._should_include_base_cached(unit_name, builder_context, should_include_dict):
            # Using pre-cached results based on parts that do not change or first time run.
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

        return True

    if TYPE_CHECKING:
        SHOULD_INCLUDE_FUNC_TYPE = Callable[
            [Type["UnitPrescription"], str, "PipelineBuilderContext", Dict[str, Any]], bool
        ]

    @classmethod
    @should_include_cache
    def _should_include_base_cached(
        cls, unit_name: str, builder_context: "PipelineBuilderContext", should_include_dict: Dict[str, Any]
    ) -> bool:
        """Determine if this unit should be included."""
        adviser_pipeline = should_include_dict.get("adviser_pipeline", False)
        if not adviser_pipeline and builder_context.is_adviser_pipeline():
            _LOGGER.debug("%s: Not registering for adviser pipeline", unit_name)
            return False
        elif adviser_pipeline and builder_context.is_adviser_pipeline():
            allowed_recommendation_types = should_include_dict.get("recommendation_types")
            if (
                allowed_recommendation_types is not None
                and builder_context.recommendation_type is not None
                and builder_context.recommendation_type.name.lower() not in _ValueList(allowed_recommendation_types)
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
                and builder_context.decision_type.name.lower() not in _ValueList(allowed_decision_types)
            ):
                _LOGGER.debug(
                    "%s: Not registering for dependency monkey pipeline with decision type %s",
                    unit_name,
                    builder_context.decision_type.name,
                )
                return False

        authenticated = should_include_dict.get("authenticated")
        if authenticated is not None and authenticated is not builder_context.authenticated:
            _LOGGER.debug(
                "%s: Not registering as authentication requirements are not met",
                unit_name,
            )
            return False

        labels_expected = should_include_dict.get("labels", {})
        if labels_expected:
            for label_key, value in labels_expected.items():
                value_context = builder_context.labels.get(label_key)
                if value == value_context:
                    break
            else:
                _LOGGER.debug(
                    "%s: Not registering as labels requested %s do not match with labels supplied %s",
                    unit_name,
                    labels_expected,
                    builder_context.labels,
                )
                return False

        # Library usage.
        library_usage_expected = should_include_dict.get("library_usage", {})
        if library_usage_expected:
            if not builder_context.library_usage:
                _LOGGER.debug("%s: Not registering as no library usage supplied", unit_name)
                return False

            for library_name, symbols_expected in library_usage_expected.items():
                symbols_used = builder_context.library_usage.get(library_name)

                if not symbols_used:
                    _LOGGER.debug("%s: Not registering as library %s is not used", unit_name, library_name)
                    return False

                if not cls._check_symbols(unit_name, library_name, symbols_expected, symbols_used):
                    return False
            else:
                _LOGGER.debug("%s: All library symbols required present in the library usage supplied", unit_name)

        runtime_environment_dict = should_include_dict.get("runtime_environments", {})

        # Operating system.
        operating_systems = runtime_environment_dict.get("operating_systems")
        os_used = builder_context.project.runtime_environment.operating_system
        os_used_name = os_used.name if os_used is not None else None
        os_used_version = os_used.version if os_used is not None else None

        if operating_systems:
            for item in operating_systems:
                os_name = item.get("name")
                os_version = item.get("version")
                if os_name == os_used_name and os_version == os_used_version:
                    _LOGGER.debug("%s: Matching operating system %r in version %r", unit_name, os_name, os_version)
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
            cpu_flags = hardware_dict.get("cpu_flags") or []
            gpu_models = hardware_dict.get("gpu_models")
            if cpu_families is not None and hw_used.cpu_family not in _ValueList(cpu_families):
                _LOGGER.debug("%s: Not matching CPU family used (using %r)", unit_name, hw_used.cpu_family)
                return False

            if cpu_models is not None and hw_used.cpu_model not in _ValueList(cpu_models):
                _LOGGER.debug("%s: Not matching CPU model used (using %r)", unit_name, hw_used.cpu_model)
                return False

            if gpu_models is not None and hw_used.gpu_model not in _ValueList(gpu_models):
                _LOGGER.debug("%s: Not matching GPU model used (using %r)", unit_name, hw_used.gpu_model)
                return False

            if cpu_flags:
                if hw_used.cpu_family is None or hw_used.cpu_model is None:
                    _LOGGER.debug(
                        "%s: CPU family (%s) or CPU model (%s) not provided, cannot check CPU flags %r",
                        unit_name,
                        hw_used.cpu_family,
                        hw_used.cpu_model,
                        cpu_flags,
                    )
                    return False

                if isinstance(cpu_flags, dict):
                    for cpu_flag in cpu_flags["not"]:
                        if CPUDatabase.provides_flag(hw_used.cpu_family, hw_used.cpu_model, cpu_flag):
                            _LOGGER.debug(
                                "%s: CPU flag %r is provided by CPU family %s and CPU model %s, not registering unit",
                                unit_name,
                                cpu_flag,
                                hw_used.cpu_family,
                                hw_used.cpu_model,
                            )
                            return False
                else:
                    for cpu_flag in cpu_flags:
                        if not CPUDatabase.provides_flag(hw_used.cpu_family, hw_used.cpu_model, cpu_flag):
                            _LOGGER.debug(
                                "%s: Not matching CPU flag %r for CPU family %s and CPU model %s, not registering unit",
                                unit_name,
                                cpu_flag,
                                hw_used.cpu_family,
                                hw_used.cpu_model,
                            )
                            return False

                _LOGGER.debug(
                    "%s: Used CPU family %s and CPU model %s provides all CPU flags required %r",
                    unit_name,
                    hw_used.cpu_family,
                    hw_used.cpu_model,
                    cpu_flags,
                )

        # Software present.
        runtime_used = builder_context.project.runtime_environment

        python_version_spec = runtime_environment_dict.get("python_version")
        if not cls._check_version(runtime_used.python_version, python_version_spec):
            _LOGGER.debug(
                "%s: Not matching Python version used (using %r; expected %r)",
                unit_name,
                runtime_used.python_version,
                python_version_spec,
            )
            return False

        cuda_version_spec = runtime_environment_dict.get("cuda_version")
        if not cls._check_version(runtime_used.cuda_version, cuda_version_spec):
            _LOGGER.debug(
                "%s: Not matching CUDA version used (using %r; expected %r)",
                unit_name,
                runtime_used.cuda_version,
                cuda_version_spec,
            )
            return False

        platforms = runtime_environment_dict.get("platforms")
        if platforms is not None and runtime_used.platform not in _ValueList(platforms):
            _LOGGER.debug("%s: Not matching platform used (using %r)", unit_name, runtime_used.platform)
            return False

        openblas_version_spec = runtime_environment_dict.get("openblas_version")
        if not cls._check_version(runtime_used.openblas_version, openblas_version_spec):
            _LOGGER.debug(
                "%s: Not matching openblas version used (using %r; expected %r)",
                unit_name,
                runtime_used.openblas_version,
                openblas_version_spec,
            )
            return False

        openmpi_version_spec = runtime_environment_dict.get("openmpi_version")
        if not cls._check_version(runtime_used.openmpi_version, openmpi_version_spec):
            _LOGGER.debug(
                "%s: Not matching openmpi version used (using %r; expected %r)",
                unit_name,
                runtime_used.openmpi_version,
                openmpi_version_spec,
            )
            return False

        cudnn_version_spec = runtime_environment_dict.get("cudnn_version")
        if not cls._check_version(runtime_used.cudnn_version, cudnn_version_spec):
            _LOGGER.debug(
                "%s: Not matching cudnn version used (using %r; expected %r)",
                unit_name,
                runtime_used.cudnn_version,
                cudnn_version_spec,
            )
            return False

        mkl_version_spec = runtime_environment_dict.get("mkl_version")
        if not cls._check_version(runtime_used.mkl_version, mkl_version_spec):
            _LOGGER.debug(
                "%s: Not matching mkl version used (using %r; expected %r)",
                unit_name,
                runtime_used.mkl_version,
                mkl_version_spec,
            )
            return False

        base_images = runtime_environment_dict.get("base_images")
        if base_images is not None and runtime_used.base_image not in _ValueListBaseImage(base_images):
            _LOGGER.debug("%s: Not matching base image used (using %r)", unit_name, runtime_used.base_image)
            return False

        # All the following require base image information.
        base_image = None
        if runtime_used.base_image:
            base_image = cls.get_base_image(runtime_used.base_image, raise_on_error=True)

        abi = runtime_environment_dict.get("abi")
        if abi:
            if not base_image:
                _LOGGER.debug(
                    "%s: Check on ABI present but no base image provided",
                    unit_name,
                )
                return False

            symbols_present = set(
                builder_context.graph.get_thoth_s2i_analyzed_image_symbols_all(
                    base_image[0],
                    base_image[1],
                    is_external=False,
                )
            )
            if not symbols_present:
                if builder_context.iteration == 0:
                    _LOGGER.warning(
                        f"%s: No symbols found for runtime environment %r", unit_name, runtime_used.base_image
                    )
                return False

            if isinstance(abi, dict) and "not" in abi:
                # Negate operation.
                if symbols_present.intersection(set(abi["not"])):
                    _LOGGER.debug("%s: Not matching ABI present in the base image", unit_name)
                    return False
                else:
                    return True
            elif isinstance(abi, list):
                if set(abi).issubset(symbols_present):
                    return True
                else:
                    _LOGGER.debug("%s: Not matching ABI present in the base image", unit_name)
                    return False
            else:
                _LOGGER.error("%s: Unknown ABI definition - please report this error to administrator", unit_name)
                return False

        rpm_packages = runtime_environment_dict.get("rpm_packages")
        if rpm_packages:
            if not base_image:
                _LOGGER.debug(
                    "%s: Check on RPM packages present but no base image provided",
                    unit_name,
                )
                return False

            analysis_document_id = builder_context.graph.get_last_analysis_document_id(
                base_image[0],
                base_image[1],
                is_external=False,
            )

            if not analysis_document_id:
                if builder_context.iteration == 0:
                    _LOGGER.warning(
                        "%s: No analysis for base container image %r found",
                        unit_name,
                        runtime_used.base_image,
                    )
                return False

            rpm_packages_present = builder_context.graph.get_rpm_package_version_all(analysis_document_id)
            if not rpm_packages_present:
                _LOGGER.debug("%s: No RPM packages found for %r", unit_name, runtime_used.base_image)
                return False
            if not cls._check_rpm_packages(unit_name, rpm_packages_present, rpm_packages):
                _LOGGER.debug(
                    "%s: Not matching RPM packages present in the base image %r", unit_name, runtime_used.base_image
                )
                return False

        python_packages = runtime_environment_dict.get("python_packages")
        if python_packages:
            if not base_image:
                _LOGGER.debug(
                    "%s: Check on Python packages present but no base image provided",
                    unit_name,
                )
                return False

            analysis_document_id = builder_context.graph.get_last_analysis_document_id(
                base_image[0],
                base_image[1],
                is_external=False,
            )

            if not analysis_document_id:
                if builder_context.iteration == 0:
                    _LOGGER.warning(
                        "%s: No analysis for base container image %r found",
                        unit_name,
                        runtime_used.base_image,
                    )
                return False

            python_packages_present = builder_context.graph.get_python_package_version_all(analysis_document_id)
            if not python_packages_present:
                _LOGGER.debug("%s: No Python packages found for %r", unit_name, runtime_used.base_image)
                return False
            if not cls._check_python_packages(unit_name, python_packages_present, python_packages):
                _LOGGER.debug(
                    "%s: Not matching Python packages present in the base image %r", unit_name, runtime_used.base_image
                )
                return False

        return True

    @classmethod
    def _index_url_check(cls, index_url_conf: Optional[Union[str, Dict[str, str]]], index_url: str) -> bool:
        """Convert index_url to a comparable object considering "not"."""
        if index_url_conf is None:
            return True

        if isinstance(index_url_conf, dict):
            if list(index_url_conf.keys()) != ["not"]:
                raise ValueError("index_url configuration should state directly string or a 'not' value")

            return index_url_conf["not"] != index_url
        else:
            return index_url_conf == index_url

    @classmethod
    def _check_python_packages(
        cls,
        unit_name: str,
        python_packages_present: List[Dict[str, str]],
        python_packages_required: List[Dict[str, str]],
    ) -> bool:
        """Check if required Python packages are present in the environment."""
        # Convert to dict to have O(1) access time.
        py_packages_present_dict: Dict[str, List[Dict[str, str]]] = {}
        for python_package_present in python_packages_present:
            package = py_packages_present_dict.get(python_package_present["package_name"])
            if package is None:
                py_packages_present_dict[python_package_present["package_name"]] = [python_package_present]
            else:
                package.append(python_package_present)

        if isinstance(python_packages_required, dict):
            if "not" not in python_packages_required:
                _LOGGER.error("%s: Unable to parse description of Python packages required", unit_name)
                return False

            for not_required_python_package in python_packages_required["not"]:
                for py_package_present in py_packages_present_dict.get(not_required_python_package["name"]) or []:
                    location = not_required_python_package.get("location")
                    if location is not None and not re.fullmatch(location, py_package_present["location"]):
                        _LOGGER.debug(
                            "%s: Python package %r in %r is located in different location %r as expected",
                            unit_name,
                            not_required_python_package["name"],
                            py_package_present["location"],
                            location,
                        )
                        continue

                    version = not_required_python_package.get("version")
                    if version and py_package_present["package_version"] not in SpecifierSet(version):
                        _LOGGER.debug(
                            "%s: Python package '%s==%s' (in %r) matches version %r but should not",
                            unit_name,
                            not_required_python_package["name"],
                            py_package_present["package_version"],
                            py_package_present["location"],
                            version,
                        )
                        continue

                    _LOGGER.debug(
                        "%s: presence of Python package %r causes not including the pipeline unit",
                        unit_name,
                        py_package_present,
                    )
                    return False
        else:
            for required_python_package in python_packages_required:
                for py_package_present in py_packages_present_dict.get(required_python_package["name"]) or []:
                    version = required_python_package.get("version")
                    if version and py_package_present["package_version"] not in SpecifierSet(version):
                        _LOGGER.debug(
                            "%s: Python package '%s==%s' (in %r) does not match required version %r",
                            unit_name,
                            required_python_package["name"],
                            py_package_present["package_version"],
                            py_package_present.get("location", "any"),
                            version,
                        )
                        continue

                    location = required_python_package.get("location")
                    if location is not None and not re.fullmatch(location, py_package_present["location"]):
                        _LOGGER.debug(
                            "%s: Python package %r is located at %r but expected to be in %r",
                            unit_name,
                            required_python_package["name"],
                            py_package_present["location"],
                            location,
                        )
                        continue

                    _LOGGER.debug(
                        "%s: Python package %r in version %r (located in %r) is found in the runtime environment",
                        unit_name,
                        required_python_package["name"],
                        required_python_package.get("version", "any"),
                        py_package_present.get("location", "any"),
                    )
                    break
                else:
                    _LOGGER.debug(
                        "%s: Not including as Python package %r (in version %r) is not present in the environment",
                        unit_name,
                        required_python_package["name"],
                        required_python_package.get("version", "any"),
                    )
                    return False

        _LOGGER.debug("%s: all Python package presence checks passed", unit_name)
        return True

    @staticmethod
    def _check_rpm_packages(
        unit_name: str,
        rpm_packages_present: List[Dict[str, str]],
        rpm_packages_required: Union[List[Dict[str, str]], Dict[str, List[Dict[str, str]]]],
    ) -> bool:
        """Check if required RPM packages are present."""
        # Convert RPM packages present to mapping to save some cycles and have O(1) look up.
        rpm_packages_pres = {i["package_name"]: i for i in rpm_packages_present}
        rpm_packages_req: List[Dict[str, str]]
        if isinstance(rpm_packages_required, dict):
            if "not" not in rpm_packages_required:
                _LOGGER.error("%s: Unable to parse description of RPM packages required", unit_name)
                return False

            should_be_present = False
            rpm_packages_req = [i for i in rpm_packages_required["not"]]
        else:
            should_be_present = True
            rpm_packages_req = [i for i in rpm_packages_required]

        for rpm_package_req in rpm_packages_req:
            rpm_name = rpm_package_req["package_name"]
            rpm_present = rpm_packages_pres.get(rpm_name)

            if should_be_present:
                if not rpm_present:
                    _LOGGER.debug(
                        "%s: Not including unit as RPM %r is not present in the runtime environment",
                        unit_name,
                        rpm_name,
                    )
                    return False

                for key, value in rpm_package_req.items():
                    value_present = rpm_present.get(key)
                    if value_present != value:
                        _LOGGER.debug(
                            "%s: Not including unit as RPM %r has not matching %r - expected %r got %r",
                            unit_name,
                            rpm_name,
                            key,
                            value,
                            value_present,
                        )
                        return False
            else:
                if not rpm_present:
                    # If just one is not present, we know the unit is included.
                    return True

                for key, value in rpm_package_req.items():
                    value_present = rpm_present.get(key)
                    if value_present != value:
                        _LOGGER.debug(
                            "%s: Not including unit as RPM %s has matching %r - expected %r got %r",
                            unit_name,
                            rpm_name,
                            key,
                            value,
                            value_present,
                        )
                        return True

        if not should_be_present:
            _LOGGER.debug("%s: Not including unit as all RPM are present in the runtime environment", unit_name)
            return False

        # Path to should be present.
        _LOGGER.debug("%s: all RPM package presence checks passed", unit_name)
        return True

    @classmethod
    def _prepare_justification_link(cls, entries: List[Dict[str, Any]]) -> None:
        """Prepare justification links before using them."""
        for entry in entries:
            link = entry.get("link")
            if link and not link.startswith(("https://", "http://")):
                entry["link"] = jl(link)

    @property
    def name(self) -> str:
        """Get name of the prescription instance."""
        name: str = self.prescription["name"]
        return name

    def pre_run(self) -> None:
        """Prepare this pipeline unit before running it."""
        self._prepare_justification_link(self.run_prescription.get("stack_info", []))
        self._configuration["prescription"]["run"] = False
        super().pre_run()

    @staticmethod
    def _yield_should_include(unit_prescription: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Yield for every entry stated in the match field."""
        match = unit_prescription.get("match", {})
        run = unit_prescription.get("run", {})
        prescription_conf = {"run": False}
        if isinstance(match, list):
            for item in match:
                yield {
                    "package_name": item["package_version"].get("name") if item else None,
                    "match": item,
                    "run": run,
                    "prescription": prescription_conf,
                }
        else:
            yield {
                "package_name": match["package_version"].get("name") if match else None,
                "match": match,
                "run": run,
                "prescription": prescription_conf,
            }

    @staticmethod
    def _yield_should_include_with_state(unit_prescription: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Yield for every entry stated in the match field."""
        match = unit_prescription.get("match", {})
        prescription_conf = {"run": False}
        if isinstance(match, list):
            for item in match:
                match_resolved = item.get("state", {}).get("resolved_dependencies")
                yield {
                    # Return the first package name that should be matched to keep optimization for wrap calls.
                    "package_name": match_resolved[0].get("name") if match_resolved else None,
                    "match": item,
                    "run": unit_prescription["run"],
                    "prescription": prescription_conf,
                }
        else:
            match_resolved = match.get("state", {}).get("resolved_dependencies") if match else None
            yield {
                "package_name": match_resolved[0].get("name") if match_resolved else None,
                "match": match,
                "run": unit_prescription["run"],
                "prescription": prescription_conf,
            }

    def _run_log(self) -> None:
        """Log message specified in the run prescription."""
        if self._configuration["prescription"]["run"]:
            # Noop. The prescription was already run.
            return

        log = self.run_prescription.get("log")
        if log:
            _LOGGER.log(level=getattr(logging, log["type"]), msg=f"{self.name}: {log['message']}")

    def _run_stack_info(self) -> None:
        """Add stack info if any prescribed."""
        if self._configuration["prescription"]["run"]:
            # Noop. The prescription was already run.
            return

        stack_info = self.run_prescription.get("stack_info")
        if stack_info:
            self.context.stack_info.extend(stack_info)

    def _check_package_tuple_from_prescription(
        self, dependency_tuple: Tuple[str, str, str], dependency: Dict[str, str]
    ) -> bool:
        """Check if the given package version tuple matches with what was written in prescription."""
        develop = dependency.get("develop")
        if develop is not None:
            package_version = self.context.get_package_version(dependency_tuple, graceful=True)
            if not package_version:
                return False

            if package_version.develop != develop:
                return False

        if not self._index_url_check(dependency.get("index_url"), dependency_tuple[2]):
            return False

        version = dependency.get("version")
        if version is not None:
            specifier = SpecifierSet(version)
            if dependency_tuple[1] not in specifier:
                return False

        return True

    def _run_state(self, state: State) -> bool:
        """Check state match."""
        state_prescription = self.match_prescription.get("state")
        if not state_prescription:
            # Nothing to check.
            return True

        for resolved_dependency in state_prescription.get("resolved_dependencies", []):
            resolved = state.resolved_dependencies.get(resolved_dependency["name"])
            if not resolved:
                return False

            if not self._check_package_tuple_from_prescription(resolved, resolved_dependency):
                return False

        return True

    def _run_state_with_initiator(self, state: State, package_version: PackageVersion) -> bool:
        """Check state match respecting also initiator of the give package."""
        state_prescription = self.match_prescription.get("state")
        if not state_prescription:
            # Nothing to check.
            return True

        package_version_from = state_prescription.get("package_version_from") or []
        # XXX: we explicitly do not consider runtime environment as we expect to have it only one here.
        dependents = {
            i[0] for i in self.context.dependents.get(package_version.name, {}).get(package_version.to_tuple(), set())
        }

        for resolved_dependency in package_version_from:
            resolved = state.resolved_dependencies.get(resolved_dependency["name"])
            if not resolved:
                return False

            if not self._check_package_tuple_from_prescription(resolved, resolved_dependency):
                return False

            if resolved not in dependents:
                _LOGGER.debug(
                    "Package %r stated in package_version_from not a did not introduce package %r",
                    resolved,
                    package_version.to_tuple(),
                )
                return False

            dependents.discard(resolved)

        if dependents and not state_prescription.get("package_version_from_allow_other", False):
            for dependent in dependents:
                if dependent == state.resolved_dependencies.get(dependent[0]):
                    return False

        for resolved_dependency in state_prescription.get("resolved_dependencies", []):
            resolved = state.resolved_dependencies.get(resolved_dependency["name"])
            if not resolved:
                return False

            if not self._check_package_tuple_from_prescription(resolved, resolved_dependency):
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
