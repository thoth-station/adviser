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

"""Test resolution of software packages."""

import attr
import pytest
import flexmock

from collections import OrderedDict
from copy import deepcopy
import itertools
from typing import List
import random

from thoth.adviser.context import Context
from thoth.adviser.resolver import Resolver
from thoth.adviser.state import State
from thoth.adviser.beam import Beam
from thoth.adviser.predictor import Predictor
from thoth.adviser.pipeline_config import PipelineConfig
from thoth.adviser.pipeline_builder import PipelineBuilder
from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import DecisionType
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages import GraphDatabase

from thoth.adviser.exceptions import BootError
from thoth.adviser.exceptions import CannotProduceStack
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.exceptions import SieveError
from thoth.adviser.exceptions import StepError
from thoth.adviser.exceptions import StrideError
from thoth.adviser.exceptions import UnresolvedDependencies
from thoth.adviser.exceptions import WrapError

import tests.units.boots as boots
import tests.units.sieves as sieves
import tests.units.steps as steps
import tests.units.strides as strides
import tests.units.wraps as wraps

from .base import AdviserTestCase


@pytest.fixture
def tf_package_versions() -> List[PackageVersion]:
    """Return a list of package versions - TensorFlow samples."""
    pypi = Source("https://pypi.org/simple")
    return [
        PackageVersion(
            name="tensorflow", version="==1.9.0rc1", index=pypi, develop=False
        ),
        PackageVersion(name="tensorflow", version="==1.9.0", index=pypi, develop=False),
        PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://thoth-station.ninja/simple"),
            develop=False,
        ),
    ]


@pytest.fixture
def numpy_package_versions() -> List[PackageVersion]:
    """Return a list of package versions - numpy samples."""
    pypi = Source("https://pypi.org/simple")
    return [
        PackageVersion(name="numpy", version="==1.17.0", index=pypi, develop=False),
        PackageVersion(name="numpy", version="==1.17.1", index=pypi, develop=False),
        PackageVersion(name="numpy", version="==1.17.2", index=pypi, develop=False),
        PackageVersion(name="numpy", version="==1.17.3", index=pypi, develop=False),
    ]


@pytest.fixture
def package_versions() -> List[PackageVersion]:
    """Return a list of package versions - TensorFlow samples."""
    pypi = Source("https://pypi.org/simple")
    return [
        PackageVersion(name="numpy", version="==1.17.4", index=pypi, develop=False),
        PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://thoth-station.ninja/simple"),
            develop=False,
        ),
        PackageVersion(name="flask", version="==1.1.1", index=pypi, develop=False),
    ]


