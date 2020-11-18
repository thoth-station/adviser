#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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
from typing import List
from typing import Optional
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
from .pseudonym import Pseudonym
from .boot import Boot
from .sieve import Sieve
from .step import Step
from .stride import Stride
from .wrap import Wrap
from .unit import Unit

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PipelineBuilderContext:
    """A context passed to units to determine if they want to participate in a pipeline."""

    graph = attr.ib(type=GraphDatabase, kw_only=True, default=None)
    project = attr.ib(type=Project, kw_only=True, default=None)
    library_usage = attr.ib(type=Optional[Dict[str, Any]], kw_only=True, default=None)
    decision_type = attr.ib(type=Optional[DecisionType], kw_only=True, default=None)
    recommendation_type = attr.ib(type=Optional[RecommendationType], kw_only=True, default=None)

    _boots = attr.ib(type=Dict[Optional[str], List[Boot]], factory=dict, kw_only=True)
    _pseudonyms = attr.ib(type=Dict[str, List[Pseudonym]], factory=dict, kw_only=True)
    _sieves = attr.ib(type=Dict[Optional[str], List[Sieve]], factory=dict, kw_only=True)
    _steps = attr.ib(type=Dict[Optional[str], List[Step]], factory=dict, kw_only=True)
    _strides = attr.ib(type=Dict[Optional[str], List[Stride]], factory=dict, kw_only=True)
    _wraps = attr.ib(type=Dict[Optional[str], List[Wrap]], factory=dict, kw_only=True)
    _boots_included = attr.ib(type=Dict[str, List[Boot]], factory=dict, kw_only=True)
    _pseudonyms_included = attr.ib(type=Dict[str, List[Pseudonym]], factory=dict, kw_only=True)
    _sieves_included = attr.ib(type=Dict[str, List[Sieve]], factory=dict, kw_only=True)
    _steps_included = attr.ib(type=Dict[str, List[Step]], factory=dict, kw_only=True)
    _strides_included = attr.ib(type=Dict[str, List[Stride]], factory=dict, kw_only=True)
    _wraps_included = attr.ib(type=Dict[str, List[Wrap]], factory=dict, kw_only=True)

    @property
    def boots(self) -> List[Boot]:
        """Get all boots registered to this pipeline builder context."""
        return list(chain(*self._boots.values()))

    @property
    def boots_dict(self) -> Dict[Optional[str], List[Boot]]:
        """Get boots as a dictionary mapping."""
        return self._boots

    @property
    def pseudonyms(self) -> List[Pseudonym]:
        """Get all pseudonyms registered to this pipeline builder context."""
        return list(chain(*self._pseudonyms.values()))

    @property
    def pseudonyms_dict(self) -> Dict[str, List[Pseudonym]]:
        """Get pseudonyms as a dictionary mapping."""
        return self._pseudonyms

    @property
    def sieves(self) -> List[Sieve]:
        """Get all sieves registered to this pipeline builder context."""
        return list(chain(*self._sieves.values()))

    @property
    def sieves_dict(self) -> Dict[Optional[str], List[Sieve]]:
        """Get sieves as a dictionary mapping."""
        return self._sieves

    @property
    def steps(self) -> List[Step]:
        """Get all steps registered to this pipeline builder context."""
        return list(chain(*self._steps.values()))

    @property
    def steps_dict(self) -> Dict[Optional[str], List[Step]]:
        """Get steps as a dictionary mapping."""
        return self._steps

    @property
    def strides(self) -> List[Stride]:
        """Get all strides registered to this pipeline builder context."""
        return list(chain(*self._strides.values()))

    @property
    def strides_dict(self) -> Dict[Optional[str], List[Stride]]:
        """Get strides as a dictionary mapping."""
        return self._strides

    @property
    def wraps(self) -> List[Wrap]:
        """Get all wraps registered to this pipeline builder context."""
        return list(chain(*self._wraps.values()))

    @property
    def wraps_dict(self) -> Dict[Optional[str], List[Wrap]]:
        """Get wraps as a dictionary mapping."""
        return self._wraps

    def __attrs_post_init__(self) -> None:
        """Verify we have only adviser or dependency monkey specific builder."""
        if self.decision_type is not None and self.recommendation_type is not None:
            raise ValueError("Cannot instantiate builder for adviser and dependency monkey at the same time")

        if self.decision_type is None and self.recommendation_type is None:
            raise ValueError("Cannot instantiate builder context not specific to adviser nor dependency monkey")

    def is_included(self, unit_class: type) -> bool:
        """Check if the given pipeline unit is already included in the pipeline configuration."""
        if issubclass(unit_class, Boot):
            return unit_class.__name__ in self._boots_included
        elif issubclass(unit_class, Pseudonym):
            return unit_class.__name__ in self._pseudonyms_included
        elif issubclass(unit_class, Sieve):
            return unit_class.__name__ in self._sieves_included
        elif issubclass(unit_class, Step):
            return unit_class.__name__ in self._steps_included
        elif issubclass(unit_class, Stride):
            return unit_class.__name__ in self._strides_included
        elif issubclass(unit_class, Wrap):
            return unit_class.__name__ in self._wraps_included

        raise InternalError(f"Unknown unit {unit_class.__name__!r}")

    def get_included_boots(self, boot_class: type) -> List[Boot]:
        """Get included boots of the provided boot class."""
        assert issubclass(boot_class, Boot)
        return self._boots_included.get(boot_class.__name__, [])

    def get_included_pseudonyms(self, pseudonym_class: type) -> List[Pseudonym]:
        """Get included sieves of the provided sieve class."""
        assert issubclass(pseudonym_class, Pseudonym)
        return self._pseudonyms_included.get(pseudonym_class.__name__, [])

    def get_included_sieves(self, sieve_class: type) -> List[Sieve]:
        """Get included sieves of the provided sieve class."""
        assert issubclass(sieve_class, Sieve)
        return self._sieves_included.get(sieve_class.__name__, [])

    def get_included_steps(self, step_class: type) -> List[Step]:
        """Get included steps of the provided step class."""
        assert issubclass(step_class, Step)
        return self._steps_included.get(step_class.__name__, [])

    def get_included_strides(self, stride_class: type) -> List[Stride]:
        """Get included strides of the provided stride class."""
        assert issubclass(stride_class, Stride)
        return self._strides_included.get(stride_class.__name__, [])

    def get_included_wraps(self, wrap_class: type) -> List[Wrap]:
        """Get included wraps of the provided wrap class."""
        assert issubclass(wrap_class, Wrap)
        return self._wraps_included.get(wrap_class.__name__, [])

    def is_adviser_pipeline(self) -> bool:
        """Check if the pipeline built is meant for adviser."""
        return self.decision_type is None and self.recommendation_type is not None

    def is_dependency_monkey_pipeline(self) -> bool:
        """Check if the pipeline built is meant for Dependency Monkey."""
        return self.decision_type is not None and self.recommendation_type is None

    def add_unit(self, unit: Unit) -> None:
        """Add the given unit to pipeline configuration."""
        package_name: Optional[str] = unit.configuration.get("package_name")

        if isinstance(unit, Boot):
            self._boots_included.setdefault(unit.__class__.__name__, []).append(unit)
            self._boots.setdefault(package_name, []).append(unit)
            return
        elif isinstance(unit, Pseudonym):
            if not package_name:
                raise PipelineConfigurationError(
                    f"Pipeline cannot be constructed as unit {unit.__class__.__name__!r} of type Pseudonym "
                    f"did not provide any package name configuration: {unit.configuration!r}"
                )
            self._pseudonyms_included.setdefault(unit.__class__.__name__, []).append(unit)
            self._pseudonyms.setdefault(package_name, []).append(unit)
            return
        elif isinstance(unit, Sieve):
            self._sieves_included.setdefault(unit.__class__.__name__, []).append(unit)
            self._sieves.setdefault(package_name, []).append(unit)
            return
        elif isinstance(unit, Step):
            self._steps_included.setdefault(unit.__class__.__name__, []).append(unit)
            self._steps.setdefault(package_name, []).append(unit)
            return
        elif isinstance(unit, Stride):
            self._strides_included.setdefault(unit.__class__.__name__, []).append(unit)
            self._strides.setdefault(package_name, []).append(unit)
            return
        elif isinstance(unit, Wrap):
            self._wraps_included.setdefault(unit.__class__.__name__, []).append(unit)
            self._wraps.setdefault(package_name, []).append(unit)
            return

        raise InternalError(f"Unknown unit {unit!r} of type {unit.__class__.__name__!r}")


