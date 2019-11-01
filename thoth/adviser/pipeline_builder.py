#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

import logging
import json
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Union
from typing import Optional
from typing import Set

import attr
from thoth.python import Project
from thoth.storages import GraphDatabase
import thoth.adviser.boots
import thoth.adviser.sieves
import thoth.adviser.steps
import thoth.adviser.strides
import thoth.adviser.wraps

from .enums import DecisionType
from .enums import RecommendationType
from .exceptions import InternalError
from .pipeline_config import PipelineConfig
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
    recommendation_type = attr.ib(
        type=Optional[RecommendationType], kw_only=True, default=None
    )
    boots = attr.ib(type=List[Boot], default=attr.Factory(list), kw_only=True)
    sieves = attr.ib(type=List[Sieve], default=attr.Factory(list), kw_only=True)
    steps = attr.ib(type=List[Step], default=attr.Factory(list), kw_only=True)
    strides = attr.ib(type=List[Stride], default=attr.Factory(list), kw_only=True)
    wraps = attr.ib(type=List[Wrap], default=attr.Factory(list), kw_only=True)
    _boots_included = attr.ib(type=Set[Any], default=attr.Factory(set), kw_only=True)
    _sieves_included = attr.ib(type=Set[Any], default=attr.Factory(set), kw_only=True)
    _steps_included = attr.ib(type=Set[Any], default=attr.Factory(set), kw_only=True)
    _strides_included = attr.ib(type=Set[Any], default=attr.Factory(set), kw_only=True)
    _wraps_included = attr.ib(type=Set[Any], default=attr.Factory(set), kw_only=True)

    def is_included(self, unit_class: type) -> bool:
        """Check if the given pipeline unit is already included in the pipeline configuration."""
        if issubclass(unit_class, Boot):
            return unit_class in self._boots_included
        if issubclass(unit_class, Sieve):
            return unit_class in self._sieves_included
        elif issubclass(unit_class, Step):
            return unit_class in self._steps_included
        elif issubclass(unit_class, Stride):
            return unit_class in self._strides_included

        raise InternalError(f"Unknown unit of type {unit_class.__name__!r}")

    def is_adviser_pipeline(self) -> bool:
        """Check if the pipeline built is meant for adviser."""
        return self.decision_type is None and self.recommendation_type is not None

    def is_dependency_monkey_pipeline(self) -> bool:
        """Check if the pipeline built is meant for Dependency Monkey."""
        return self.decision_type is not None and self.recommendation_type is None

    def add_unit(self, unit: Unit) -> None:
        """Add the given unit to pipeline configuration."""
        if isinstance(unit, Boot):
            self._boots_included.add(unit.__class__)
            self.boots.append(unit)
            return
        if isinstance(unit, Sieve):
            self._sieves_included.add(unit.__class__)
            self.sieves.append(unit)
            return
        elif isinstance(unit, Step):
            self._steps_included.add(unit.__class__)
            self.steps.append(unit)
            return
        elif isinstance(unit, Stride):
            self._strides_included.add(unit.__class__)
            self.strides.append(unit)
            return
        elif isinstance(unit, Wrap):
            self._wraps_included.add(unit.__class__)
            self.wraps.append(unit)
            return

        raise InternalError(
            f"Unknown unit {unit!r} of type {unit.__class__.__name__!r}"
        )


@attr.s(slots=True)
class PipelineBuilder:
    """Builder responsible for creating pipeline configuration from the project and its library usage."""

    def __init__(self) -> None:
        """Instantiation of the pipeline builder - do NOT instantiate this class."""
        raise NotImplemented("Cannot instantiate pipeline builder")

    @staticmethod
    def _iter_units() -> Generator[Union[Sieve, Step, Stride], None, None]:
        """Iterate over pipeline units available in this implementation."""
        for boot_name in thoth.adviser.boots.__all__:
            yield getattr(thoth.adviser.boots, boot_name)

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
        _LOGGER.debug("Creating pipeline configuration")
        change = True
        while change:
            change = False
            for unit_class in cls._iter_units():
                unit_configuration = unit_class.should_include(ctx)
                if unit_configuration is None:
                    _LOGGER.debug(
                        "Pipeline unit %r will not be included in the pipeline configuration in this round",
                        unit_class.__name__,  # type: ignore
                    )
                    continue

                change = True

                _LOGGER.debug(
                    "Including pipeline unit %r in pipeline configuration with unit configuration %r",
                    unit_class.__name__,  # type: ignore
                    unit_configuration,
                )
                unit_instance = unit_class(  # type: ignore
                    graph=ctx.graph,
                    project=ctx.project,
                    library_usage=ctx.library_usage,
                )

                if unit_configuration:
                    unit_instance.update_parameters(unit_configuration)

                ctx.add_unit(unit_instance)

        pipeline = PipelineConfig(
            boots=ctx.boots,
            sieves=ctx.sieves,
            steps=ctx.steps,
            strides=ctx.strides,
            wraps=ctx.wraps,
        )
        _LOGGER.debug(
            "Pipeline configuration creation ended, configuration:\n%s",
            json.dumps(pipeline.to_dict(), indent=2),
        )
        return pipeline

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
    def get_dependency_monkey_config(
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
