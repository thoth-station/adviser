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

from collections import OrderedDict
from copy import deepcopy
import itertools
from typing import List
import random

from thoth.adviser.context import Context
from thoth.adviser.beam import Beam
from thoth.adviser.resolver import Resolver
from thoth.adviser.state import State
from thoth.adviser.predictor import Predictor
from thoth.adviser.product import Product
from thoth.adviser.pipeline_config import PipelineConfig
from thoth.adviser.pipeline_builder import PipelineBuilder
from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import DecisionType
from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.python import Project
from thoth.storages import GraphDatabase
from thoth.storages.exceptions import NotFoundError

from thoth.adviser.exceptions import BootError
from thoth.adviser.exceptions import CannotProduceStack
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.exceptions import SieveError
from thoth.adviser.exceptions import StepError
from thoth.adviser.exceptions import StrideError
from thoth.adviser.exceptions import UnresolvedDependencies
from thoth.adviser.exceptions import WrapError
from thoth.adviser.exceptions import EagerStopPipeline
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
    return PackageVersion(
        name="tensorflow",
        version="==2.0.0",
        index=Source("https://pypi.org/simple"),
        develop=False,
    )


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
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://thoth-station.ninja/simple"),
            develop=False,
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

        # We use object here as flexmock has no direct support for generator args. Tests
        # for generator args are done in sieve related testsuite.
        sieves.Sieve1.should_receive("run").with_args(object).and_yield(
            *tf_package_versions
        ).once()
        sieves.Sieve2.should_receive("run").with_args(object).and_yield(
            *tf_package_versions
        ).once()

        resolver.pipeline.sieves = [sieves.Sieve1(), sieves.Sieve2()]

        assert list(resolver._run_sieves(tf_package_versions)) == tf_package_versions

    def test_run_sieves_error(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test raising sieve specific error by resolver if any error occurs."""
        flexmock(sieves.Sieve1)

        sieves.Sieve1.should_receive("run").with_args(object).and_raise(
            ValueError
        ).once()
        resolver.pipeline.sieves = [sieves.Sieve1()]

        with pytest.raises(SieveError):
            list(resolver._run_sieves(tf_package_versions))

    def test_run_sieves_not_acceptable(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test raising not acceptable causes filtering of packages."""
        flexmock(sieves.Sieve1)

        sieves.Sieve1.should_receive("run").with_args(object).and_raise(
            NotAcceptable
        ).once()

        resolver.pipeline.sieves = [sieves.Sieve1()]

        assert list(resolver._run_sieves(tf_package_versions)) == []

    def test_run_steps_not_acceptable(
            self, resolver: Resolver, package_version: PackageVersion
    ) -> None:
        """Test running steps when not acceptable is raised."""
        state1 = State()
        state1.score = 0.1
        state1.add_justification([{"hello": "thoth"}])
        state1.add_resolved_dependency(("hexsticker", "1.2.0", "https://pypi.org/simple"))

        flexmock(steps.Step1)
        flexmock(steps.Step2)

        steps.Step1.should_receive("run").with_args(
            state1, package_version
        ).and_return((1.0, [{"baz": "bar"}])).ordered()

        steps.Step2.should_receive("run").with_args(
            state1, package_version
        ).and_raise(NotAcceptable).ordered()

        resolver.pipeline.steps = [steps.Step1(), steps.Step2()]

        resolver._init_context()
        assert resolver.beam.size == 0
        assert (
                resolver._run_steps(state1, package_version, {"numpy": [("numpy", "1.18.0")]})
                is None
        )
        assert resolver.beam.size == 0

    def test_run_steps_step_error(self, resolver: Resolver, package_version: PackageVersion) -> None:
        """Test raising a step error when a step raises an unexpected error."""
        state = State()
        state.score = 0.1
        state.add_justification([{"hello": "thoth"}])
        state.add_unresolved_dependency(("hexsticker", "1.2.0", "https://pypi.org/simple"))

        original_state = deepcopy(state)

        flexmock(steps.Step1)
        steps.Step1.should_receive("run").with_args(
            state, package_version
        ).and_raise(NameError).once()

        resolver.pipeline.steps = [steps.Step1()]

        with pytest.raises(StepError):
            assert resolver._run_steps(
                state,
                package_version,
                {"flask": [("flask", "0.12", "https://pypi.org/simple")]},
            )

        assert original_state == state, "State is not untouched"

    def test_run_steps_error(
        self, resolver: Resolver, package_version: PackageVersion
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
            state, package_version
        ).and_raise(NameError).once()

        resolver.pipeline.steps = [steps.Step1()]

        with pytest.raises(StepError):
            assert resolver._run_steps(
                state,
                package_version,
                {"flask": ("flask", "1.0.0", "https://pypi.org/simple")}
            ) is None

        assert original_state == state, "State is not untouched"

    @pytest.mark.parametrize("score", [float("inf"), float("nan")])
    def test_run_steps_inf_nan(
        self,
        score: float,
        resolver: Resolver,
        package_version: PackageVersion,
    ):
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
            state, package_version
        ).and_return((score, [{"foo": "bar"}])).once()

        resolver.pipeline.steps = [steps.Step1()]

        with pytest.raises(StepError):
            assert resolver._run_steps(
                state,
                package_version,
                {"flask": ("flask", "1.0.0", "https://pypi.org/simple")}
            ) is None

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
        ).and_return({}).once()

        resolver._solver = solver_mock
        with pytest.raises(
            UnresolvedDependencies, match="Unable to resolve all direct dependencies"
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
        ).and_return({"tensorflow": tf_package_versions, "flask": []}).once()

        resolver._solver = solver_mock
        with pytest.raises(
            UnresolvedDependencies, match="Unable to resolve all direct dependencies"
        ) as exc:
            resolver._resolve_direct_dependencies(with_devel=True)

        assert exc.value.unresolved == ["flask"]

    def test_resolve_direct_dependencies(
        self, resolver: Resolver, tf_package_versions: List[PackageVersion]
    ) -> None:
        """Test resolving multiple direct dependencies."""
        resolved = {
            "tensorflow": tf_package_versions,
            "flask": [
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

        resolver.should_receive("_resolve_direct_dependencies").with_args(
            with_devel=False
        ).and_return(
            {
                "tensorflow": tf_package_versions_shuffled,
                "flask": flask_package_versions_shuffled,
            }
        ).once()

        resolver.should_receive("_run_sieves").with_args(
            tf_package_versions
        ).and_return(tf_package_versions).ordered()

        resolver.should_receive("_run_sieves").with_args(
            flask_package_versions
        ).and_return(flask_package_versions).ordered()

        resolver._init_context()
        resolver._prepare_initial_state(with_devel=False)
        assert resolver.beam.size == 1

        state = resolver.beam.top()
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
        resolver.should_receive("_resolve_direct_dependencies").with_args(
            with_devel=True
        ).and_return(
            {"numpy": numpy_package_versions, "tensorflow": tf_package_versions}
        ).once()

        # This is dependent on dict order, Python 3.6+ required.
        resolver.should_receive("_run_sieves").with_args(object).and_yield(
            *numpy_package_versions
        ).ordered()
        resolver.should_receive("_run_sieves").with_args(object).and_yield(
            *[]
        ).ordered()

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
        resolver.should_receive("_resolve_direct_dependencies").with_args(
            with_devel=True
        ).and_return(
            {"numpy": numpy_package_versions, "tensorflow": tf_package_versions}
        ).once()

        # This is dependent on dict order, Python 3.6+ required.
        resolver.should_receive("_run_sieves").with_args(object).and_yield(
            *numpy_package_versions
        ).ordered()
        resolver.should_receive("_run_sieves").with_args(object).and_yield(
            *tf_package_versions
        ).ordered()

        flexmock(Beam)
        resolver.beam.should_receive("wipe").with_args().and_return(None).once()
        resolver._init_context()
        assert resolver._prepare_initial_state(with_devel=True) is None

        for package_version in itertools.chain(
            numpy_package_versions, tf_package_versions
        ):
            assert (
                resolver.context.get_package_version(package_version.to_tuple())
                is package_version
            ), "Not all packages registered in resolver context"

        assert resolver.beam.size == 1

        state = resolver.beam.top()
        unresolved_dependencies = set(state.iter_unresolved_dependencies())
        assert unresolved_dependencies == (
                {pv.to_tuple() for pv in numpy_package_versions} | {pv.to_tuple() for pv in tf_package_versions}
        )
        assert list(state.iter_resolved_dependencies()) == []

    def test_expand_state_not_found(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state when a package was not found."""
        to_expand_package_tuple = state.get_random_unresolved_dependency()

        resolver._init_context()
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
        ).and_raise(NotFoundError).once()
        assert resolver._expand_state(state, to_expand_package_tuple) is None
        assert resolver.beam.size == 0

    def test_expand_state_no_dependencies_final(
        self, resolver: Resolver, state: State
    ) -> None:
        """Test expanding a state when the given package has no dependencies producing final state."""
        to_expand_package_tuple = state.get_random_unresolved_dependency()

        resolver._init_context()
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
        ).and_return([]).once()

        assert (
            len(state.unresolved_dependencies) == 1
        ), "State in the test case should have only once dependency to resolve in order to check production of a final state"

        original_resolved_count = len(state.resolved_dependencies)

        assert (
            resolver._expand_state(state, to_expand_package_tuple) is state
        ), "State returned is not the one passed"

        assert to_expand_package_tuple in state.iter_resolved_dependencies()
        assert to_expand_package_tuple not in state.iter_unresolved_dependencies()
        assert resolver.beam.size == 0, "Some adjustments to beam were made"
        assert len(state.resolved_dependencies) == original_resolved_count + 1

    def test_expand_state_no_dependencies_not_final(
        self, resolver: Resolver, state: State
    ) -> None:
        """Test expanding a state when the given package has no dependencies producing not final state."""
        to_expand_package_tuple = state.get_random_unresolved_dependency()

        # Add one more making sure there will be still some unresolved dependencies.
        assert (
            "flask" not in state.unresolved_dependencies
        ), "State cannot have package flask in unresolved for this test case"
        state.add_unresolved_dependency(("flask", "0.12", "https://pypi.org/simple"))

        resolver._init_context()
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
        ).and_return([]).once()

        original_resolved_count = len(state.resolved_dependencies)

        returned_value = resolver._expand_state(state, to_expand_package_tuple)

        assert returned_value is None, "No state should be returned"
        assert to_expand_package_tuple in state.iter_resolved_dependencies()
        assert (
            len(state.resolved_dependencies) == original_resolved_count + 1
        ), "State returned has no adjusted resolved dependencies"
        assert (
            "flask" in state.unresolved_dependencies
        ), "State returned has no adjusted resolved dependencies"
        assert resolver.beam.size == 1, "State not present in beam"
        assert resolver.beam.top() is state, "State in the beam is not the one passed"

    def test_expand_state_add_dependencies_call(
        self, resolver: Resolver, state: State
    ) -> None:
        """Test expanding a state which results in a call for adding new dependencies."""
        to_expand_package_tuple = ("tensorflow", "2.0.0", "https://pypi.org/simple")

        pypi = Source("https://pypi.org/simple")
        dep_package_versions = [
            PackageVersion(
                name="absl-py", version="==0.8.1", index=pypi, develop=False
            ),
            PackageVersion(
                name="absl-py", version="==0.8.2", index=pypi, develop=False
            ),
            PackageVersion(
                name="tensorboard", version="==2.0.0", index=pypi, develop=False
            ),
            PackageVersion(
                name="tensorboard", version="==2.0.1", index=pypi, develop=False
            ),
        ]

        resolver.graph.should_receive("get_depends_on").with_args(
            *to_expand_package_tuple,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.operating_system.version,
            extras=frozenset([None]),
            marker_evaluation_result=None,
        ).and_return(
            {None: [(pv.name, pv.locked_version) for pv in dep_package_versions]}
        ).once()

        resolver._init_context()
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
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://pypi.org.simple"),
            extras=None,
            develop=False,
        )

        resolver.project.runtime_environment.should_receive(
            "is_fully_specified"
        ).with_args().and_return(False)

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
        resolver.context.register_package_version(package_version)
        resolver._expand_state_add_dependencies(
            state=state,
            package_version=package_version,
            dependencies=[("absl-py", "0.8.1"), ("tensorboard", "2.0.0")],
        )

        assert (
            resolver.beam.size == 0
        ), "A new state was added even the dependency sub-graph is not resolved"

    def test_resolve_boot_error(self, resolver: Resolver):
        """Test raising an exception in boots causes halt of resolver."""
        assert (
            resolver.pipeline.boots
        ), "No boots in the pipeline configuration to run test with"

        resolver.pipeline.boots[0].should_receive("run").and_raise(ValueError).once()
        with pytest.raises(BootError):
            resolver.resolve(with_devel=False)

    @pytest.mark.parametrize(
        "unit_type", ["boots", "sieves", "steps", "strides", "wraps"]
    )
    def test_resolve_pre_run_error(self, unit_type: str, resolver: Resolver):
        """Test raising an exception in pre-run phase causes halt of resolver."""
        units = getattr(resolver.pipeline, unit_type)
        assert units, "No unit in the pipeline configuration to run test with"

        unit = units[0]
        unit.should_receive("pre_run").and_raise(ValueError).once()
        with pytest.raises(PipelineUnitError):
            resolver.resolve(with_devel=False)

    def test_do_resolve_states_limit_reached(
        self, resolver: Resolver, final_state: State
    ) -> None:
        """Resolve states until the limit of generated states is reached."""
        assert (
            resolver.pipeline.boots
        ), "No boots in the pipeline configuration to run test with"
        assert (
            resolver.pipeline.strides
        ), "No strides in the pipeline configuration to run test with"
        assert (
            resolver.pipeline.wraps
        ), "No strides in the pipeline configuration to run test with"

        state1 = State(score=0.0)
        state1.add_unresolved_dependency(("thoth-pipenv", "2018.12.17", "https://pypi.org/simple"))
        state2 = State(score=1.0)
        state2.add_unresolved_dependency(("selinon", "1.0.0", "https://pypi.org/simple"))
        state3 = State(score=2.0)
        state2.add_unresolved_dependency(("hexsticker", "1.0.0", "https://pypi.org/simple"))

        flexmock(Beam)
        resolver.beam.should_receive("new_iteration").and_return(None).twice()
        resolver.beam.add_state(state1)
        resolver.beam.add_state(state2)
        resolver.beam.add_state(state3)

        resolver.limit = 1
        resolver._init_context()

        for boot in resolver.pipeline.boots:
            boot.should_receive("run").with_args().and_return(None).once()

        for stride in resolver.pipeline.strides:
            stride.should_receive("run").with_args(final_state).and_return(None).once()

        for wrap in resolver.pipeline.wraps:
            wrap.should_receive("run").with_args(final_state).and_return(None).once()

        resolver.should_receive("_prepare_initial_state").with_args(
            with_devel=True
        ).and_return(resolver.beam).once()

        to_expand_package_tuple2 = state2.get_random_unresolved_dependency()
        to_expand_package_tuple1 = state1.get_random_unresolved_dependency()
        resolver.predictor.should_receive("run").with_args(
            resolver.context
        ).and_return(state2, to_expand_package_tuple2).and_return(state1, to_expand_package_tuple1).twice()

        resolver.should_receive("_expand_state").with_args(state2, to_expand_package_tuple2).and_return(
            None
        ).once()

        resolver.should_receive("_expand_state").with_args(state1, to_expand_package_tuple1).and_return(
            final_state
        ).once()

        states = list(resolver._do_resolve_states(with_devel=True))
        assert states == [final_state]
        assert resolver.context.iteration == 2
        assert resolver.context.accepted_final_states_count == 1
        assert resolver.context.discarded_final_states_count == 0
        assert resolver.beam.size == 1
        assert resolver.beam.top() is state3

    def test_expand_state_marker_true(
        self, resolver: Resolver
    ) -> None:
        """Add a check for leaf dependency nodes for which environment markers apply and remove dependencies."""
        package_tuple = ("hexsticker", "1.0.0", "https://pypi.org/simple")
        state = State(score=1.0)
        state.add_unresolved_dependency(package_tuple)

        resolver._init_context()
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
        ).and_return({"enum34": [("enum34", "1.1.6")]}).once()

        enum34_records = [
            {
                "package_name": "enum34",
                "package_version": "1.1.6",
                "index_url": "https://pypi.org/simple",
                "os_name": resolver.project.runtime_environment.operating_system.name,
                "os_version": resolver.project.runtime_environment.operating_system.version,
                "python_version": resolver.project.runtime_environment.python_version,
            },
        ]
        resolver.graph.should_receive("get_python_package_version_records").with_args(
            package_name="enum34",
            package_version="1.1.6",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(enum34_records).once()

        resolver.project.runtime_environment.should_receive(
            "is_fully_specified"
        ).and_return(True).once()

        resolver.context.register_package_tuple(
            package_tuple,
            develop=False,
            os_name=None,
            os_version=None,
            python_version=None,
        )

        assert resolver._expand_state(state, package_tuple) is None
        assert resolver.beam.size == 1

        state = resolver.beam.top()

        assert list(state.iter_unresolved_dependencies()) == [("enum34", "1.1.6", "https://pypi.org/simple")]
        assert list(state.iter_resolved_dependencies()) == [package_tuple]

    def test_expand_state_marker_false(
        self, resolver: Resolver
    ) -> None:
        """Add a check for leaf dependency nodes for which environment markers apply and remove dependencies."""
        package_tuple = ("hexsticker", "1.0.0", "https://pypi.org/simple")
        state = State(score=1.0)
        state.add_unresolved_dependency(package_tuple)

        resolver._init_context()
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
        ).and_return([]).once()

        resolver.project.runtime_environment.should_receive(
            "is_fully_specified"
        ).and_return(True).once()

        resolver.context.register_package_tuple(
            package_tuple,
            develop=False,
            os_name=None,
            os_version=None,
            python_version=None,
        )

        assert resolver._expand_state(state, package_tuple) is state
        assert resolver.beam.size == 0

    def test_do_resolve_states_beam_empty(
        self, resolver: Resolver, final_state: State
    ) -> None:
        """Resolve states until the beam is not empty."""
        assert (
            resolver.pipeline.boots
        ), "No boots in the pipeline configuration to run test with"
        assert (
            len(resolver.pipeline.strides) == 1
        ), "Wrong number of strides in the pipeline configuration for this test case"
        assert (
            resolver.pipeline.wraps
        ), "No strides in the pipeline configuration to run test with"

        state1 = State(score=0.0)
        state1.add_unresolved_dependency(("flask", "1.0.0", "https://pypi.org/simple"))

        state2 = State(score=1.0)
        state2.add_unresolved_dependency(("flask", "1.1.0", "https://pypi.org/simple"))

        state3 = State(score=2.0)
        state3.add_unresolved_dependency(("flask", "1.2.0", "https://pypi.org/simple"))

        resolver.beam.add_state(state1)
        resolver.beam.add_state(state2)
        resolver.beam.add_state(state3)

        resolver._init_context()

        resolver.should_receive("_prepare_initial_state").with_args(
            with_devel=True
        ).and_return(None).once()

        unresolved_dependency1 = state1.get_random_unresolved_dependency()
        unresolved_dependency2 = state2.get_random_unresolved_dependency()
        unresolved_dependency3 = state3.get_random_unresolved_dependency()

        resolver.predictor.should_receive("run").with_args(object)\
            .and_return(state1, unresolved_dependency1)\
            .and_return(state2, unresolved_dependency2)\
            .and_return(state3, unresolved_dependency3).times(3)

        resolver.should_receive("_expand_state").with_args(state3, unresolved_dependency3).and_return(
            final_state
        ).once()

        resolver.should_receive("_expand_state").with_args(state1, unresolved_dependency1).and_return(
            final_state
        ).once()

        resolver.should_receive("_expand_state").with_args(state2, unresolved_dependency2).and_return(
            final_state
        ).once()

        for boot in resolver.pipeline.boots:
            boot.should_receive("run").with_args().and_return(None).once()

        resolver.pipeline.strides[0].should_receive("run").with_args(
            final_state
        ).and_return(None).and_raise(NotAcceptable).and_return(None).times(3)

        for wrap in resolver.pipeline.wraps:
            wrap.should_receive("run").with_args(final_state).and_return(None).times(2)

        states = list(resolver._do_resolve_states(with_devel=True))
        assert states == [final_state, final_state]
        assert resolver.context.iteration == 3
        assert resolver.context.accepted_final_states_count == 2
        assert resolver.context.discarded_final_states_count == 1
        assert resolver.beam.size == 0

    def test_resolve_products(self, resolver: Resolver) -> None:
        """Test resolving products."""
        # Check resolver adjusts count if it is more than limit.
        resolver.count = 5
        resolver.limit = 3

        resolver.project.runtime_environment.should_receive(
            "is_fully_specified"
        ).with_args().and_return(False).ordered()

        resolver.predictor.should_call("pre_run").ordered()

        for unit in resolver.pipeline.iter_units():
            unit.should_receive("pre_run").with_args().and_return(None).once()

        final_state1 = State(score=0.33)
        product1 = flexmock()
        final_state2 = State(score=0.30)
        product2 = flexmock()

        resolver._init_context()

        resolver.should_receive("_do_resolve_states").with_args(
            with_devel=True
        ).and_yield(final_state1, final_state2).once()

        flexmock(Product)
        Product.should_receive("from_final_state").with_args(
            context=resolver.context, state=final_state1
        ).and_return(product1).ordered()

        Product.should_receive("from_final_state").with_args(
            context=resolver.context, state=final_state2
        ).and_return(product2).ordered()

        resolver.predictor.should_call("post_run").ordered()

        for unit in resolver.pipeline.iter_units():
            unit.should_receive("post_run").with_args().and_return(None)

        assert list(resolver.resolve_products(with_devel=True)) == [product1, product2]
        assert resolver.count == 3, "Count was not adjusted based on limit"
        assert resolver.limit == 3, "Limit was not left untouched"

    def test_resolve_products_eager_stop(self, resolver: Resolver) -> None:
        """Test resolving products with eager stopping."""
        resolver.project.runtime_environment.should_receive(
            "is_fully_specified"
        ).with_args().and_return(True).ordered()

        final_state1 = State(score=0.3)
        product1 = flexmock()

        resolver._init_context()

        resolver.should_receive("_do_resolve_states").with_args(
            with_devel=True
        ).and_yield(final_state1).and_raise(EagerStopPipeline).once()

        flexmock(Product)
        Product.should_receive("from_final_state").with_args(
            context=resolver.context, state=final_state1
        ).and_return(product1).ordered()

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

        resolver.should_receive("_do_resolve_products").with_args(
            with_devel=False
        ).and_return([]).once()

        with pytest.raises(CannotProduceStack, match="No stack was produced"):
            resolver.resolve(with_devel=False)

    def test_resolve(self, resolver: Resolver) -> None:
        """Test report creation during resolution."""
        product = flexmock(score=1.0)
        resolver.should_receive("_do_resolve_products").with_args(
            with_devel=True
        ).and_return([product]).once()
        resolver.pipeline.should_receive("call_post_run_report").once()
        resolver.predictor.should_receive("post_run_report").once()

        stack_info = [{"foo": "bar"}]

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
        PipelineBuilder.should_receive(
            "get_dependency_monkey_pipeline_config"
        ).with_args(
            decision_type=kwargs["decision_type"],
            project=kwargs["project"],
            library_usage=kwargs["library_usage"],
            graph=graph_mock,
        ).and_return(
            pipeline
        ).once()

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

    @pytest.mark.parametrize(
        "limit,count", [(-1, 10), (10, -1), (-1, -1), (0, 10), (10, 0), (0, 0)]
    )
    def test_positive_int_validator(
        self,
        pipeline_config: PipelineConfig,
        project: Project,
        predictor_mock: Predictor,
        limit: int,
        count: int,
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
