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

"""Test resolution of software packages."""

import pytest
import flexmock

import gc
import math
from collections import OrderedDict
from copy import deepcopy
import itertools
from typing import List
from typing import Generator
import random

from thoth.adviser.beam import Beam
from thoth.adviser.resolver import Resolver
from thoth.adviser.state import State
from thoth.adviser.predictor import Predictor
from thoth.adviser.product import Product
from thoth.adviser.pipeline_config import PipelineConfig
from thoth.adviser.pipeline_builder import PipelineBuilder
from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import DecisionType
from thoth.adviser.step import Step
from thoth.adviser.sieve import Sieve
from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import PipfileLock
from thoth.python import Source
from thoth.python import Project
from thoth.storages import GraphDatabase
from thoth.storages.exceptions import NotFoundError

from thoth.adviser.exceptions import BootError
from thoth.adviser.exceptions import SkipPackage
from thoth.adviser.exceptions import CannotProduceStack
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.exceptions import SieveError
from thoth.adviser.exceptions import StepError
from thoth.adviser.exceptions import StrideError
from thoth.adviser.exceptions import UnresolvedDependencies
from thoth.adviser.exceptions import WrapError
from thoth.adviser.exceptions import EagerStopPipeline
from thoth.adviser.exceptions import UserLockFileError
from thoth.adviser.exceptions import PipelineUnitError

import tests.units.boots as boots
import tests.units.sieves as sieves
import tests.units.steps as steps
import tests.units.strides as strides
import tests.units.wraps as wraps

from .base import AdviserTestCase


@pytest.fixture
def package_version() -> List[PackageVersion]:
    """Return a package version."""
    return PackageVersion(name="tensorflow", version="==2.0.0", index=Source("https://pypi.org/simple"), develop=False,)


@pytest.fixture
def tf_package_versions() -> List[PackageVersion]:
    """Return a list of package versions - TensorFlow samples."""
    pypi = Source("https://pypi.org/simple")
    return [
        PackageVersion(name="tensorflow", version="==1.9.0rc1", index=pypi, develop=False),
        PackageVersion(name="tensorflow", version="==1.9.0", index=pypi, develop=False),
        PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://thoth-station.ninja/simple"), develop=False,
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
def flask_package_versions() -> List[PackageVersion]:
    """Return a list of package versions - numpy samples."""
    pypi = Source("https://pypi.org/simple")
    return [
        PackageVersion(name="flask", version="==1.1.1", index=pypi, develop=False),
        PackageVersion(name="flask", version="==1.1.0", index=pypi, develop=False),
        PackageVersion(name="flask", version="==1.0.0", index=pypi, develop=False),
    ]


@pytest.fixture
def package_versions() -> List[PackageVersion]:
    """Return a list of package versions - TensorFlow samples."""
    pypi = Source("https://pypi.org/simple")
    return [
        PackageVersion(name="numpy", version="==1.17.4", index=pypi, develop=False),
        PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://thoth-station.ninja/simple"), develop=False,
        ),
        PackageVersion(name="flask", version="==1.1.1", index=pypi, develop=False),
    ]


@pytest.fixture
def state() -> State:
    """Get a sample of a state - the state is not final and not initial."""
    state = State(score=0.5)
    state.add_unresolved_dependency(("tensorflow", "2.0.0", "https://pypi.org/simple"))
    state.add_resolved_dependency(("numpy", "1.17.4", "https://pypi.org/simple"))
    return state


@pytest.fixture
def final_state() -> State:
    """Return a final state."""
    return State(
        score=0.5,
        unresolved_dependencies=OrderedDict(
            (
                ("tensorflow", ("tensorflow", "2.0.0", "https://pypi.org/simple")),
                ("numpy", ("numpy", "1.17.4", "https://pypi.org/simple")),
            )
        ),
        resolved_dependencies=OrderedDict(),
        advised_runtime_environment=RuntimeEnvironment.from_dict({}),
    )


