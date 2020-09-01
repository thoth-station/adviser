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

"""File conftest.py for pytest test suite."""

from typing import Callable
from collections import OrderedDict

import pytest
import flexmock

from thoth.adviser.context import Context
from thoth.adviser.beam import Beam
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.pipeline_config import PipelineConfig
from thoth.adviser.resolver import Resolver
from thoth.adviser.predictor import Predictor
from thoth.adviser.state import State
from thoth.common import RuntimeEnvironment
from thoth.python import Project

from .units.boots import Boot1
from .units.sieves import Sieve1
from .units.steps import Step1
from .units.strides import Stride1
from .units.wraps import Wrap1

from thoth.storages import GraphDatabase

from .base import AdviserTestCase


class PredictorMock(Predictor):
    """A mocked predictor for testing, which always returns a random index to beam."""

    def run(self) -> int:
        """Run the main method used for predictor."""
        return self.context.beam.get_random()


@pytest.fixture
def context(project: Project) -> Context:
    """Create a fixture for a clean context."""
    flexmock(Context)
    flexmock(Beam)
    flexmock(GraphDatabase)

    return Context(
        project=project,
        graph=GraphDatabase(),
        library_usage=None,
        limit=100,
        count=3,
        beam=Beam(),
        recommendation_type=RecommendationType.LATEST,
    )


@pytest.fixture
def pipeline_config() -> PipelineConfig:
    """Create a fixture for a pipeline configuration with few representatives of each pipeline unit type."""
    flexmock(PipelineConfig)

    flexmock(Boot1)
    flexmock(Sieve1)
    flexmock(Step1)
    flexmock(Stride1)
    flexmock(Wrap1)

    return PipelineConfig(boots=[Boot1()], sieves=[Sieve1()], steps=[Step1()], strides=[Stride1()], wraps=[Wrap1()],)


@pytest.fixture
def project() -> Project:
    """Create a fixture for a project representation."""
    flexmock(Project)
    flexmock(RuntimeEnvironment)

    pipfile_path = AdviserTestCase.data_dir / "projects" / "Pipfile"
    pipfile_lock_path = AdviserTestCase.data_dir / "projects" / "Pipfile.lock"

    return Project.from_files(
        pipfile_path=str(pipfile_path),
        pipfile_lock_path=str(pipfile_lock_path),
        runtime_environment=RuntimeEnvironment.from_dict({}),
    )


@pytest.fixture
def graph() -> GraphDatabase:
    """Create a knowledge graph connector fixture."""
    flexmock(GraphDatabase)

    graph = GraphDatabase()
    graph.connect()
    return graph


@pytest.fixture
def predictor_mock() -> Predictor:
    """Return a mock for predictor."""
    flexmock(PredictorMock)

    return PredictorMock()


@pytest.fixture
def predictor_mock_class() -> type:
    """Return a predictor mock class."""
    flexmock(PredictorMock)

    return PredictorMock


@pytest.fixture
def resolver(pipeline_config: PipelineConfig, project: Project, predictor_mock: Predictor) -> Resolver:
    """Create a resolver instance for tests."""
    flexmock(Resolver)
    flexmock(GraphDatabase)
    flexmock(Beam)

    return Resolver(
        pipeline=pipeline_config,
        project=project,
        library_usage={},
        graph=GraphDatabase(),
        predictor=predictor_mock,
        recommendation_type=RecommendationType.LATEST,
        limit=Resolver.DEFAULT_LIMIT,
        count=Resolver.DEFAULT_COUNT,
        beam_width=Resolver.DEFAULT_BEAM_WIDTH,
        limit_latest_versions=Resolver.DEFAULT_LIMIT_LATEST_VERSIONS,
    )


def _get_state() -> State:
    """Create a fixture for a non-final state."""
    unresolved_dependency = ("flask", "1.1.1", "https://pypi.org/simple")
    unresolved_dependencies = OrderedDict([(id(unresolved_dependency), unresolved_dependency)])
    state = State(
        score=0.1,
        unresolved_dependencies=OrderedDict({"flask": unresolved_dependencies}),
        resolved_dependencies=OrderedDict({"hexsticker": ("hexsticker", "1.0.0", "https://pypi.org/simple")}),
        advised_runtime_environment=RuntimeEnvironment.from_dict({"python_version": "3.6"}),
    )
    state.add_justification([{"foo": "bar"}, {"bar": "baz"}])
    return state


@pytest.fixture
def state() -> State:
    """Create a fixture for a non-final state."""
    return _get_state()


@pytest.fixture(scope="session")
def state_factory() -> Callable[[], State]:
    """Return a state - handy to be used in tests requiring hypothesis."""
    return _get_state


@pytest.fixture
def builder_context(project: Project) -> PipelineBuilderContext:
    """Create a fixture for a pipeline builder context."""
    flexmock(PipelineBuilderContext)
    flexmock(GraphDatabase)

    return PipelineBuilderContext(
        graph=GraphDatabase(),
        project=project,
        library_usage=None,
        decision_type=None,
        recommendation_type=RecommendationType.LATEST,
    )
