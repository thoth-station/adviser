#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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

"""Implementation of pipeline builder - create pipeline configuration based on the project and its library usage."""

import os
import logging
import json
from typing import Any
from typing import Dict
from typing import Generator
from typing import Type
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from itertools import chain

import attr
from thoth.python import Project
from thoth.storages import GraphDatabase
import yaml

from .enums import DecisionType
from .enums import RecommendationType
from .exceptions import InternalError
from .exceptions import UnknownPipelineUnitError
from .exceptions import PipelineConfigurationError
from .pipeline_config import PipelineConfig
from .prescription import UnitPrescription

if TYPE_CHECKING:
    from .prescription import Prescription  # noqa: F401
    from .unit_types import BootType
    from .unit_types import PseudonymType
    from .unit_types import SieveType
    from .unit_types import StepType
    from .unit_types import StrideType
    from .unit_types import UnitType
    from .unit_types import WrapType

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PipelineBuilderContext:
    """A context passed to units to determine if they want to participate in a pipeline."""

    graph = attr.ib(type=GraphDatabase, kw_only=True, default=None)
    project = attr.ib(type=Project, kw_only=True, default=None)
    library_usage = attr.ib(type=Optional[Dict[str, Any]], kw_only=True, default=None)
    labels = attr.ib(type=Dict[str, str], kw_only=True, default=attr.Factory(dict))
    decision_type = attr.ib(type=Optional[DecisionType], kw_only=True, default=None)
    recommendation_type = attr.ib(type=Optional[RecommendationType], kw_only=True, default=None)
    cli_parameters = attr.ib(type=Dict[str, Any], kw_only=True, default=attr.Factory(dict))
    prescription = attr.ib(type=Optional["Prescription"], kw_only=True, default=None)
    iteration = attr.ib(type=int, kw_only=True, default=0)
    authenticated = attr.ib(type=bool, kw_only=True)

    _boots = attr.ib(type=Dict[Optional[str], List["BootType"]], factory=dict, kw_only=True)
    _pseudonyms = attr.ib(type=Dict[str, List["PseudonymType"]], factory=dict, kw_only=True)
    _sieves = attr.ib(type=Dict[Optional[str], List["SieveType"]], factory=dict, kw_only=True)
    _steps = attr.ib(type=Dict[Optional[str], List["StepType"]], factory=dict, kw_only=True)
    _strides = attr.ib(type=Dict[Optional[str], List["StrideType"]], factory=dict, kw_only=True)
    _wraps = attr.ib(type=Dict[Optional[str], List["WrapType"]], factory=dict, kw_only=True)
    _boots_included = attr.ib(type=Dict[str, List["BootType"]], factory=dict, kw_only=True)
    _pseudonyms_included = attr.ib(type=Dict[str, List["PseudonymType"]], factory=dict, kw_only=True)
    _sieves_included = attr.ib(type=Dict[str, List["SieveType"]], factory=dict, kw_only=True)
    _steps_included = attr.ib(type=Dict[str, List["StepType"]], factory=dict, kw_only=True)
    _strides_included = attr.ib(type=Dict[str, List["StrideType"]], factory=dict, kw_only=True)
    _wraps_included = attr.ib(type=Dict[str, List["WrapType"]], factory=dict, kw_only=True)

    @authenticated.default
    def _authenticated_default(self) -> bool:
        """Check if adviser is running in an authenticated mode."""
        env_authenticated = os.getenv("THOTH_AUTHENTICATED_ADVISE")
        return bool(int(env_authenticated)) if env_authenticated is not None else False

    @property
    def boots(self) -> List["BootType"]:
        """Get all boots registered to this pipeline builder context."""
        return list(chain(*self._boots.values()))

    @property
    def boots_dict(self) -> Dict[Optional[str], List["BootType"]]:
        """Get boots as a dictionary mapping."""
        return self._boots

    @property
    def pseudonyms(self) -> List["PseudonymType"]:
        """Get all pseudonyms registered to this pipeline builder context."""
        return list(chain(*self._pseudonyms.values()))

    @property
    def pseudonyms_dict(self) -> Dict[str, List["PseudonymType"]]:
        """Get pseudonyms as a dictionary mapping."""
        return self._pseudonyms

    @property
    def sieves(self) -> List["SieveType"]:
        """Get all sieves registered to this pipeline builder context."""
        return list(chain(*self._sieves.values()))

    @property
    def sieves_dict(self) -> Dict[Optional[str], List["SieveType"]]:
        """Get sieves as a dictionary mapping."""
        return self._sieves

    @property
    def steps(self) -> List["StepType"]:
        """Get all steps registered to this pipeline builder context."""
        return list(chain(*self._steps.values()))

    @property
    def steps_dict(self) -> Dict[Optional[str], List["StepType"]]:
        """Get steps as a dictionary mapping."""
        return self._steps

    @property
    def strides(self) -> List["StrideType"]:
        """Get all strides registered to this pipeline builder context."""
        return list(chain(*self._strides.values()))

    @property
    def strides_dict(self) -> Dict[Optional[str], List["StrideType"]]:
        """Get strides as a dictionary mapping."""
        return self._strides

    @property
    def wraps(self) -> List["WrapType"]:
        """Get all wraps registered to this pipeline builder context."""
        return list(chain(*self._wraps.values()))

    @property
    def wraps_dict(self) -> Dict[Optional[str], List["WrapType"]]:
        """Get wraps as a dictionary mapping."""
        return self._wraps

    def __attrs_post_init__(self) -> None:
        """Verify we have only adviser or dependency monkey specific builder."""
        if self.decision_type is not None and self.recommendation_type is not None:
            raise ValueError("Cannot instantiate builder for adviser and dependency monkey at the same time")

        if self.decision_type is None and self.recommendation_type is None:
            raise ValueError("Cannot instantiate builder context not specific to adviser nor dependency monkey")

    def is_included(self, unit_class: Type["UnitType"]) -> bool:
        """Check if the given pipeline unit is already included in the pipeline configuration."""
        if unit_class.is_boot_unit_type():
            return unit_class.get_unit_name() in self._boots_included
        elif unit_class.is_pseudonym_unit_type():
            return unit_class.get_unit_name() in self._pseudonyms_included
        elif unit_class.is_sieve_unit_type():
            return unit_class.get_unit_name() in self._sieves_included
        elif unit_class.is_step_unit_type():
            return unit_class.get_unit_name() in self._steps_included
        elif unit_class.is_stride_unit_type():
            return unit_class.get_unit_name() in self._strides_included
        elif unit_class.is_wrap_unit_type():
            return unit_class.get_unit_name() in self._wraps_included

        raise InternalError(f"Unknown unit {unit_class.get_unit_name()!r} of type {unit_class}")

    def get_included_boots(self, boot_class: Type["UnitType"]) -> Generator["BootType", None, None]:
        """Get included boots of the provided boot class."""
        assert boot_class.is_boot_unit_type()
        yield from self._boots_included.get(boot_class.get_unit_name(), [])

    def get_included_boot_names(self) -> Generator[str, None, None]:
        """Get names of included boots."""
        yield from self._boots_included.keys()

    def get_included_pseudonyms(self, pseudonym_class: Type["PseudonymType"]) -> Generator["PseudonymType", None, None]:
        """Get included sieves of the provided sieve class."""
        assert pseudonym_class.is_pseudonym_unit_type()
        yield from self._pseudonyms_included.get(pseudonym_class.get_unit_name(), [])

    def get_included_pseudonym_names(self) -> Generator[str, None, None]:
        """Get names of included pseudonyms."""
        yield from self._pseudonyms_included.keys()

    def get_included_sieves(self, sieve_class: Type["SieveType"]) -> Generator["SieveType", None, None]:
        """Get included sieves of the provided sieve class."""
        assert sieve_class.is_sieve_unit_type()
        yield from self._sieves_included.get(sieve_class.get_unit_name(), [])

    def get_included_sieve_names(self) -> Generator[str, None, None]:
        """Get names of included sieves."""
        yield from self._sieves_included.keys()

    def get_included_steps(self, step_class: Type["StepType"]) -> Generator["StepType", None, None]:
        """Get included steps of the provided step class."""
        assert step_class.is_step_unit_type()
        yield from self._steps_included.get(step_class.get_unit_name(), [])

    def get_included_step_names(self) -> Generator[str, None, None]:
        """Get names of included steps."""
        yield from self._steps_included.keys()

    def get_included_strides(self, stride_class: Type["StrideType"]) -> Generator["StrideType", None, None]:
        """Get included strides of the provided stride class."""
        assert stride_class.is_stride_unit_type()
        yield from self._strides_included.get(stride_class.get_unit_name(), [])

    def get_included_stride_names(self) -> Generator[str, None, None]:
        """Get names of included strides."""
        yield from self._strides_included.keys()

    def get_included_wraps(self, wrap_class: Type["WrapType"]) -> Generator["WrapType", None, None]:
        """Get included wraps of the provided wrap class."""
        assert wrap_class.is_wrap_unit_type()
        yield from self._wraps_included.get(wrap_class.get_unit_name(), [])

    def get_included_wrap_names(self) -> Generator[str, None, None]:
        """Get names of included wraps."""
        yield from self._wraps_included.keys()

    def is_adviser_pipeline(self) -> bool:
        """Check if the pipeline built is meant for adviser."""
        return self.decision_type is None and self.recommendation_type is not None

    def is_dependency_monkey_pipeline(self) -> bool:
        """Check if the pipeline built is meant for Dependency Monkey."""
        return self.decision_type is not None and self.recommendation_type is None

    def add_unit(self, unit: "UnitType") -> None:
        """Add the given unit to pipeline configuration."""
        package_name: Optional[str] = unit.configuration.get("package_name")

        if unit.is_boot_unit_type():
            self._boots_included.setdefault(unit.name, []).append(unit)
            self._boots.setdefault(package_name, []).append(unit)
            return
        elif unit.is_pseudonym_unit_type():
            if not package_name:
                raise PipelineConfigurationError(
                    f"Pipeline cannot be constructed as unit {unit.name!r} of type Pseudonym "
                    f"did not provide any package name configuration: {unit.configuration!r}"
                )
            self._pseudonyms_included.setdefault(unit.name, []).append(unit)
            self._pseudonyms.setdefault(package_name, []).append(unit)
            return
        elif unit.is_sieve_unit_type():
            self._sieves_included.setdefault(unit.name, []).append(unit)
            self._sieves.setdefault(package_name, []).append(unit)
            return
        elif unit.is_step_unit_type():
            self._steps_included.setdefault(unit.name, []).append(unit)
            self._steps.setdefault(package_name, []).append(unit)
            return
        elif unit.is_stride_unit_type():
            self._strides_included.setdefault(unit.name, []).append(unit)
            self._strides.setdefault(package_name, []).append(unit)
            return
        elif unit.is_wrap_unit_type():
            self._wraps_included.setdefault(unit.name, []).append(unit)
            self._wraps.setdefault(package_name, []).append(unit)
            return

        raise InternalError(f"Unknown unit {unit!r} of type {unit.name!r}")