class _Functools32SkipPackageSieve(Sieve):
    """A mock to skip functools32 package."""

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        for pv in package_versions:
            if pv.name == "functools32":
                raise SkipPackage

            yield pv


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

    def test_run_boots_not_acceptable(self, resolver: Resolver) -> None:
        """Test running pipeline boots with not acceptable exception raised."""
        flexmock(boots.Boot1)
        flexmock(boots.Boot2)

        boots.Boot1.should_receive("run").and_return(None).ordered()
        boots.Boot2.should_receive("run").and_raise(NotAcceptable).ordered()

        resolver.pipeline.boots = [boots.Boot1(), boots.Boot2()]

        with pytest.raises(CannotProduceStack):
            resolver.resolve()

    def test_run_boots_error(self, resolver: Resolver) -> None:
        """Test running pipeline boots raising boot specific error if any error occurs."""
        flexmock(boots.Boot1)
        boots.Boot1.should_receive("run").and_raise(ValueError).once()

        resolver.pipeline.boots = [boots.Boot1()]

        with pytest.raises(BootError):
            resolver._run_boots()

    def test_run_sieves(self, resolver: Resolver, tf_package_versions: List[PackageVersion]) -> None:
        """Test running pipeline sieves."""
        flexmock(sieves.Sieve1)
        flexmock(sieves.Sieve2)

        # We use object here as flexmock has no direct support for generator args. Tests
        # for generator args are done in sieve related testsuite.
        sieves.Sieve1.should_receive("run").with_args(object).and_yield(*tf_package_versions).once()
        sieves.Sieve2.should_receive("run").with_args(object).and_yield(*tf_package_versions).once()

        resolver.pipeline.sieves = [sieves.Sieve1(), sieves.Sieve2()]

        assert list(resolver._run_sieves(tf_package_versions)) == tf_package_versions

    def test_run_sieves_error(self, resolver: Resolver, tf_package_versions: List[PackageVersion]) -> None:
        """Test raising sieve specific error by resolver if any error occurs."""
        flexmock(sieves.Sieve1)

        sieves.Sieve1.should_receive("run").with_args(object).and_raise(ValueError).once()
        resolver.pipeline.sieves = [sieves.Sieve1()]

        with pytest.raises(SieveError):
            list(resolver._run_sieves(tf_package_versions))

    def test_run_sieves_not_acceptable(self, resolver: Resolver, tf_package_versions: List[PackageVersion]) -> None:
        """Test raising not acceptable causes filtering of packages."""
        flexmock(sieves.Sieve1)

        sieves.Sieve1.should_receive("run").with_args(object).and_raise(NotAcceptable).once()

        resolver.pipeline.sieves = [sieves.Sieve1()]

        assert list(resolver._run_sieves(tf_package_versions)) == []

    def test_run_steps_not_acceptable(self, resolver: Resolver, package_version: PackageVersion) -> None:
        """Test running steps when not acceptable is raised."""
        state1 = State()
        state1.score = 0.1
        state1.add_justification([{"hello": "thoth"}])
        state1.add_resolved_dependency(("hexsticker", "1.2.0", "https://pypi.org/simple"))

        flexmock(steps.Step1)
        flexmock(steps.Step2)

        steps.Step1.should_receive("run").with_args(state1, package_version).and_return(
            (1.0, [{"baz": "bar"}])
        ).ordered()

        steps.Step2.should_receive("run").with_args(state1, package_version).and_raise(NotAcceptable).ordered()

        resolver.pipeline.steps = [steps.Step1(), steps.Step2()]

        resolver._init_context()

        resolver.predictor.should_receive("set_reward_signal").with_args(
            state1, package_version.to_tuple(), math.nan
        ).once()
        resolver.beam.should_receive("remove").with_args(state1).and_return(None).once()

        assert resolver.beam.size == 0
        assert resolver._run_steps(state1, package_version, {"numpy": [("numpy", "1.18.0")]}) is None
        assert resolver.beam.size == 0

    def test_run_steps_step_error(self, resolver: Resolver, package_version: PackageVersion) -> None:
        """Test raising a step error when a step raises an unexpected error."""
        state = State()
        state.score = 0.1
        state.add_justification([{"hello": "thoth"}])
        state.add_unresolved_dependency(("hexsticker", "1.2.0", "https://pypi.org/simple"))

        original_state = deepcopy(state)

        flexmock(steps.Step1)
        steps.Step1.should_receive("run").with_args(state, package_version).and_raise(NameError).once()

        resolver.pipeline.steps = [steps.Step1()]

        with pytest.raises(StepError):
            resolver._run_steps(
                state, package_version, {"flask": [("flask", "0.12", "https://pypi.org/simple")]},
            )

        assert original_state == state, "State is not untouched"

    def test_run_steps_multi_package_resolution(self, resolver: Resolver, package_version: PackageVersion) -> None:
        """Test running pipeline step with a multi package resolution flag set."""
        flexmock(steps.Step1)
        flexmock(steps.Step2)

        state = State()

        package_version_tuple = package_version.to_tuple()
        state.add_resolved_dependency(package_version_tuple)
        state.add_unresolved_dependency(package_version_tuple)
        # Discard optimization path which reuses already existing state.
        state.add_unresolved_dependency(
            (package_version_tuple[0], package_version_tuple[1] + "dev0", package_version_tuple[2])
        )

        resolver.pipeline.steps = [steps.Step1(), steps.Step2()]

        steps.Step1.MULTI_PACKAGE_RESOLUTIONS = True
        steps.Step2.MULTI_PACKAGE_RESOLUTIONS = False

        resolver._init_context()
        resolver.context.iteration = state.iteration + 1

        resolver.pipeline.steps[0].should_receive("run").with_args(state, package_version).and_return(None).once()
        resolver.pipeline.steps[1].should_receive("run").times(0)

        dependency_tuple = ("flask", "0.12", "https://pypi.org/simple")

        state_returned = resolver._run_steps(state, package_version, {"flask": [dependency_tuple]})
        assert state_returned is not None
        assert state_returned is not state
        assert state_returned.parent is state
        assert resolver.beam.size == 1
        assert resolver.beam.max() is not state

        state_added = resolver.beam.max()

        assert state_added is state_returned
        assert set(state_added.iter_resolved_dependencies()) == (
            set(state.iter_resolved_dependencies()) | {package_version.to_tuple()}
        )
        assert list(state_added.iter_unresolved_dependencies()) == [dependency_tuple]

    def test_run_steps_error(self, resolver: Resolver, package_version: PackageVersion) -> None:
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
        steps.Step1.should_receive("run").with_args(state, package_version).and_raise(NameError).once()

        resolver.pipeline.steps = [steps.Step1()]

        with pytest.raises(StepError):
            resolver._run_steps(
                state, package_version, {"flask": ("flask", "1.0.0", "https://pypi.org/simple")},
            )

        assert original_state == state, "State is not untouched"

    @pytest.mark.parametrize("score", [float("inf"), float("nan")])
    def test_run_steps_inf_nan(self, score: float, resolver: Resolver, package_version: PackageVersion):
        """Run tests for inf and NaN."""
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
        steps.Step1.should_receive("run").with_args(state, package_version).and_return((score, [{"foo": "bar"}])).once()

        resolver.pipeline.steps = [steps.Step1()]

        with pytest.raises(StepError):
            resolver._run_steps(
                state, package_version, {"flask": ("flask", "1.0.0", "https://pypi.org/simple")},
            )

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
        strides.Stride2.should_receive("run").with_args(state).and_raise(NotAcceptable).once()

        resolver.pipeline.strides = [strides.Stride1(), strides.Stride2()]

        resolver._init_context()
        assert resolver._run_strides(state) is False
        assert original_state == state, "State is not untouched"

    def test_run_strides_error(self, resolver: Resolver) -> None:
        """Test running pipeline strides."""
        state = State()
        state.score = 0.1
        state.add_justification([{"khoor": "zruogv"}])

        original_state = deepcopy(state)

        flexmock(strides.Stride1)

        strides.Stride1.should_receive("run").with_args(state).and_raise(NotImplementedError).once()
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

    def test_resolve_direct_dependencies_multiple_error(self, resolver: Resolver) -> None:
        """Test error produced if no direct dependencies were resolved."""
        solver_mock = flexmock()
        solver_mock.should_receive("solve").with_args(
            sorted(resolver.project.iter_dependencies(with_devel=True), key=lambda p: p.name,), graceful=True,
        ).and_return({}).once()

        resolver._solver = solver_mock
        with pytest.raises(UnresolvedDependencies, match="Unable to resolve all direct dependencies") as exc:
            resolver._resolve_direct_dependencies(with_devel=True)

        assert exc.value.unresolved == [
            package_version.name for package_version in resolver.project.iter_dependencies(with_devel=True)
        ]

    def test_resolve_direct_dependencies_some_error(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test error produced if not all direct dependencies were resolved."""
        solver_mock = flexmock()
        solver_mock.should_receive("solve").with_args(
            sorted(resolver.project.iter_dependencies(with_devel=True), key=lambda p: p.name,), graceful=True,
        ).and_return({"tensorflow": tf_package_versions, "flask": []}).once()

        resolver._solver = solver_mock
        with pytest.raises(UnresolvedDependencies, match="Unable to resolve all direct dependencies") as exc:
            resolver._resolve_direct_dependencies(with_devel=True)

        assert exc.value.unresolved == ["flask"]

    def test_resolve_direct_dependencies(self, resolver: Resolver, tf_package_versions: List[PackageVersion]) -> None:
        """Test resolving multiple direct dependencies."""
        resolved = {
            "tensorflow": tf_package_versions,
            "flask": [
                PackageVersion(name="numpy", version="==1.1.1", index=Source("https://pypi.org/simple"), develop=False,)
            ],
        }
        solver_mock = flexmock()
        solver_mock.should_receive("solve").with_args(
            sorted(resolver.project.iter_dependencies(with_devel=True), key=lambda p: p.name,), graceful=True,
        ).and_return(resolved).once()

        resolver._solver = solver_mock
        assert resolver._resolve_direct_dependencies(with_devel=True) == resolved

    def test_prepare_initial_state_limit_latest_versions(
        self,
        resolver: Resolver,
        tf_package_versions: List[PackageVersion],
        flask_package_versions: List[PackageVersion],
    ) -> None:
        """Test limiting number of latest versions considered."""
        resolver.limit_latest_versions = 2
        resolver.pipeline.boots = []
        resolver.pipeline.sieves = []
        resolver.pipeline.steps = []
        resolver.pipeline.strides = []
        resolver.pipeline.wraps = []

        tf_package_versions.sort(key=lambda pv: pv.semantic_version, reverse=True)
        flask_package_versions.sort(key=lambda pv: pv.semantic_version, reverse=True)

        tf_package_versions_shuffled = list(tf_package_versions)
        random.shuffle(tf_package_versions_shuffled)
        flask_package_versions_shuffled = list(flask_package_versions)
        random.shuffle(flask_package_versions_shuffled)

        resolver.should_receive("_resolve_direct_dependencies").with_args(with_devel=False).and_return(
            {"tensorflow": tf_package_versions_shuffled, "flask": flask_package_versions_shuffled,}
        ).once()

        resolver.should_receive("_run_sieves").with_args(tf_package_versions).and_return(tf_package_versions).ordered()

        resolver.should_receive("_run_sieves").with_args(flask_package_versions).and_return(
            flask_package_versions
        ).ordered()

        resolver._init_context()
        resolver._prepare_initial_state(with_devel=False)
        assert resolver.beam.size == 1

        state = resolver.beam.max()
        assert "flask" in state.unresolved_dependencies
        assert "tensorflow" in state.unresolved_dependencies

        unresolved_dependencies = set(state.iter_unresolved_dependencies())
        assert len(unresolved_dependencies) == 4
        assert tf_package_versions[0].to_tuple() in unresolved_dependencies
        assert tf_package_versions[1].to_tuple() in unresolved_dependencies
        assert flask_package_versions[0].to_tuple() in unresolved_dependencies
        assert flask_package_versions[1].to_tuple() in unresolved_dependencies

    def test_prepare_initial_state_cannot_produce_stack(
        self,
        resolver: Resolver,
        tf_package_versions: List[PackageVersion],
        numpy_package_versions: List[PackageVersion],
    ) -> None:
        """Test preparing initial state for predictor."""
        resolver.should_receive("_resolve_direct_dependencies").with_args(with_devel=True).and_return(
            {"numpy": numpy_package_versions, "tensorflow": tf_package_versions}
        ).once()

        # This is dependent on dict order, Python 3.6+ required.
        resolver.should_receive("_run_sieves").with_args(object).and_yield(*numpy_package_versions).ordered()
        resolver.should_receive("_run_sieves").with_args(object).and_yield(*[]).ordered()

        resolver._init_context()
        with pytest.raises(CannotProduceStack):
            resolver._prepare_initial_state(with_devel=True)

    def test_prepare_initial_state(
        self,
        resolver: Resolver,
        tf_package_versions: List[PackageVersion],
        numpy_package_versions: List[PackageVersion],
    ) -> None:
        """Test preparing initial state for predictor."""
        resolver.should_receive("_resolve_direct_dependencies").with_args(with_devel=True).and_return(
            {"numpy": numpy_package_versions, "tensorflow": tf_package_versions}
        ).once()

        # This is dependent on dict order, Python 3.6+ required.
        resolver.should_receive("_run_sieves").with_args(object).and_yield(*numpy_package_versions).ordered()
        resolver.should_receive("_run_sieves").with_args(object).and_yield(*tf_package_versions).ordered()

        flexmock(Beam)
        resolver.beam.should_receive("wipe").with_args().and_return(None).once()
        resolver._init_context()
        assert resolver._prepare_initial_state(with_devel=True) is None

        for package_version in itertools.chain(numpy_package_versions, tf_package_versions):
            assert (
                resolver.context.get_package_version(package_version.to_tuple()) is package_version
            ), "Not all packages registered in resolver context"

        assert resolver.beam.size == 1

        state = resolver.beam.max()
        unresolved_dependencies = set(state.iter_unresolved_dependencies())
        assert unresolved_dependencies == (
            {pv.to_tuple() for pv in numpy_package_versions} | {pv.to_tuple() for pv in tf_package_versions}
        )
        assert list(state.iter_resolved_dependencies()) == []

    def test_expand_state_not_found_one_unresolved(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state (with one unresolved dependency) when a package was not found."""
        assert len(list(state.iter_unresolved_dependencies())) == 1
        to_expand_package_tuple = state.get_first_unresolved_dependency()

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            extras=["postgresql"],
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        )

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset(["postgresql", None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_raise(NotFoundError).once()
        resolver.predictor.should_receive("set_reward_signal").with_args(
            state, to_expand_package_tuple, math.nan
        ).once()
        assert resolver._expand_state(state, to_expand_package_tuple) is None
        assert resolver.beam.size == 0

    def test_expand_state_not_found_more_unresolved(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state (with more unresolved dependencies) when a package was not found."""
        to_expand_package_tuple = state.get_first_unresolved_dependency()
        additional_package_tuple = (to_expand_package_tuple[0], "1.2.0.dev", "https://pypi.org/simple")

        state.add_unresolved_dependency(additional_package_tuple)

        assert len(list(state.iter_unresolved_dependencies())) > 1

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            extras=["postgresql"],
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        )

        resolver.context.register_package_tuple(
            additional_package_tuple,
            develop=False,
            extras=None,
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        )

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset(["postgresql", None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_raise(NotFoundError).once()
        resolver.predictor.should_receive("set_reward_signal").with_args(
            state, to_expand_package_tuple, math.nan
        ).once()
        assert resolver._expand_state(state, to_expand_package_tuple) is None
        assert resolver.beam.size == 1

    def test_expand_state_no_dependencies_final_simple(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state when the given package has no dependencies producing final state."""
        to_expand_package_tuple = state.get_random_unresolved_dependency()

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            extras=None,
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        )

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset([None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({}).once()

        assert len(state.unresolved_dependencies) == 1, (
            "State in the test case should have only once dependency to resolve in "
            "order to check production of a final state"
        )

        resolver.predictor.should_receive("set_reward_signal").with_args(
            object, to_expand_package_tuple, math.inf
        ).once()

        original_resolved_count = len(state.resolved_dependencies)

        assert resolver._expand_state(state, to_expand_package_tuple) is state, "State returned is not the one passed"

        # We test a fast-path when state can be directly returned.
        assert resolver.beam.size == 0
        assert to_expand_package_tuple in list(state.iter_resolved_dependencies())
        assert to_expand_package_tuple not in list(state.iter_unresolved_dependencies())
        assert len(state.resolved_dependencies) == original_resolved_count + 1
        assert len(state.unresolved_dependencies) == 0

    def test_expand_state_no_dependencies_final(self, resolver: Resolver, state: State) -> None:
        """Test state expansion with multiple dependencies of a same type."""
        to_expand_package_tuple = state.get_random_unresolved_dependency()
        additional_package_tuple = ("numpy", "1.0.0", "https://pypi.org/simple")

        assert to_expand_package_tuple != additional_package_tuple

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple, develop=False, extras=None, os_name="rhel", os_version="8.0", python_version="3.7",
        )

        resolver.context.register_package_tuple(
            additional_package_tuple,
            develop=False,
            extras=None,
            os_name="rhel",
            os_version="8.0",
            python_version="3.7",
        )

        state.add_unresolved_dependency(additional_package_tuple)

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset([None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({}).once()

        assert len(state.unresolved_dependencies) == 2

        resolver.predictor.should_receive("set_reward_signal").with_args(object, to_expand_package_tuple, 0.0).once()

        original_resolved_count = len(state.resolved_dependencies)
        original_unresolved_count = len(state.unresolved_dependencies)

        resolver.context.iteration = state.iteration + 1
        state_returned = resolver._expand_state(state, to_expand_package_tuple)
        assert state_returned is not None
        # An optimization that reuses object previously allocated as no dependencies were added by get_depends_on.
        assert state_returned is state

        assert resolver.beam.get_last() is state_returned
        assert resolver.beam.size == 1

        assert state.iteration == resolver.context.iteration
        assert to_expand_package_tuple in state.iter_resolved_dependencies()
        assert to_expand_package_tuple not in state.iter_unresolved_dependencies()
        assert additional_package_tuple in state.iter_unresolved_dependencies()
        assert len(state.resolved_dependencies) == original_resolved_count + 1
        assert len(state.unresolved_dependencies) == original_unresolved_count - 1

    def test_expand_state_no_dependencies_final_multiple_different(self, resolver: Resolver, state: State) -> None:
        """Test state expansion with multiple dependencies of a same type."""
        to_expand_package_tuple = ("connexion", "2.0.0", "https://pypi.org/simple")
        additional_package_tuple = ("connexion", "1.0.0", "https://pypi.org/simple")

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple, develop=False, extras=None, os_name="ubi", os_version="8.1", python_version="3.6",
        )

        resolver.context.register_package_tuple(
            additional_package_tuple, develop=False, extras=None, os_name="ubi", os_version="8.1", python_version="3.6",
        )

        state.add_unresolved_dependency(to_expand_package_tuple)
        state.add_unresolved_dependency(additional_package_tuple)

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset([None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({}).once()

        assert len(list(state.iter_unresolved_dependencies())) == 3

        resolver.predictor.should_receive("set_reward_signal").with_args(object, to_expand_package_tuple, 0.0).once()

        original_resolved_count = len(list(state.iter_resolved_dependencies()))
        original_unresolved_count = len(list(state.iter_unresolved_dependencies()))

        resolver.context.iteration = state.iteration + 1
        state_returned = resolver._expand_state(state, to_expand_package_tuple)
        assert state_returned is not state

        assert resolver.beam.get_last() is not state
        assert resolver.beam.get_last() is state_returned
        assert resolver.beam.size == 2

        assert to_expand_package_tuple not in state.iter_resolved_dependencies()
        assert to_expand_package_tuple not in state.iter_unresolved_dependencies()
        assert additional_package_tuple in state.iter_unresolved_dependencies()
        assert additional_package_tuple not in state.iter_resolved_dependencies()
        assert len(state.resolved_dependencies) == original_resolved_count
        assert len(state.unresolved_dependencies) == original_unresolved_count - 1

        assert to_expand_package_tuple in state_returned.iter_resolved_dependencies()
        assert to_expand_package_tuple not in state_returned.iter_unresolved_dependencies()
        assert additional_package_tuple not in state_returned.iter_resolved_dependencies()
        assert additional_package_tuple not in state_returned.iter_unresolved_dependencies()
        assert len(list(state_returned.iter_resolved_dependencies())) == original_resolved_count + 1
        # All dependencies of type to_expand_package_tuple[0] removed.
        assert len(list(state_returned.iter_unresolved_dependencies())) == original_unresolved_count - 2

    def test_expand_state_no_dependencies_final_multiple_same(self, resolver: Resolver, state: State) -> None:
        """Test state expansion with multiple dependencies without same type."""
        to_expand_package_tuple = ("connexion", "2.0.0", "https://pypi.org/simple")
        additional_package_tuple = ("connexion", "1.0.0", "https://pypi.org/simple")

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple, develop=False, extras=None, os_name="ubi", os_version="8.1", python_version="3.6",
        )

        resolver.context.register_package_tuple(
            additional_package_tuple, develop=False, extras=None, os_name="ubi", os_version="8.1", python_version="3.6",
        )

        # Discard any present.
        state.unresolved_dependencies = OrderedDict()
        state.add_unresolved_dependency(to_expand_package_tuple)
        state.add_unresolved_dependency(additional_package_tuple)

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset([None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({}).once()

        assert len(list(state.iter_unresolved_dependencies())) == 2

        resolver.predictor.should_receive("set_reward_signal").with_args(
            object, to_expand_package_tuple, math.inf
        ).once()

        original_resolved_count = len(list(state.iter_resolved_dependencies()))
        original_unresolved_count = len(list(state.iter_unresolved_dependencies()))

        resolver.context.iteration = state.iteration + 1
        state_added = resolver._expand_state(state, to_expand_package_tuple)
        assert state_added is not None
        assert state_added is not state

        assert resolver.beam.max() is state
        assert resolver.beam.size == 1

        assert to_expand_package_tuple not in state.iter_resolved_dependencies()
        assert to_expand_package_tuple not in state.iter_unresolved_dependencies()
        assert additional_package_tuple in state.iter_unresolved_dependencies()
        assert additional_package_tuple not in state.iter_resolved_dependencies()
        assert len(state.resolved_dependencies) == original_resolved_count
        assert len(state.unresolved_dependencies) == original_unresolved_count - 1

        assert to_expand_package_tuple in state_added.iter_resolved_dependencies()
        assert to_expand_package_tuple not in state_added.iter_unresolved_dependencies()
        assert additional_package_tuple not in state_added.iter_resolved_dependencies()
        assert additional_package_tuple not in state_added.iter_unresolved_dependencies()
        assert len(list(state_added.iter_resolved_dependencies())) == original_resolved_count + 1
        # All dependencies of type to_expand_package_tuple[0] removed.
        assert len(list(state_added.iter_unresolved_dependencies())) == 0

    def test_expand_state_no_intersection(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state with no intersected dependencies."""
        to_expand_package_tuple = ("tensorflow", "2.0.0", "https://pypi.org/simple")

        resolver.project.runtime_environment.operating_system.name = "fedora"
        resolver.project.runtime_environment.operating_system.version = "31"
        resolver.project.runtime_environment.python_version = "3.7"
        resolver.project.runtime_environment.platform = "linux-x86_64"

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
            extras=frozenset({None}),
            marker_evaluation_result=True,
            is_missing=False,
        ).and_return({None: [("absl-py", "0.9.0"), ("absl-py", "0.8.0")]}).once()

        absl_py_090_records = [
            {
                "package_name": "absl-py",
                "package_version": "0.9.0",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "31",
                "python_version": "3.7",
            }
        ]

        absl_py_080_records = [
            {
                "package_name": "absl-py",
                "package_version": "0.8.0",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "31",
                "python_version": "3.7",
            }
        ]

        # No intersected dependencies.
        state.add_unresolved_dependency(("absl-py", "0.7.0", "https://pypi.org/simple"))
        state.add_unresolved_dependency(("absl-py", "0.6.0", "https://pypi.org/simple"))

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="absl-py",
            package_version="0.9.0",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(absl_py_090_records).ordered()

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="absl-py",
            package_version="0.8.0",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(absl_py_080_records).ordered()

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        )

        resolver.predictor.should_receive("set_reward_signal").with_args(
            state, to_expand_package_tuple, math.nan
        ).once()
        assert resolver._expand_state(state, to_expand_package_tuple) is None

    def test_expand_state_sieves_discarded(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state but all dependencies are filtered out by sieves."""
        to_expand_package_tuple = ("tensorflow", "2.0.0", "https://pypi.org/simple")

        resolver.project.runtime_environment.operating_system.name = "fedora"
        resolver.project.runtime_environment.operating_system.version = "31"
        resolver.project.runtime_environment.python_version = "3.7"
        resolver.project.runtime_environment.platform = "linux-x86_64"

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
            extras=frozenset({None}),
            marker_evaluation_result=True,
            is_missing=False,
        ).and_return({None: [("absl-py", "0.8.0")]}).once()

        absl_py_080_records = [
            {
                "package_name": "absl-py",
                "package_version": "0.8.0",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "31",
                "python_version": "3.7",
            }
        ]

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="absl-py",
            package_version="0.8.0",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(absl_py_080_records).ordered()

        resolver._init_context()
        resolver.beam.add_state(state)

        resolver.pipeline.sieves[0].should_receive("run").with_args(object).and_raise(NotAcceptable).once()

        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        )

        resolver.predictor.should_receive("set_reward_signal").with_args(
            state, to_expand_package_tuple, math.nan
        ).once()
        assert resolver._expand_state(state, to_expand_package_tuple) is None

    def test_expand_state_intersection_adjust(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state with intersected dependencies - intersected dependencies are adjusted."""
        to_expand_package_tuple = ("tensorflow", "2.0.0", "https://pypi.org/simple")

        resolver.project.runtime_environment.operating_system.name = "rhel"
        resolver.project.runtime_environment.operating_system.version = "9"
        resolver.project.runtime_environment.python_version = "3.7"
        resolver.project.runtime_environment.platform = "linux-x86_64"

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
            extras=frozenset({None}),
            marker_evaluation_result=True,
            is_missing=False,
        ).and_return({None: [("absl-py", "0.9.0"), ("absl-py", "0.8.0")]}).once()

        absl_py_090_records = [
            {
                "package_name": "absl-py",
                "package_version": "0.9.0",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "31",
                "python_version": "3.7",
            }
        ]

        absl_py_080_records = [
            {
                "package_name": "absl-py",
                "package_version": "0.8.0",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "31",
                "python_version": "3.7",
            }
        ]

        # No intersected dependencies.
        state.add_unresolved_dependency(("absl-py", "0.8.0", "https://pypi.org/simple"))
        state.add_unresolved_dependency(("absl-py", "0.6.0", "https://pypi.org/simple"))
        state.add_unresolved_dependency(("tensorflow", "0.6.0", "https://pypi.org/simple"))

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="absl-py",
            package_version="0.9.0",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(absl_py_090_records).ordered()

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="absl-py",
            package_version="0.8.0",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(absl_py_080_records).ordered()

        resolver._init_context()
        resolver.beam.wipe()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        )

        resolver.context.iteration += 1

        resolver.pipeline.steps[0].should_receive("run").and_return((0.1, [])).once()
        resolver.predictor.should_receive("set_reward_signal").with_args(object, to_expand_package_tuple, 0.1).once()

        assert resolver.beam.size == 1
        state_returned = resolver._expand_state(state, to_expand_package_tuple)
        assert state_returned is not state
        assert resolver.beam.size == 2

        state0 = resolver.beam.get(0)
        state1 = resolver.beam.get(1)

        assert state0 is state
        assert state_returned is state1

        assert ("absl-py", "0.8.0", "https://pypi.org/simple",) in state.iter_unresolved_dependencies()
        assert ("absl-py", "0.6.0", "https://pypi.org/simple",) in state.iter_unresolved_dependencies()
        assert ("absl-py", "0.9.0", "https://pypi.org/simple",) not in state.iter_unresolved_dependencies()

        # Only ("absl-py", "0.8.0", "https://pypi.org/simple") is in intersection.

        assert ("absl-py", "0.8.0", "https://pypi.org/simple",) in state1.iter_unresolved_dependencies()
        assert ("absl-py", "0.9.0", "https://pypi.org/simple",) not in state1.iter_unresolved_dependencies()
        assert ("absl-py", "0.6.0", "https://pypi.org/simple",) not in state1.iter_unresolved_dependencies()

    def test_expand_state_no_dependencies_not_final(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state when the given package has no dependencies producing not final state."""
        to_expand_package_tuple = state.get_random_unresolved_dependency()

        # Add one more making sure there will be still some unresolved dependencies.
        assert (
            "flask" not in state.unresolved_dependencies
        ), "State cannot have package flask in unresolved for this test case"
        state.add_unresolved_dependency(("flask", "0.12", "https://pypi.org/simple"))

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            extras=["s3", "ui"],
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        )

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset(["s3", "ui", None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({}).once()

        resolver.predictor.should_receive("set_reward_signal").with_args(object, to_expand_package_tuple, 0.0).once()

        original_resolved_count = len(state.resolved_dependencies)

        resolver.context.iteration = state.iteration + 1
        returned_state = resolver._expand_state(state, to_expand_package_tuple)

        last_state_added = resolver.beam.get_last()

        assert resolver.beam.size == 1
        assert last_state_added in resolver.beam.iter_states()
        assert state in resolver.beam.iter_states()
        assert last_state_added is not None
        assert returned_state is not None
        assert returned_state is state
        assert returned_state is last_state_added
        assert to_expand_package_tuple in state.iter_resolved_dependencies()
        assert to_expand_package_tuple not in state.iter_unresolved_dependencies()
        assert len(state.resolved_dependencies) == original_resolved_count + 1
        assert "flask" in state.unresolved_dependencies

    def test_expand_state_add_dependencies_call(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state which results in a call for adding new dependencies."""
        to_expand_package_tuple = ("tensorflow", "2.0.0", "https://pypi.org/simple")

        pypi = Source("https://pypi.org/simple")
        dep_package_versions = [
            PackageVersion(name="absl-py", version="==0.8.1", index=pypi, develop=False),
            PackageVersion(name="absl-py", version="==0.8.2", index=pypi, develop=False),
            PackageVersion(name="tensorboard", version="==2.0.0", index=pypi, develop=False),
            PackageVersion(name="tensorboard", version="==2.0.1", index=pypi, develop=False),
        ]

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset([None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({None: [(pv.name, pv.locked_version) for pv in dep_package_versions]}).once()

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            extras=None,
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        )
        package_version = resolver.context.get_package_version(to_expand_package_tuple)

        resolver.should_receive("_expand_state_add_dependencies").with_args(
            state=state,
            package_version=package_version,
            dependencies=[(pv.name, pv.locked_version) for pv in dep_package_versions],
        ).and_return(None).once()

        assert resolver._expand_state(state, to_expand_package_tuple) is None

    def test_expand_state_add_dependencies_unsolved(self, resolver: Resolver) -> None:
        """Test aborting state expansion if dependency graph is not fully resolved."""
        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://pypi.org.simple"), extras=None, develop=False,
        )

        resolver.project.runtime_environment.should_receive("is_fully_specified").with_args().and_return(False)

        # As tensorflow has not resolved tensorboard dependency sub-graph, we will discard expanding state.
        tb_records = []
        absl_py_records = [
            {
                "package_name": "absl-py",
                "package_version": "0.8.1",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "29",
                "python_version": "3.6",
            }
        ]

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="absl-py",
            package_version="0.8.1",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(absl_py_records).once()

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="tensorboard",
            package_version="2.0.0",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(tb_records).once()

        state = State(score=0.0)

        resolver._init_context()
        resolver.predictor.should_receive("set_reward_signal").with_args(
            state, package_version.to_tuple(), math.nan
        ).once()
        resolver.context.register_package_version(package_version)
        resolver.beam.should_receive("remove").with_args(state).once()
        resolver._expand_state_add_dependencies(
            state=state, package_version=package_version, dependencies=[("absl-py", "0.8.1"), ("tensorboard", "2.0.0")],
        )

        assert resolver.beam.size == 0, "A new state was added even the dependency sub-graph is not resolved"

    def test_resolve_boot_error(self, resolver: Resolver):
        """Test raising an exception in boots causes halt of resolver."""
        assert resolver.pipeline.boots, "No boots in the pipeline configuration to run test with"

        resolver.pipeline.boots[0].should_receive("run").and_raise(ValueError).once()
        with pytest.raises(BootError):
            resolver.resolve(with_devel=False)

    @pytest.mark.parametrize("unit_type", ["boots", "sieves", "steps", "strides", "wraps"])
    def test_resolve_pre_run_error(self, unit_type: str, resolver: Resolver):
        """Test raising an exception in pre-run phase causes halt of resolver."""
        units = getattr(resolver.pipeline, unit_type)
        assert units, "No unit in the pipeline configuration to run test with"

        unit = units[0]
        unit.should_receive("pre_run").and_raise(ValueError).once()
        with pytest.raises(PipelineUnitError):
            resolver.resolve(with_devel=False)

    def test_do_resolve_states_limit_reached(self, resolver: Resolver) -> None:
        """Resolve states until the limit of generated states is reached."""
        assert resolver.pipeline.boots, "No boots in the pipeline configuration to run test with"
        assert resolver.pipeline.strides, "No strides in the pipeline configuration to run test with"
        assert resolver.pipeline.wraps, "No strides in the pipeline configuration to run test with"

        state1 = State(score=0.0)
        state1.add_unresolved_dependency(("thoth-pipenv", "2018.12.17", "https://pypi.org/simple"))
        state2 = State(score=1.0)
        state2.add_unresolved_dependency(("selinon", "1.0.0", "https://pypi.org/simple"))
        state3 = State(score=2.0)
        state2.add_unresolved_dependency(("hexsticker", "1.0.0", "https://pypi.org/simple"))

        resolver.beam.should_receive("new_iteration").and_return(None).times(2)
        resolver.beam.add_state(state1)
        resolver.beam.add_state(state2)
        resolver.beam.add_state(state3)

        resolver.limit = 1
        resolver._init_context()

        final_state = State(score=1.2)

        for boot in resolver.pipeline.boots:
            boot.should_receive("run").with_args().and_return(None).once()

        for stride in resolver.pipeline.strides:
            stride.should_receive("run").with_args(final_state).and_return(None).once()

        for wrap in resolver.pipeline.wraps:
            wrap.should_receive("run").with_args(final_state).and_return(None).once()

        resolver.should_receive("_prepare_initial_state").with_args(with_devel=True).and_return(resolver.beam).once()

        to_expand_package_tuple2 = state2.get_random_unresolved_dependency()
        to_expand_package_tuple1 = state1.get_random_unresolved_dependency()

        resolver.predictor.should_receive("run").with_args().and_return(state2, to_expand_package_tuple2).and_return(
            state1, to_expand_package_tuple1
        ).times(2)

        resolver.should_receive("_expand_state").with_args(state2, to_expand_package_tuple2).and_return(None).once()

        resolver.should_receive("_expand_state").with_args(state1, to_expand_package_tuple1).and_return(
            final_state
        ).once()

        states = list(resolver._do_resolve_states(with_devel=True, user_stack_scoring=True))
        assert states == [final_state]
        assert resolver.context.iteration == 2
        assert resolver.context.accepted_final_states_count == 1
        assert resolver.context.discarded_final_states_count == 0

    def test_expand_state_marker_true(self, resolver: Resolver) -> None:
        """Add a check for leaf dependency nodes for which environment markers apply and remove dependencies."""
        package_tuple = ("hexsticker", "1.0.0", "https://pypi.org/simple")
        state = State(score=1.0)
        state.add_unresolved_dependency(package_tuple)

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.project.runtime_environment.operating_system.name = "ubi"
        resolver.project.runtime_environment.operating_system.version = "8.1"
        resolver.project.runtime_environment.python_version = "3.6"

        resolver.graph.should_receive("get_depends_on").with_args(
            *package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
            extras=frozenset({None}),
            marker_evaluation_result=True,
            is_missing=False,
        ).and_return({"enum34": [("enum34", "1.1.6")]}).once()

        enum34_records = [
            {
                "package_name": "enum34",
                "package_version": "1.1.6",
                "index_url": "https://pypi.org/simple",
                "os_name": resolver.project.runtime_environment.operating_system.name,
                "os_version": resolver.project.runtime_environment.operating_system.version,
                "python_version": resolver.project.runtime_environment.python_version,
            }
        ]
        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="enum34",
            package_version="1.1.6",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(enum34_records).once()

        resolver.project.runtime_environment.should_receive("is_fully_specified").and_return(True).once()

        package_version = resolver.context.register_package_tuple(
            package_tuple, develop=False, os_name=None, os_version=None, python_version=None,
        )

        resolver.pipeline.steps[0].should_receive("run").with_args(state, package_version).and_return((0.1, [])).once()
        resolver.predictor.should_receive("set_reward_signal").with_args(object, package_tuple, 0.1).once()
        state_returned = resolver._expand_state(state, package_tuple)
        assert state_returned is not None
        assert resolver.beam.size == 1
        assert resolver.beam.get(0) is state_returned

        state = resolver.beam.max()
        assert state_returned is state

        assert list(state.iter_unresolved_dependencies()) == [("enum34", "1.1.6", "https://pypi.org/simple")]
        assert list(state.iter_resolved_dependencies()) == [package_tuple]

    def test_expand_state_marker_false(self, resolver: Resolver) -> None:
        """Add a check for leaf dependency nodes for which environment markers apply and remove dependencies."""
        package_tuple = ("hexsticker", "1.0.0", "https://pypi.org/simple")
        state = State(score=1.0)
        state.add_unresolved_dependency(package_tuple)

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.project.runtime_environment.operating_system.name = "rhel"
        resolver.project.runtime_environment.operating_system.version = "8.1"
        resolver.project.runtime_environment.python_version = "3.6"

        resolver.graph.should_receive("get_depends_on").with_args(
            *package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
            extras=frozenset({None}),
            marker_evaluation_result=True,
            is_missing=False,
        ).and_return({}).once()

        resolver.project.runtime_environment.should_receive("is_fully_specified").and_return(True).once()

        resolver.context.register_package_tuple(
            package_tuple, develop=False, os_name=None, os_version=None, python_version=None,
        )

        assert resolver._expand_state(state, package_tuple) is state
        assert resolver.beam.size == 0

    def test_do_resolve_states_beam_empty(self, resolver: Resolver) -> None:
        """Resolve states until the beam is not empty."""
        resolver._init_context()
        resolver.beam.wipe()

        resolver.should_receive("_prepare_initial_state").with_args(with_devel=True).and_return(None).once()

        states = list(resolver._do_resolve_states(with_devel=True, user_stack_scoring=True))
        assert states == []
        assert resolver.context.iteration == 0
        assert resolver.context.accepted_final_states_count == 0
        assert resolver.context.discarded_final_states_count == 0
        assert resolver.beam.size == 0

    def test_resolve_products(self, resolver: Resolver) -> None:
        """Test resolving products."""
        # Check resolver adjusts count if it is more than limit.
        resolver.count = 5
        resolver.limit = 3

        resolver.predictor.should_call("pre_run").ordered()

        for unit in resolver.pipeline.iter_units():
            unit.should_receive("pre_run").with_args().and_return(None).once()

        final_state1 = State(score=0.33)
        product1 = flexmock()
        final_state2 = State(score=0.30)
        product2 = flexmock()

        resolver._init_context()

        resolver.should_receive("_do_resolve_states").with_args(with_devel=True, user_stack_scoring=True,).and_yield(
            final_state1, final_state2
        ).once()

        flexmock(Product)
        Product.should_receive("from_final_state").with_args(context=resolver.context, state=final_state1).and_return(
            product1
        ).ordered()

        Product.should_receive("from_final_state").with_args(context=resolver.context, state=final_state2).and_return(
            product2
        ).ordered()

        resolver.predictor.should_call("post_run").ordered()

        for unit in resolver.pipeline.iter_units():
            unit.should_receive("post_run").with_args().and_return(None)

        assert list(resolver.resolve_products(with_devel=True)) == [product1, product2]
        assert resolver.count == 3, "Count was not adjusted based on limit"
        assert resolver.limit == 3, "Limit was not left untouched"

    def test_resolve_products_eager_stop(self, resolver: Resolver) -> None:
        """Test resolving products with eager stopping."""
        final_state1 = State(score=0.3)
        product1 = flexmock()

        resolver._init_context()

        resolver.should_receive("_do_resolve_states").with_args(with_devel=True, user_stack_scoring=True).and_yield(
            final_state1
        ).and_raise(EagerStopPipeline).once()

        flexmock(Product)
        Product.should_receive("from_final_state").with_args(context=resolver.context, state=final_state1).and_return(
            product1
        ).ordered()

        # Expect each pipeline unit of a type.
        assert resolver.pipeline.boots
        assert resolver.pipeline.sieves
        assert resolver.pipeline.steps
        assert resolver.pipeline.strides
        assert resolver.pipeline.wraps
        resolver.predictor.should_call("post_run").ordered()
        for unit in resolver.pipeline.iter_units():
            unit.should_call("post_run").and_return(None).once()

        assert list(resolver.resolve_products(with_devel=True)) == [product1]

    def test_resolve_no_stack(self, resolver: Resolver) -> None:
        """Test report creation during resolution."""
        with pytest.raises(ValueError):
            assert resolver.context, "Context is already bound to resolver"

        resolver.should_receive("_do_resolve_products").with_args(with_devel=False, user_stack_scoring=True).and_return(
            []
        ).once()

        with pytest.raises(
            CannotProduceStack,
            match="Resolver did not find any stack that would satisfy "
            "requirements and stack characteristics given the time allocated",
        ):
            resolver.resolve(with_devel=False)

    def test_resolve(self, resolver: Resolver) -> None:
        """Test report creation during resolution."""
        product = flexmock(score=1.0)
        resolver.should_receive("_do_resolve_products").with_args(with_devel=True, user_stack_scoring=True).and_return(
            [product]
        ).once()
        resolver.pipeline.should_receive("call_post_run_report").once()
        resolver.predictor.should_receive("post_run_report").once()

        with pytest.raises(ValueError):
            assert resolver.context, "Context is already bound to resolver"

        report = resolver.resolve(with_devel=True)

        assert resolver.context is not None, "Context is not bound to resolver"
        assert report.product_count() == 1
        assert list(report.iter_products()) == [product]

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

    @pytest.mark.parametrize("limit,count", [(-1, 10), (10, -1), (-1, -1), (0, 10), (10, 0), (0, 0)])
    def test_positive_int_validator(
        self, pipeline_config: PipelineConfig, project: Project, predictor_mock: Predictor, limit: int, count: int,
    ) -> Resolver:
        """Check parameter validation for attributes that should be positive int."""
        with pytest.raises(ValueError):
            return Resolver(
                pipeline=pipeline_config,
                project=project,
                library_usage={},
                graph=GraphDatabase(),
                predictor=predictor_mock,
                recommendation_type=RecommendationType.LATEST,
                limit=limit,
                count=count,
                beam_width=Resolver.DEFAULT_BEAM_WIDTH,
                limit_latest_versions=Resolver.DEFAULT_LIMIT_LATEST_VERSIONS,
            )

    def test_no_direct_dependencies_error(self, resolver: Resolver) -> None:
        """Test raising an error if no direct dependencies were resolved."""
        resolver.should_receive("_resolve_direct_dependencies").with_args(with_devel=True).and_return({}).once()

        resolver._init_context()
        with pytest.raises(CannotProduceStack):
            resolver._prepare_initial_state(with_devel=True)

    def test_finalize_initial_state(self, resolver: Resolver, tf_package_versions: List[PackageVersion]) -> None:
        """Test finalization of an initial state objects."""
        initial_state_id_called = None

        def finalize_state(state_id: int) -> None:
            nonlocal initial_state_id_called
            initial_state_id_called = state_id

        resolver.should_receive("_resolve_direct_dependencies").with_args(with_devel=False).and_return(
            {"tensorflow": tf_package_versions}
        ).once()

        resolver.predictor.finalize_state = finalize_state

        resolver._init_context()
        resolver._prepare_initial_state(with_devel=False)
        assert resolver.beam.size == 1

        initial_state = resolver.beam.pop(0)

        assert resolver.beam.size == 0

        initial_state_id = id(initial_state)
        del initial_state
        gc.collect()

        assert initial_state_id_called == initial_state_id

    def test_finalize_state(self, resolver: Resolver, state: State) -> None:
        """Test finalization of a state objects."""
        state_id_called = None

        def finalize_state(state_id: int) -> None:
            nonlocal state_id_called
            state_id_called = state_id

        # Keep just one state - the one expanded, we do not care about initial state.
        resolver.beam.width = 1

        package_tuple = ("hexsticker", "1.0.0", "https://pypi.org/simple")
        state = State(score=1.0)
        state.add_unresolved_dependency(package_tuple)
        # To prevent from state allocation optimizations.
        state.add_unresolved_dependency(("hexsticker", "1.1.0", "https://pypi.org/simple"))
        state.add_unresolved_dependency(("selinon", "1.0.0", "https://pypi.org/simple"))

        resolver._init_context()
        resolver.context.iteration = 42
        resolver.predictor.finalize_state = finalize_state

        resolver.graph.should_receive("get_depends_on").with_args(
            *package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
            extras=frozenset({None}),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({"click": [("click", "1.0.0")]}).once()

        click_records = [
            {
                "package_name": "click",
                "package_version": "1.0.0",
                "index_url": "https://pypi.org/simple",
                "os_name": resolver.project.runtime_environment.operating_system.name,
                "os_version": resolver.project.runtime_environment.operating_system.version,
                "python_version": resolver.project.runtime_environment.python_version,
            }
        ]
        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="click",
            package_version="1.0.0",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(click_records).once()

        resolver.context.register_package_tuple(
            package_tuple, develop=False, os_name=None, os_version=None, python_version=None,
        )

        state_returned = resolver._expand_state(state, package_tuple)
        assert state_returned is not state
        assert resolver.beam.size == 1
        assert resolver.beam.pop(0) is state_returned
        assert resolver.beam.size == 0

        state_id = id(state_returned)
        del state_returned
        gc.collect()

        assert state_id_called == state_id

    @pytest.mark.parametrize(
        "score_returned, score_expected",
        [(Step.SCORE_MAX + 100.0, Step.SCORE_MAX), (Step.SCORE_MIN - 100.0, Step.SCORE_MIN),],
    )
    def test_step_boundaries(
        self, score_returned: float, score_expected: float, resolver: Resolver, package_version: PackageVersion,
    ) -> None:
        """Test adjusting return values of step units."""
        state = State()
        state.resolved_dependencies["hexsticker"] = (
            "hexsticker",
            "1.2.0",
            "https://pypi.org/simple",
        )

        flexmock(steps.Step1)
        steps.Step1.should_receive("run").with_args(state, package_version).and_return((score_returned, [])).once()

        resolver.pipeline.steps = [steps.Step1()]
        resolver.beam.should_receive("remove").with_args(state).once()

        resolver._init_context()
        with steps.Step1.assigned_context(resolver.context):
            resolver._run_steps(
                state, package_version, {"flask": ("flask", "1.0.0", "https://pypi.org/simple")},
            )

        state = resolver.beam.max()
        assert state.score == score_expected

    def test_maybe_score_user_lock_file_no_lock_file(self, resolver: Resolver) -> None:
        """Test scoring user stack lock file if no lock file is provided."""
        resolver._init_context()
        resolver.project.pipfile_lock = None

        assert resolver.context.project.pipfile_lock is None
        assert resolver.beam.size == 0

        resolver.should_receive("_prepare_user_lock_file").and_return(None).times(0)
        resolver._maybe_score_user_lock_file()

        assert resolver.beam.size == 0

    def test_maybe_score_user_lock_file_sieves_removal(self, resolver: Resolver) -> None:
        """Test scoring user stack lock file when sieves removed a package."""
        resolver._init_context()
        resolver.pipeline.sieves[0].should_receive("run").with_args(object).and_raise(NotAcceptable).once()
        assert resolver.beam.size == 0

        resolver.should_receive("_prepare_user_lock_file").and_return(None).once()
        resolver._maybe_score_user_lock_file()

        assert resolver.beam.size == 0

    def test_maybe_score_user_lock_file_steps_removal(self, resolver: Resolver) -> None:
        """Test scoring user stack lock file when steps discarded a state creation."""
        resolver._init_context()
        package_version = list(resolver.project.iter_dependencies_locked(with_devel=True))[0]
        resolver.pipeline.steps[0].should_receive("run").with_args(object, package_version).and_raise(
            NotAcceptable
        ).once()
        assert resolver.beam.size == 0

        resolver.should_receive("_prepare_user_lock_file").and_return(None).once()
        resolver._maybe_score_user_lock_file()

        assert resolver.beam.size == 0

    def test_maybe_score_user_lock_file(self, resolver: Resolver) -> None:
        """Test scoring user stack lock file when sieves removed a package."""
        resolver._init_context()

        resolver.should_receive("_prepare_user_lock_file").and_return(None).once()

        assert resolver.beam.size == 0
        resolver._maybe_score_user_lock_file()
        assert resolver.beam.size == 1

        state = resolver.beam.get(0)

        assert state.resolved_dependencies
        assert set(state.resolved_dependencies.values()) == set(
            d.to_tuple() for d in resolver.project.iter_dependencies_locked()
        ), "Not all dependencies captured in the state made out of the user's stack"

    def test_maybe_score_user_lock_file_error(self, resolver: Resolver) -> None:
        """Test scoring user stack lock file when sieves removed a package."""
        resolver._init_context()

        resolver.should_receive("_prepare_user_lock_file").and_raise(UserLockFileError).once()

        with pytest.raises(UserLockFileError):
            resolver._maybe_score_user_lock_file()

    def test_prepare_user_lock_file_index_not_enabled(self, resolver: Resolver) -> None:
        """Test preparing and validating user's lock file submitted if not enabled package index is used."""
        resolver._init_context()

        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://foo.bar/simple"), develop=False,
        )

        # We do not care about the linkage to not relevant Pipfile here.
        pipfile_lock = PipfileLock.from_package_versions(
            pipfile=resolver.project.pipfile, packages=[package_version], meta=resolver.project.pipfile.meta,
        )
        resolver.project.pipfile_lock = pipfile_lock
        resolver.project.pipfile_lock.meta.sources = {
            "foo": package_version.index,
            "another": Source("https://another.sk/simple"),
        }
        assert resolver.context.project.pipfile_lock is pipfile_lock

        resolver.graph.should_receive("get_python_package_index_urls_all").with_args(enabled=True).and_return(
            ["https://pypi.org/simple", "https://thoth-station.ninja/simple"]
        ).once()

        with pytest.raises(
            UserLockFileError, match=r"User's lock file uses one or more indexes that are not enabled: .*",
        ):
            resolver._prepare_user_lock_file()

    def test_prepare_user_lock_file_provenance_unknown(self, resolver: Resolver) -> None:
        """Test preparing and validating user's lock file submitted when provenance of a package is not known."""
        resolver._init_context()

        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=None, develop=False, hashes=["sha256:foo", "sha256:bar"],
        )

        thoth_station_source = Source("https://thoth-station.ninja/simple")
        pypi_source = Source("https://pypi.org/simple")

        # We do not care about the linkage to not relevant Pipfile here.
        pipfile_lock = PipfileLock.from_package_versions(
            pipfile=resolver.project.pipfile, packages=[package_version], meta=resolver.project.pipfile.meta,
        )
        resolver.project.pipfile_lock = pipfile_lock
        resolver.project.pipfile_lock.meta.sources = {
            "thoth-station": thoth_station_source,
            "pypi": pypi_source,
        }
        assert resolver.context.project.pipfile_lock is pipfile_lock

        resolver.graph.should_receive("get_python_package_index_urls_all").with_args(enabled=True).and_return(
            [pypi_source.url, thoth_station_source.url]
        ).once()

        resolver.graph.should_receive("get_python_package_hashes_sha256").with_args(
            package_version.name, package_version.locked_version, thoth_station_source.url,
        ).and_return(["unknown"]).once()

        resolver.graph.should_receive("get_python_package_hashes_sha256").with_args(
            package_version.name, package_version.locked_version, pypi_source.url
        ).and_return(["just-another-unknown", "foo-unknown"]).once()

        with pytest.raises(
            UserLockFileError, match="Could not determine provenance of package 'tensorflow' in version '2.0.0'",
        ):
            resolver._prepare_user_lock_file()

    def test_prepare_user_lock_file_one_source(self, resolver: Resolver) -> None:
        """Test preparing and validating user's lock file submitted if one Python package source index is used."""
        resolver._init_context()

        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=None, develop=False, hashes=["sha256:foo", "sha256:bar"],
        )

        thoth_station_source = Source("https://thoth-station.ninja/simple")

        # We do not care about the linkage to not relevant Pipfile here.
        pipfile_lock = PipfileLock.from_package_versions(
            pipfile=resolver.project.pipfile, packages=[package_version], meta=resolver.project.pipfile.meta,
        )
        resolver.project.pipfile_lock = pipfile_lock
        resolver.project.pipfile_lock.meta.sources = {
            "thoth-station": thoth_station_source,
        }
        assert resolver.context.project.pipfile_lock is pipfile_lock

        resolver.graph.should_receive("get_python_package_index_urls_all").with_args(enabled=True).and_return(
            [thoth_station_source.url]
        ).once()

        resolver.graph.should_receive("get_python_package_hashes_sha256").with_args(
            package_version.name, package_version.locked_version, thoth_station_source.url,
        ).and_return(["unknown"]).times(0)

        resolver._prepare_user_lock_file()
        assert package_version.index == thoth_station_source

    def test_prepare_user_lock_file_multiple_sources(self, resolver: Resolver) -> None:
        """Test preparing and validating user's lock file submitted when multiple Python package sources used."""
        resolver._init_context()

        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=None, develop=False, hashes=["sha256:foo", "sha256:bar"],
        )

        thoth_station_source = Source("https://thoth-station.ninja/simple")
        pypi_source = Source("https://pypi.org/simple")

        # We do not care about the linkage to not relevant Pipfile here.
        pipfile_lock = PipfileLock.from_package_versions(
            pipfile=resolver.project.pipfile, packages=[package_version], meta=resolver.project.pipfile.meta,
        )
        resolver.project.pipfile_lock = pipfile_lock
        resolver.project.pipfile_lock.meta.sources = {
            "thoth-station": thoth_station_source,
            "pypi": pypi_source,
        }
        assert resolver.context.project.pipfile_lock is pipfile_lock

        resolver.graph.should_receive("get_python_package_index_urls_all").with_args(enabled=True).and_return(
            [pypi_source.url, thoth_station_source.url]
        ).once()

        # We use sets so there is no counting on these two methods - their evaluation is hash dependent.
        resolver.graph.should_receive("get_python_package_hashes_sha256").with_args(
            package_version.name, package_version.locked_version, thoth_station_source.url,
        ).and_return(["foo"])
        resolver.graph.should_receive("get_python_package_hashes_sha256").with_args(
            package_version.name, package_version.locked_version, pypi_source.url
        ).and_return(["just-another-unknown", "foo-unknown"])

        resolver._prepare_user_lock_file()
        assert package_version.index == thoth_station_source

    def test_skip_package_exception(self, resolver: Resolver, tf_package_versions: List[PackageVersion]) -> None:
        """Test propagation of an exception caused to skip a package."""
        flexmock(sieves.Sieve1)
        flexmock(sieves.Sieve2)

        sieves.Sieve1.should_receive("run").with_args(object).and_yield(*tf_package_versions).once()
        sieves.Sieve2.should_receive("run").with_args(object).and_raise(SkipPackage).once()

        resolver.pipeline.sieves = [sieves.Sieve1(), sieves.Sieve2()]

        with pytest.raises(SkipPackage):
            list(resolver._run_sieves(tf_package_versions))

    def test_skip_package(self, resolver: Resolver, state: State) -> None:
        """Test raising a SkipPackage exception causes a dependency to be excluded."""
        flexmock(sieves.Sieve1)
        sieves.Sieve1.should_call("run").times(1)

        to_expand_package_tuple = ("tensorflow", "2.2.0", "https://pypi.org/simple")

        pypi = Source("https://pypi.org/simple")
        dep_package_versions = [
            PackageVersion(name="functools32", version="==3.2.3-1", index=pypi, develop=False),
            PackageVersion(name="functools32", version="==3.2.3-2", index=pypi, develop=False),
        ]

        functools323_1_records = [
            {
                "package_name": "functools32",
                "package_version": "3.2.3-1",
                "index_url": "https://pypi.org/simple",
                "os_name": resolver.project.runtime_environment.operating_system.name,
                "os_version": resolver.project.runtime_environment.operating_system.version,
                "python_version": resolver.project.runtime_environment.python_version,
            }
        ]

        functools323_2_records = [
            {
                "package_name": "functools32",
                "package_version": "3.2.3-2",
                "index_url": "https://pypi.org/simple",
                "os_name": resolver.project.runtime_environment.operating_system.name,
                "os_version": resolver.project.runtime_environment.operating_system.version,
                "python_version": resolver.project.runtime_environment.python_version,
            }
        ]

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="functools32",
            package_version="3.2.3-1",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(functools323_1_records).ordered()

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="functools32",
            package_version="3.2.3-2",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(functools323_2_records).ordered()

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset([None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({None: [(pv.name, pv.locked_version) for pv in dep_package_versions]}).once()

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            extras=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        )

        resolver.pipeline.sieves = [sieves.Sieve1(), _Functools32SkipPackageSieve()]
        state.unresolved_dependencies.clear()
        state.add_unresolved_dependency(to_expand_package_tuple)
        state_returned = resolver._expand_state(state, to_expand_package_tuple)
        # No more unresolved dependencies, the state is final.
        assert state_returned is state
        assert not state.unresolved_dependencies

    def test_skip_package_unresolved(self, resolver: Resolver, state: State) -> None:
        """Test raising a SkipPackage exception causes a dependency to be excluded."""
        flexmock(sieves.Sieve1)
        sieves.Sieve1.should_call("run").times(2)

        to_expand_package_tuple = ("tensorflow", "2.2.0", "https://pypi.org/simple")

        pypi = Source("https://pypi.org/simple")
        dep_package_versions = [
            PackageVersion(name="absl-py", version="==0.9.0", index=pypi, develop=False),
            PackageVersion(name="functools32", version="==3.2.3-2", index=pypi, develop=False),
        ]

        absl_py_records = [
            {
                "package_name": "absl-py",
                "package_version": "0.9.0",
                "index_url": "https://pypi.org/simple",
                "os_name": resolver.project.runtime_environment.operating_system.name,
                "os_version": resolver.project.runtime_environment.operating_system.version,
                "python_version": resolver.project.runtime_environment.python_version,
            }
        ]

        functools323_2_records = [
            {
                "package_name": "functools32",
                "package_version": "3.2.3-2",
                "index_url": "https://pypi.org/simple",
                "os_name": resolver.project.runtime_environment.operating_system.name,
                "os_version": resolver.project.runtime_environment.operating_system.version,
                "python_version": resolver.project.runtime_environment.python_version,
            }
        ]

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="absl-py",
            package_version="0.9.0",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(absl_py_records).ordered()

        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="functools32",
            package_version="3.2.3-2",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(functools323_2_records).ordered()

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset([None]),
            marker_evaluation_result=None,
            is_missing=False,
        ).and_return({None: [(pv.name, pv.locked_version) for pv in dep_package_versions]}).once()

        resolver._init_context()
        resolver.beam.add_state(state)
        resolver.context.register_package_tuple(
            to_expand_package_tuple,
            develop=False,
            extras=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        )

        resolver.pipeline.sieves = [sieves.Sieve1(), _Functools32SkipPackageSieve()]
        state.add_unresolved_dependency(to_expand_package_tuple)
        state_returned = resolver._expand_state(state, to_expand_package_tuple)
        assert state_returned is not None
        assert state_returned is not state
        assert "absl-py" in state_returned.unresolved_dependencies
        assert len(state_returned.unresolved_dependencies["absl-py"]) == 1
        assert "functools32" not in state_returned.unresolved_dependencies

    def test_skip_package_direct(self, resolver: Resolver, numpy_package_versions: List[PackageVersion],) -> None:
        """Test raising a SkipPackage exception causes a direct dependency to be excluded."""
        flexmock(sieves.Sieve1)
        sieves.Sieve1.should_call("run").times(2)

        pypi = Source("https://pypi.org/simple")
        functools32_package_versions = [
            PackageVersion(name="functools32", version="==3.2.3-2", index=pypi, develop=False),
            PackageVersion(name="functools32", version="==3.2.3-1", index=pypi, develop=False),
        ]

        resolver.should_receive("_resolve_direct_dependencies").with_args(with_devel=True).and_return(
            {"numpy": numpy_package_versions, "functools32": functools32_package_versions}
        ).once()

        flexmock(Beam)
        resolver.beam.should_receive("wipe").with_args().and_return(None).once()
        resolver._init_context()

        resolver.pipeline.sieves = [sieves.Sieve1(), _Functools32SkipPackageSieve()]

        assert resolver._prepare_initial_state(with_devel=True) is None
        assert resolver.beam.size == 1
        initial_state = resolver.beam.get(0)
        assert "functools32" not in initial_state.unresolved_dependencies
        assert "numpy" in initial_state.unresolved_dependencies
        assert len(initial_state.unresolved_dependencies["numpy"]) == len(numpy_package_versions)

    def test_skip_package_user_stack(self, resolver: Resolver) -> None:
        """Test skipping a package on the supplied user stack."""
        flexmock(sieves.Sieve1)
        sieves.Sieve1.should_call("run").times(2)
        resolver.pipeline.sieves = [sieves.Sieve1(), _Functools32SkipPackageSieve()]
        resolver.should_receive("_prepare_user_lock_file").with_args(with_devel=True).and_return(None).once()

        pypi = Source("https://pypi.org/simple")
        resolver.project = Project.from_package_versions(
            packages=[PackageVersion(name="tensorflow", version=">=2.0", index=pypi, develop=False),],
            packages_locked=[
                PackageVersion(name="functools32", version="==3.2.3-1", index=pypi, develop=False),
                PackageVersion(name="tensorflow", version="==2.2.0", index=pypi, develop=False),
            ],
        )

        assert "functools32" not in (pv.name for pv in resolver.project.iter_dependencies(with_devel=True))
        assert "functools32" in (pv.name for pv in resolver.project.iter_dependencies_locked(with_devel=True))

        resolver._init_context()
        user_stack_state = resolver._maybe_score_user_lock_file()

        assert not user_stack_state.unresolved_dependencies
        assert "tensorflow" in user_stack_state.resolved_dependencies
        assert "functools32" not in user_stack_state.resolved_dependencies

        assert "functools32" not in (pv.name for pv in resolver.project.iter_dependencies(with_devel=True))
        assert "functools32" not in (pv.name for pv in resolver.project.iter_dependencies_locked(with_devel=True))

        assert "tensorflow" in (pv.name for pv in resolver.project.iter_dependencies(with_devel=False))
        assert "tensorflow" in (pv.name for pv in resolver.project.iter_dependencies_locked(with_devel=False))

    def test_skip_package_user_stack_direct(self, resolver: Resolver) -> None:
        """Test skipping a package on the supplied user stack, the package is a direct dependency."""
        flexmock(sieves.Sieve1)
        sieves.Sieve1.should_call("run").times(2)
        resolver.pipeline.sieves = [sieves.Sieve1(), _Functools32SkipPackageSieve()]
        resolver.should_receive("_prepare_user_lock_file").with_args(with_devel=True).and_return(None).once()

        pypi = Source("https://pypi.org/simple")
        resolver.project = Project.from_package_versions(
            packages=[
                PackageVersion(name="thoth-glyph", version="*", index=pypi, develop=False),
                PackageVersion(name="functools32", version="==3.2.3-1", index=pypi, develop=False),
            ],
            packages_locked=[
                PackageVersion(name="thoth-glyph", version="==0.1.1", index=pypi, develop=False),
                PackageVersion(name="functools32", version="==3.2.3-1", index=pypi, develop=False),
            ],
        )

        assert "functools32" in (pv.name for pv in resolver.project.iter_dependencies(with_devel=True))
        assert "functools32" in (pv.name for pv in resolver.project.iter_dependencies_locked(with_devel=True))

        resolver._init_context()

        user_stack_state = resolver._maybe_score_user_lock_file()

        assert not user_stack_state.unresolved_dependencies

        assert "thoth-glyph" in user_stack_state.resolved_dependencies
        assert "functools32" not in user_stack_state.resolved_dependencies

        assert "functools32" not in (pv.name for pv in resolver.project.iter_dependencies(with_devel=True))
        assert "functools32" not in (pv.name for pv in resolver.project.iter_dependencies_locked(with_devel=True))

        assert "thoth-glyph" in (pv.name for pv in resolver.project.iter_dependencies(with_devel=False))
        assert "thoth-glyph" in (pv.name for pv in resolver.project.iter_dependencies_locked(with_devel=False))