class TestResolver(AdviserTestCase):
    """Test resolution algorithm and its compatibility with Python ecosystem."""

    def test_run_boots(self, resolver: Resolver) -> None:
        """Test running pipeline boots."""
        flexmock(boots.Boot1)
        flexmock(boots.Boot2)

        boots.Boot1.should_receive("run").and_return(None).ordered()
        boots.Boot2.should_receive("run").and_return(None).ordered()

        resolver.pipeline.boots = [boots.Boot1(), boots.Boot2()]

        assert resolver._run_boots() is None

    def test_run_boots_error(self, resolver: Resolver) -> None:
        """Test running pipeline boots raising boot specific error if any error occurs."""
        flexmock(boots.Boot1)
        boots.Boot1.should_receive("run").and_raise(ValueError).once()

        resolver.pipeline.boots = [boots.Boot1()]

        with pytest.raises(BootError):
            resolver._run_boots()

    def test_run_sieves(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test running pipeline sieves."""
        flexmock(sieves.Sieve1)
        flexmock(sieves.Sieve2)

        for package_version in tf_package_versions:
            sieves.Sieve1.should_receive("run").with_args(package_version).and_return(
                None
            ).ordered()
            sieves.Sieve2.should_receive("run").with_args(package_version).and_return(
                None
            ).ordered()

        resolver.pipeline.sieves = [sieves.Sieve1(), sieves.Sieve2()]

        resolver._run_sieves(*tf_package_versions)

    def test_run_sieves_error(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test raising sieve specific error by resolver if any error occurs."""
        flexmock(sieves.Sieve1)

        sieves.Sieve1.should_receive("run").with_args(tf_package_versions[0]).and_raise(
            ValueError
        ).once()
        resolver.pipeline.sieves = [sieves.Sieve1()]

        with pytest.raises(SieveError):
            resolver._run_sieves(*tf_package_versions)

    def test_run_sieves_not_acceptable(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test raising not acceptable causes filtering of packages."""
        flexmock(sieves.Sieve1)
        sieves.Sieve1.should_receive("run").with_args(
            tf_package_versions[0]
        ).and_return(None).ordered()
        sieves.Sieve1.should_receive("run").with_args(tf_package_versions[1]).and_raise(
            NotAcceptable
        ).ordered()
        sieves.Sieve1.should_receive("run").with_args(
            tf_package_versions[2]
        ).and_return(None).ordered()

        resolver.pipeline.sieves = [sieves.Sieve1()]

        assert resolver._run_sieves(*tf_package_versions[:3]) == [
            tf_package_versions[0],
            tf_package_versions[2],
        ]

    def test_run_steps(
        self, resolver: Resolver, package_versions: List[PackageVersion]
    ) -> None:
        """Test running pipeline steps."""
        state = State()
        state.score = 0.1
        state.add_justification([{"hello": "thoth"}])
        state.resolved_dependencies["hexsticker"] = (
            "hexsticker",
            "1.2.0",
            "https://pypi.org/simple",
        )

        flexmock(steps.Step1)
        flexmock(steps.Step2)

        steps.Step1.should_receive("run").with_args(
            state, package_versions[0]
        ).and_return((1.0, None)).ordered()
        steps.Step2.should_receive("run").with_args(
            state, package_versions[0]
        ).and_return((0.5, [{"foo": 1}])).ordered()

        steps.Step1.should_receive("run").with_args(
            state, package_versions[1]
        ).and_return(None).ordered()
        steps.Step2.should_receive("run").with_args(
            state, package_versions[1]
        ).and_return((None, None)).ordered()

        steps.Step1.should_receive("run").with_args(
            state, package_versions[2]
        ).and_return((None, [{"baz": "bar"}])).ordered()
        steps.Step2.should_receive("run").with_args(
            state, package_versions[2]
        ).and_return(None).ordered()

        resolver.pipeline.steps = [steps.Step1(), steps.Step2()]

        beam = Beam()

        assert resolver._run_steps(beam, state, *package_versions[:3]) is None
        assert beam.size == 1
        assert beam.top().to_dict() == {
            "advised_runtime_environment": None,
            "justification": [{"hello": "thoth"}, {"foo": 1}, {"baz": "bar"}],
            "resolved_dependencies": state.resolved_dependencies,
            "score": 1.6,
            "unresolved_dependencies": OrderedDict(
                ((p.name, p.to_tuple()) for p in package_versions)
            ),
        }

        assert state.score == 0.1, "Score of the original state is not untouched"
        assert state.justification == [
            {"hello": "thoth"}
        ], "Justification of the original score is not untouched"

    def test_run_steps_not_acceptable(
        self, resolver: Resolver, package_versions: List[PackageVersion]
    ) -> None:
        """Test running steps when not acceptable is raised."""
        state = State()
        state.score = 0.1
        state.add_justification([{"hello": "thoth"}])
        state.resolved_dependencies["hexsticker"] = (
            "hexsticker",
            "1.2.0",
            "https://pypi.org/simple",
        )

        original_state = deepcopy(state)

        flexmock(steps.Step1)
        flexmock(steps.Step2)

        steps.Step1.should_receive("run").with_args(
            state, package_versions[0]
        ).and_return((1.0, {"baz": "bar"})).ordered()
        steps.Step2.should_receive("run").with_args(
            state, package_versions[0]
        ).and_raise(NotAcceptable).ordered()

        resolver.pipeline.steps = [steps.Step1(), steps.Step2()]

        beam = Beam()

        assert resolver._run_steps(beam, state, *package_versions[:3]) is None
        assert beam.size == 0
        assert original_state == state, "State is not unoutched"

    def test_run_steps_error(
        self, resolver: Resolver, package_versions: List[PackageVersion]
    ) -> None:
        """Test running steps produces a step specific error."""
        state = State()
        state.score = 0.1
        state.add_justification([{"hello": "thoth"}])
        state.resolved_dependencies["hexsticker"] = (
            "hexsticker",
            "1.2.0",
            "https://pypi.org/simple",
        )

        original_state = deepcopy(state)

        flexmock(steps.Step1)
        steps.Step1.should_receive("run").with_args(
            state, package_versions[0]
        ).and_raise(NameError).once()

        resolver.pipeline.steps = [steps.Step1()]

        # Beam set to None, it should not be used.
        with pytest.raises(StepError):
            assert resolver._run_steps(None, state, *package_versions[:3])

        assert original_state == state, "State is not untouched"

    def test_run_strides(self, resolver: Resolver) -> None:
        """Test running pipeline strides."""
        state = State()
        state.score = 0.1
        state.add_justification([{"ehlo": "esmtp"}])

        original_state = deepcopy(state)

        flexmock(strides.Stride1)
        flexmock(strides.Stride2)

        strides.Stride1.should_receive("run").with_args(state).and_return(None).once()
        strides.Stride2.should_receive("run").with_args(state).and_return(None).once()

        resolver.pipeline.strides = [strides.Stride1(), strides.Stride2()]

        assert resolver._run_strides(state) is True
        assert original_state == state, "State is not untouched"

    def test_run_strides_not_acceptable(self, resolver: Resolver) -> None:
        """Test running pipeline strides."""
        state = State()
        state.score = 0.1
        state.add_justification([{"khoor": "zruogv"}])

        original_state = deepcopy(state)

        flexmock(strides.Stride1)
        flexmock(strides.Stride2)

        strides.Stride1.should_receive("run").with_args(state).and_return(None).once()
        strides.Stride2.should_receive("run").with_args(state).and_raise(
            NotAcceptable
        ).once()

        resolver.pipeline.strides = [strides.Stride1(), strides.Stride2()]

        assert resolver._run_strides(state) is False
        assert original_state == state, "State is not untouched"

    def test_run_strides_error(self, resolver: Resolver) -> None:
        """Test running pipeline strides."""
        state = State()
        state.score = 0.1
        state.add_justification([{"khoor": "zruogv"}])

        original_state = deepcopy(state)

        flexmock(strides.Stride1)

        strides.Stride1.should_receive("run").with_args(state).and_raise(
            NotImplementedError
        ).once()
        resolver.pipeline.strides = [strides.Stride1()]

        with pytest.raises(StrideError):
            resolver._run_strides(state)

        assert original_state == state, "State is not untouched"

    def test_run_wraps(self, resolver: Resolver) -> None:
        """Test running pipeline wraps."""
        state = State()
        state.score = 0.01
        state.add_justification([{"uhg": "kdw"}])

        original_state = deepcopy(state)

        flexmock(wraps.Wrap1)
        flexmock(wraps.Wrap2)
        wraps.Wrap1.should_receive("run").with_args(state).and_return(None).once()
        wraps.Wrap2.should_receive("run").with_args(state).and_return(None).once()

        resolver.pipeline.wraps = [wraps.Wrap1(), wraps.Wrap2()]

        assert resolver._run_wraps(state) is None
        assert original_state == state, "State has changed during running wraps"

    def test_run_wraps_error(self, resolver: Resolver) -> None:
        """Test running pipeline wraps and raising a wrap error."""
        state = State()
        state.score = 0.42
        state.add_justification([{"iulgrolq": "srnruqb"}])

        original_state = deepcopy(state)

        flexmock(wraps.Wrap1)
        wraps.Wrap1.should_receive("run").with_args(state).and_raise(ValueError).once()

        resolver.pipeline.wraps = [wraps.Wrap1()]

        with pytest.raises(WrapError):
            resolver._run_wraps(state)

        assert original_state == state, "State has changed during running wraps"

    def test_resolve_direct_dependencies_multiple_error(
        self, resolver: Resolver
    ) -> None:
        """Test error produced if no direct dependencies were resolved."""
        solver_mock = flexmock()
        solver_mock.should_receive("solve").with_args(
            list(resolver.project.iter_dependencies(with_devel=True)), graceful=True
        ).and_return([]).once()

        resolver._solver = solver_mock
        with pytest.raises(
            UnresolvedDependencies, match="No direct dependencies were resolved"
        ) as exc:
            resolver._resolve_direct_dependencies(with_devel=True)

        assert exc.value.unresolved == [
            package_version.name
            for package_version in resolver.project.iter_dependencies(with_devel=True)
        ]

    def test_resolve_direct_dependencies_some_error(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test error produced if not all direct dependencies were resolved."""
        solver_mock = flexmock()
        solver_mock.should_receive("solve").with_args(
            list(resolver.project.iter_dependencies(with_devel=True)), graceful=True
        ).and_return({"tensorflow": tf_package_versions, "numpy": []}).once()

        resolver._solver = solver_mock
        with pytest.raises(
            UnresolvedDependencies, match="Unable to resolve all direct dependencies"
        ) as exc:
            resolver._resolve_direct_dependencies(with_devel=True)

        assert exc.value.unresolved == ["numpy"]

    def test_resolve_direct_dependencies(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test resolving multiple direct dependencies."""
        resolved = {
            "tensorflow": tf_package_versions,
            "numpy": [
                PackageVersion(
                    name="numpy",
                    version="==1.1.1",
                    index=Source("https://pypi.org/simple"),
                    develop=False,
                )
            ],
        }
        solver_mock = flexmock()
        solver_mock.should_receive("solve").with_args(
            list(resolver.project.iter_dependencies(with_devel=True)), graceful=True
        ).and_return(resolved).once()

        resolver._solver = solver_mock
        assert resolver._resolve_direct_dependencies(with_devel=True) == resolved

    @pytest.mark.parametrize("limit", [2, 1, None])
    def test_semver_sort_and_limit_latest_versions(
        self, limit, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test no limit on latest versions in when sorting based on semver."""
        assert (
            len(tf_package_versions) > 2
        ), "Not enough package versions to perform test case"

        resolver.limit_latest_versions = limit

        # reversed from oldest to latest by default.
        sorted_tf_package_versions = list(reversed(tf_package_versions))
        random.shuffle(tf_package_versions)

        result = resolver._semver_sort_and_limit_latest_versions(*tf_package_versions)
        if limit is not None:
            assert len(result) == limit
            assert result == sorted_tf_package_versions[:limit]
        else:
            assert result == sorted_tf_package_versions

    def test_prepare_initial_state_cannot_produce_stack(
        self,
        resolver: Resolver,
        tf_package_versions: List[PackageVersion],
        numpy_package_versions: List[PackageVersion],
    ) -> None:
        """Test preparing initial state for predictor."""
        resolver.should_receive("_resolve_direct_dependencies").with_args(
            with_devel=True
        ).and_return(
            {"numpy": numpy_package_versions, "tensorflow": tf_package_versions}
        ).once()

        # This is dependent on dict order, Python 3.6+ required.
        resolver.should_receive("_run_sieves").with_args(
            *numpy_package_versions
        ).and_return(numpy_package_versions).ordered()
        resolver.should_receive("_run_sieves").with_args(
            *tf_package_versions
        ).and_return([]).ordered()

        resolver._init_context()
        with pytest.raises(CannotProduceStack):
            resolver._prepare_initial_states(with_devel=True)

    def test_prepare_initial_state(
        self,
        resolver: Resolver,
        tf_package_versions: List[PackageVersion],
        numpy_package_versions: List[PackageVersion],
    ) -> None:
        """Test preparing initial state for predictor."""
        resolver.should_receive("_resolve_direct_dependencies").with_args(
            with_devel=True
        ).and_return(
            {"numpy": numpy_package_versions, "tensorflow": tf_package_versions}
        ).once()

        # This is dependent on dict order, Python 3.6+ required.
        resolver.should_receive("_run_sieves").with_args(
            *numpy_package_versions
        ).and_return(numpy_package_versions).ordered()
        resolver.should_receive("_run_sieves").with_args(
            *tf_package_versions
        ).and_return(tf_package_versions).ordered()

        # Default steps do not filter out any state, let't produce them all in this case.
        resolver._init_context()
        beam = resolver._prepare_initial_states(with_devel=True)

        for package_version in itertools.chain(numpy_package_versions, tf_package_versions):
            assert (
                resolver.context.get_package_version(package_version.to_tuple())
                is package_version
            ), "Not all packages registered in resolver context"

        combinations = list(
            itertools.product(
                [pv.to_tuple() for pv in numpy_package_versions],
                [pv.to_tuple() for pv in tf_package_versions],
            )
        )

        assert beam.size == len(tf_package_versions) * len(
            numpy_package_versions
        ), "Incorrect number of initial states produced"

        for state in beam.iter_states():
            assert state.score == 0.0
            assert state.justification == []
            assert "numpy" in state.unresolved_dependencies
            assert "tensorflow" in state.unresolved_dependencies

            combination = (
                state.unresolved_dependencies["numpy"],
                state.unresolved_dependencies["tensorflow"],
            )
            assert (
                combination in combinations
            ), "Wrong combination of initial states produced"

    def test_resolve_no_stack(self, resolver: Resolver) -> None:
        """Test report creation during resolution."""
        with pytest.raises(ValueError):
            assert resolver.context, "Context is already bound to resolver"

        resolver.should_receive("resolve_products").with_args(with_devel=False).and_return([]).once()

        with pytest.raises(CannotProduceStack, match="No stack was produced"):
            resolver.resolve(with_devel=False)

    def test_resolve(self, resolver: Resolver) -> None:
        """Test report creation during resolution."""
        product = flexmock(score=1.0)
        resolver.should_receive("resolve_products").with_args(with_devel=True).and_return([product]).once()
        resolver.pipeline.should_receive("call_post_run_report").once()
        resolver.predictor.should_receive("post_run_report").once()

        stack_info = [{"foo": "bar"}]
        flexmock(Context).new_instances(flexmock(stack_info=stack_info))

        with pytest.raises(ValueError):
            assert resolver.context, "Context is already bound to resolver"

        report = resolver.resolve(with_devel=True)

        assert resolver.context is not None, "Context is not bound to resolver"
        assert report.product_count() == 1
        assert report.iter_products() == [product]
        assert report.stack_info is stack_info

    def test_get_adviser_instance(self, predictor_mock: Predictor) -> None:
        """Test getting a resolver for adviser."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("is_connected").and_return(True).once()
        graph_mock = GraphDatabase()

        kwargs = {
            "predictor": predictor_mock,
            "beam_width": 4,
            "count": 10,
            "graph": graph_mock,
            "library_usage": {"foo": "bar"},
            "limit": 5,
            "limit_latest_versions": 5,
            "project": flexmock(),
            "recommendation_type": RecommendationType.LATEST,
        }

        pipeline = flexmock(PipelineConfig)

        flexmock(PipelineBuilder)
        PipelineBuilder.should_receive("get_adviser_pipeline_config").with_args(
            recommendation_type=kwargs["recommendation_type"],
            project=kwargs["project"],
            library_usage=kwargs["library_usage"],
            graph=graph_mock,
        ).and_return(pipeline).once()

        resolver = Resolver.get_adviser_instance(**kwargs)

        assert pipeline is pipeline
        assert resolver.project is kwargs["project"]
        assert resolver.library_usage is kwargs["library_usage"]
        assert resolver.graph is graph_mock
        assert resolver.predictor is predictor_mock
        assert resolver.recommendation_type == kwargs["recommendation_type"]
        assert resolver.decision_type is None
        assert resolver.limit == kwargs["limit"]
        assert resolver.count == kwargs["count"]
        assert resolver.beam_width == kwargs["beam_width"]
        assert resolver.limit_latest_versions == kwargs["limit_latest_versions"]

    def test_get_dependency_monkey_instance(self, predictor_mock: Predictor) -> None:
        """Test getting a resolver for dependency monkey."""
        graph_mock = flexmock()
        flexmock(GraphDatabase).new_instances(graph_mock)
        graph_mock.should_receive("is_connected").and_return(False).once()
        graph_mock.should_receive("connect").and_return(None).once()

        kwargs = {
            "predictor": predictor_mock,
            "beam_width": 10000,
            "count": 1022,
            "library_usage": {"foo": "bar"},
            "limit_latest_versions": 5,
            "project": flexmock(),
            "decision_type": DecisionType.ALL,
        }

        pipeline = flexmock(PipelineConfig)

        flexmock(PipelineBuilder)
        PipelineBuilder.should_receive("get_dependency_monkey_pipeline_config").with_args(
            decision_type=kwargs["decision_type"],
            project=kwargs["project"],
            library_usage=kwargs["library_usage"],
            graph=graph_mock,
        ).and_return(pipeline).once()

        resolver = Resolver.get_dependency_monkey_instance(**kwargs)

        assert pipeline is pipeline
        assert resolver.project is kwargs["project"]
        assert resolver.library_usage is kwargs["library_usage"]
        assert resolver.graph is graph_mock
        assert resolver.predictor is predictor_mock
        assert resolver.recommendation_type is None
        assert resolver.decision_type == kwargs["decision_type"]
        assert resolver.limit == kwargs["count"]
        assert resolver.count == kwargs["count"]
        assert resolver.beam_width == kwargs["beam_width"]
        assert resolver.limit_latest_versions == kwargs["limit_latest_versions"]