class PipelineBuilder:
    """Builder responsible for creating pipeline configuration from the project and its library usage."""

    __slots__: List[str] = []

    def __init__(self) -> None:
        """Instantiate of the pipeline builder - do NOT instantiate this class."""
        raise NotImplementedError("Cannot instantiate pipeline builder")

    @staticmethod
    def _iter_units(ctx: PipelineBuilderContext) -> Generator["UnitType", None, None]:
        """Iterate over pipeline units available in this implementation."""
        # Imports placed here to simplify tests.
        import thoth.adviser.boots
        import thoth.adviser.pseudonyms
        import thoth.adviser.sieves
        import thoth.adviser.steps
        import thoth.adviser.strides
        import thoth.adviser.wraps

        for boot_name in thoth.adviser.boots.__all__:
            yield getattr(thoth.adviser.boots, boot_name)
        if ctx.prescription:
            yield from ctx.prescription.iter_boot_units()

        for pseudonym_name in thoth.adviser.pseudonyms.__all__:
            yield getattr(thoth.adviser.pseudonyms, pseudonym_name)
        if ctx.prescription:
            yield from ctx.prescription.iter_pseudonym_units()

        for sieve_name in thoth.adviser.sieves.__all__:
            yield getattr(thoth.adviser.sieves, sieve_name)
        if ctx.prescription:
            yield from ctx.prescription.iter_sieve_units()

        for step_name in thoth.adviser.steps.__all__:
            yield getattr(thoth.adviser.steps, step_name)
        if ctx.prescription:
            yield from ctx.prescription.iter_step_units()

        for stride_name in thoth.adviser.strides.__all__:
            yield getattr(thoth.adviser.strides, stride_name)
        if ctx.prescription:
            yield from ctx.prescription.iter_stride_units()

        for wrap_name in thoth.adviser.wraps.__all__:
            yield getattr(thoth.adviser.wraps, wrap_name)
        if ctx.prescription:
            yield from ctx.prescription.iter_wrap_units()

    @classmethod
    def _build_configuration(cls, ctx: PipelineBuilderContext) -> PipelineConfig:
        """Instantiate units and return the actual pipeline configuration."""
        # As pipeline steps can have dependencies on each other, iterate over them until we have any change done
        # to the pipeline configuration.
        _LOGGER.info("Creating pipeline configuration")

        blocked_units = (
            set(os.environ["THOTH_ADVISER_BLOCKED_UNITS"].split(","))
            if "THOTH_ADVISER_BLOCKED_UNITS" in os.environ
            else set()
        )

        change = True
        ctx.iteration = -1
        try:
            while change:
                change = False
                ctx.iteration += 1
                for unit_class in cls._iter_units(ctx):
                    unit_name = unit_class.get_unit_name()
                    if unit_name in blocked_units:
                        _LOGGER.debug(
                            "Avoiding adding pipeline unit %r based on blocked units configuration",
                            unit_name,
                        )
                        continue

                    for unit_configuration in unit_class.should_include(ctx):
                        if unit_configuration is None:
                            _LOGGER.debug(
                                "Pipeline unit %r will not be included in the pipeline configuration in this round",
                                unit_name,
                            )
                            continue

                        change = True

                        _LOGGER.debug(
                            "Including pipeline unit %r in pipeline configuration with unit configuration %r",
                            unit_name,
                            unit_configuration,
                        )
                        unit_instance = unit_class()  # type: ignore

                        # Always perform update, even with an empty dict. Update triggers a schema check.
                        try:
                            unit_instance.update_configuration(unit_configuration)
                        except Exception as exc:
                            raise PipelineConfigurationError(
                                f"Filed to initialize pipeline unit configuration for {unit_name!r} "
                                f"with configuration {unit_configuration!r}: {str(exc)}"
                            ) from exc

                        ctx.add_unit(unit_instance)
        finally:
            # Once the build pipeline is constructed or fails to construct, we can clear cached results.
            UnitPrescription.SHOULD_INCLUDE_CACHE.clear()

        pipeline = PipelineConfig(
            boots=ctx.boots_dict,
            pseudonyms=ctx.pseudonyms_dict,
            sieves=ctx.sieves_dict,
            steps=ctx.steps_dict,
            strides=ctx.strides_dict,
            wraps=ctx.wraps_dict,
        )

        if _LOGGER.getEffectiveLevel() <= logging.DEBUG:
            _LOGGER.debug(
                "Pipeline configuration creation ended, configuration:\n%s",
                json.dumps(pipeline.to_dict(), indent=2),
            )

        return pipeline

    @staticmethod
    def _do_instantiate_from_dict(module: object, configuration_entry: Dict[str, Any]) -> "UnitType":
        """Instantiate a pipeline unit from a dict representation."""
        if "name" not in configuration_entry:
            raise ValueError(f"No pipeline unit name provided in the configuration entry: {configuration_entry!r}")

        try:
            unit_class = getattr(module, configuration_entry["name"])
        except AttributeError as exc:
            raise UnknownPipelineUnitError(f"Cannot import unit {configuration_entry['name']}: {str(exc)}") from exc

        unit: "UnitType" = unit_class()

        if configuration_entry.get("configuration"):
            try:
                unit.update_configuration(configuration_entry["configuration"])
            except Exception as exc:
                raise PipelineConfigurationError(
                    f"Filed to initialize pipeline unit configuration for {unit.name!r} "
                    f"with configuration {configuration_entry['configuration']!r}: {str(exc)}"
                ) from exc

        return unit

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]) -> "PipelineConfig":
        """Instantiate pipeline configuration based on dictionary supplied."""
        # Imports placed here to simplify tests.
        import thoth.adviser.boots
        import thoth.adviser.pseudonyms
        import thoth.adviser.sieves
        import thoth.adviser.steps
        import thoth.adviser.strides
        import thoth.adviser.wraps

        boots: Dict[Optional[str], List["BootType"]] = {}
        for boot_entry in dict_.pop("boots", []) or []:
            boot_unit: "BootType" = cls._do_instantiate_from_dict(thoth.adviser.boots, boot_entry)
            package_name = boot_unit.configuration.get("package_name")
            boots.setdefault(package_name, []).append(boot_unit)

        pseudonyms: Dict[str, List["PseudonymType"]] = {}
        for pseudonym_entry in dict_.pop("pseudonyms", []) or []:
            unit: "PseudonymType" = cls._do_instantiate_from_dict(thoth.adviser.pseudonyms, pseudonym_entry)

            package_name = unit.configuration.get("package_name")
            if not package_name:
                raise PipelineConfigurationError(
                    f"Pipeline cannot be constructed as unit {unit.name!r} of type Pseudonym "
                    f"did not provide any package name configuration: {unit.configuration!r}"
                )

            pseudonyms.setdefault(package_name, []).append(unit)

        sieves: Dict[Optional[str], List["SieveType"]] = {}
        for sieve_entry in dict_.pop("sieves", []) or []:
            sieve_unit: "SieveType" = cls._do_instantiate_from_dict(thoth.adviser.sieves, sieve_entry)
            package_name = sieve_unit.configuration.get("package_name")
            sieves.setdefault(package_name, []).append(sieve_unit)

        steps: Dict[Optional[str], List["StepType"]] = {}
        for step_entry in dict_.pop("steps", []) or []:
            step_unit: "StepType" = cls._do_instantiate_from_dict(thoth.adviser.steps, step_entry)
            package_name = step_unit.configuration.get("package_name")
            steps.setdefault(package_name, []).append(step_unit)

        strides: Dict[Optional[str], List["StrideType"]] = {}
        for stride_entry in dict_.pop("strides", []) or []:
            stride_unit: "StrideType" = cls._do_instantiate_from_dict(thoth.adviser.strides, stride_entry)
            package_name = stride_unit.configuration.get("package_name")
            strides.setdefault(package_name, []).append(stride_unit)

        wraps: Dict[Optional[str], List["WrapType"]] = {}
        for wrap_entry in dict_.pop("wraps", []) or []:
            wrap_unit: "WrapType" = cls._do_instantiate_from_dict(thoth.adviser.wraps, wrap_entry)
            package_name = wrap_unit.configuration.get("package_name")
            wraps.setdefault(package_name, []).append(wrap_unit)

        if dict_:
            _LOGGER.warning("Unknown entry in pipeline configuration: %r", dict_)

        pipeline = PipelineConfig(
            boots=boots,
            pseudonyms=pseudonyms,
            sieves=sieves,
            steps=steps,
            strides=strides,
            wraps=wraps,
        )
        _LOGGER.debug(
            "Pipeline configuration creation ended, configuration:\n%s",
            json.dumps(pipeline.to_dict(), indent=2),
        )
        return pipeline

    @classmethod
    def load(cls, config: str) -> "PipelineConfig":
        """Load pipeline configuration from a file or a string."""
        if os.path.isfile(config):
            _LOGGER.debug("Loading pipeline configuration from file %r", config)
            with open(config, "r") as config_file:
                config = config_file.read()

        return cls.from_dict(yaml.safe_load(config))

    @classmethod
    def get_adviser_pipeline_config(
        cls,
        *,
        recommendation_type: RecommendationType,
        graph: GraphDatabase,
        project: Project,
        labels: Dict[str, str],
        library_usage: Optional[Dict[str, Any]],
        prescription: Optional["Prescription"],
        cli_parameters: Dict[str, Any],
    ) -> PipelineConfig:
        """Get adviser's pipeline configuration."""
        return cls._build_configuration(
            PipelineBuilderContext(
                graph=graph,
                project=project,
                labels=labels,
                library_usage=library_usage,
                recommendation_type=recommendation_type,
                prescription=prescription,
                cli_parameters=cli_parameters,
            )
        )

    @classmethod
    def get_dependency_monkey_pipeline_config(
        cls,
        *,
        decision_type: DecisionType,
        graph: GraphDatabase,
        project: Project,
        labels: Dict[str, str],
        library_usage: Optional[Dict[str, Any]],
        prescription: Optional["Prescription"],
        cli_parameters: Dict[str, Any],
    ) -> PipelineConfig:
        """Get dependency-monkey's pipeline configuration."""
        return cls._build_configuration(
            PipelineBuilderContext(
                graph=graph,
                project=project,
                labels=labels,
                library_usage=library_usage,
                decision_type=decision_type,
                prescription=prescription,
                cli_parameters=cli_parameters,
            )
        )