class PipelineBuilder:
    """Builder responsible for creating pipeline configuration from the project and its library usage."""

    __slots__: List[str] = []

    def __init__(self) -> None:
        """Instantiate of the pipeline builder - do NOT instantiate this class."""
        raise NotImplementedError("Cannot instantiate pipeline builder")

    @staticmethod
    def _iter_units() -> Generator[type, None, None]:
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

        for pseudonym_name in thoth.adviser.pseudonyms.__all__:
            yield getattr(thoth.adviser.pseudonyms, pseudonym_name)

        for sieve_name in thoth.adviser.sieves.__all__:
            yield getattr(thoth.adviser.sieves, sieve_name)

        for step_name in thoth.adviser.steps.__all__:
            yield getattr(thoth.adviser.steps, step_name)

        for stride_name in thoth.adviser.strides.__all__:
            yield getattr(thoth.adviser.strides, stride_name)

        for wrap_name in thoth.adviser.wraps.__all__:
            yield getattr(thoth.adviser.wraps, wrap_name)

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
        while change:
            change = False
            for unit_class in cls._iter_units():
                if unit_class.__name__ in blocked_units:
                    _LOGGER.debug(
                        "Avoiding adding pipeline unit %r based on blocked units configuration",
                        unit_class.__name__,
                    )
                    continue

                unit_configuration = unit_class.should_include(ctx)  # type: ignore
                if unit_configuration is None:
                    _LOGGER.debug(
                        "Pipeline unit %r will not be included in the pipeline configuration in this round",
                        unit_class.__name__,
                    )
                    continue

                change = True

                _LOGGER.debug(
                    "Including pipeline unit %r in pipeline configuration with unit configuration %r",
                    unit_class.__name__,
                    unit_configuration,
                )
                unit_instance = unit_class()

                # Always perform update, even with an empty dict. Update triggers a schema check.
                try:
                    unit_instance.update_configuration(unit_configuration)
                except Exception as exc:
                    raise PipelineConfigurationError(
                        f"Filed to initialize pipeline unit configuration for {unit_class.__name__!r} "
                        f"with configuration {unit_configuration!r}: {str(exc)}"
                    ) from exc

                ctx.add_unit(unit_instance)

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
    def _do_instantiate_from_dict(module: object, configuration_entry: Dict[str, Any]) -> Unit:
        """Instantiate a pipeline unit from a dict representation."""
        if "name" not in configuration_entry:
            raise ValueError(f"No pipeline unit name provided in the configuration entry: {configuration_entry!r}")

        try:
            unit_class = getattr(module, configuration_entry["name"])
        except AttributeError as exc:
            raise UnknownPipelineUnitError(f"Cannot import unit {configuration_entry['name']}: {str(exc)}") from exc

        unit: Unit = unit_class()

        if configuration_entry.get("configuration"):
            try:
                unit.update_configuration(configuration_entry["configuration"])
            except Exception as exc:
                raise PipelineConfigurationError(
                    f"Filed to initialize pipeline unit configuration for {unit_class.__name__!r} "
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

        boots: Dict[Optional[str], List[Boot]] = {}
        for boot_entry in dict_.pop("boots", []) or []:
            boot_unit: Boot = cls._do_instantiate_from_dict(thoth.adviser.boots, boot_entry)  # type: ignore
            package_name = boot_unit.configuration.get("package_name")
            boots.setdefault(package_name, []).append(boot_unit)

        pseudonyms: Dict[str, List[Pseudonym]] = {}
        for pseudonym_entry in dict_.pop("pseudonyms", []) or []:
            unit: Pseudonym = cls._do_instantiate_from_dict(thoth.adviser.pseudonyms, pseudonym_entry)  # type: ignore

            package_name = unit.configuration.get("package_name")
            if not package_name:
                raise PipelineConfigurationError(
                    f"Pipeline cannot be constructed as unit {unit.__class__.__name__!r} of type Pseudonym "
                    f"did not provide any package name configuration: {unit.configuration!r}"
                )

            pseudonyms.setdefault(package_name, []).append(unit)

        sieves: Dict[Optional[str], List[Sieve]] = {}
        for sieve_entry in dict_.pop("sieves", []) or []:
            sieve_unit: Sieve = cls._do_instantiate_from_dict(thoth.adviser.sieves, sieve_entry)  # type: ignore
            package_name = sieve_unit.configuration.get("package_name")
            sieves.setdefault(package_name, []).append(sieve_unit)

        steps: Dict[Optional[str], List[Step]] = {}
        for step_entry in dict_.pop("steps", []) or []:
            step_unit: Step = cls._do_instantiate_from_dict(thoth.adviser.steps, step_entry)  # type: ignore
            package_name = step_unit.configuration.get("package_name")
            steps.setdefault(package_name, []).append(step_unit)

        strides: Dict[Optional[str], List[Stride]] = {}
        for stride_entry in dict_.pop("strides", []) or []:
            stride_unit: Stride = cls._do_instantiate_from_dict(thoth.adviser.strides, stride_entry)  # type: ignore
            package_name = stride_unit.configuration.get("package_name")
            strides.setdefault(package_name, []).append(stride_unit)

        wraps: Dict[Optional[str], List[Wrap]] = {}
        for wrap_entry in dict_.pop("wraps", []) or []:
            wrap_unit: Wrap = cls._do_instantiate_from_dict(thoth.adviser.wraps, wrap_entry)  # type: ignore
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
        library_usage: Optional[Dict[str, Any]],
    ) -> PipelineConfig:
        """Get adviser's pipeline configuration."""
        return cls._build_configuration(
            PipelineBuilderContext(
                graph=graph,
                project=project,
                library_usage=library_usage,
                recommendation_type=recommendation_type,
            )
        )

    @classmethod
    def get_dependency_monkey_pipeline_config(
        cls,
        *,
        decision_type: DecisionType,
        graph: GraphDatabase,
        project: Project,
        library_usage: Optional[Dict[str, Any]],
    ) -> PipelineConfig:
        """Get dependency-monkey's pipeline configuration."""
        return cls._build_configuration(
            PipelineBuilderContext(
                graph=graph,
                project=project,
                library_usage=library_usage,
                decision_type=decision_type,
            )
        )
