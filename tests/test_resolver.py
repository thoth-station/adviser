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

import pytest
import flexmock

from collections import OrderedDict
from copy import deepcopy
import itertools
from typing import List
from typing import Tuple
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
    return State(
        score=0.5,
        unresolved_dependencies=OrderedDict(
            (("tensorflow", ("tensorflow", "2.0.0", "https://pypi.org/simple")),)
        ),
        resolved_dependencies=OrderedDict(
            (("numpy", ("numpy", "1.17.4", "https://pypi.org/simple")),)
        ),
        advised_runtime_environment=RuntimeEnvironment.from_dict({}),
    )


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

    def test_run_steps(
        self, resolver: Resolver, package_versions: List[PackageVersion]
    ) -> None:
        """Test running pipeline steps."""
        state1 = State()
        state1.score = 0.1
        state1.add_justification([{"hello": "thoth"}])
        state1.resolved_dependencies["hexsticker"] = (
            "hexsticker",
            "1.2.0",
            "https://pypi.org/simple",
        )

        flexmock(steps.Step1)
        flexmock(steps.Step2)

        steps.Step1.should_receive("run").with_args(
            state1, package_versions[0]
        ).and_return((1.0, None)).ordered()

        steps.Step2.should_receive("run").with_args(
            state1, package_versions[0]
        ).and_return((0.5, [{"foo": 1}])).ordered()

        state2 = state1.clone()
        state2.score += 1.0 + 0.5
        state2.add_unresolved_dependency(package_versions[0].to_tuple())
        state2.add_justification([{"foo": 1}])

        steps.Step1.should_receive("run").with_args(
            state2, package_versions[1]
        ).and_return((None, None)).ordered()

        steps.Step2.should_receive("run").with_args(
            state2, package_versions[1]
        ).and_return(None).ordered()

        state3 = state2.clone()
        state3.add_unresolved_dependency(package_versions[1].to_tuple())

        steps.Step1.should_receive("run").with_args(
            state3, package_versions[2]
        ).and_return((None, [{"baz": "bar"}])).ordered()
        steps.Step2.should_receive("run").with_args(
            state3, package_versions[2]
        ).and_return(None).ordered()

        beam_state = state3.clone()
        beam_state.add_unresolved_dependency(package_versions[2].to_tuple())
        beam_state.add_justification([{"baz": "bar"}])

        resolver.pipeline.steps = [steps.Step1(), steps.Step2()]

        resolver._init_context()
        assert resolver.beam.size == 0
        assert (
            resolver._run_steps(state1, {pv.name: [pv] for pv in package_versions})
            is None
        )
        assert resolver.beam.size == 1
        assert resolver.beam.top() == beam_state

    def test_run_steps_not_acceptable(
        self, resolver: Resolver, package_versions: List[PackageVersion]
    ) -> None:
        """Test running steps when not acceptable is raised."""
        state1 = State()
        state1.score = 0.1
        state1.add_justification([{"hello": "thoth"}])
        state1.resolved_dependencies["hexsticker"] = (
            "hexsticker",
            "1.2.0",
            "https://pypi.org/simple",
        )

        flexmock(steps.Step1)
        flexmock(steps.Step2)

        steps.Step1.should_receive("run").with_args(
            state1, package_versions[0]
        ).and_return((1.0, [{"baz": "bar"}])).ordered()

        steps.Step2.should_receive("run").with_args(
            state1, package_versions[0]
        ).and_raise(NotAcceptable).ordered()

        resolver.pipeline.steps = [steps.Step1(), steps.Step2()]

        assert resolver.beam.size == 0
        assert (
            resolver._run_steps(state1, {pv.name: [pv] for pv in package_versions[:3]})
            is None
        )
        assert resolver.beam.size == 0

    @pytest.mark.parametrize(
        "package_tuple",
        [
            # Any of version or index url is different.
            ("tensorflow", "1.9.0", "https://pypi.org/simple"),
            ("tensorflow", "2.0.0", "https://thoth-station.ninja"),
            ("tensorflow", "1.9.0", "https://thoth-station.ninja"),
        ],
    )
    def test_run_steps_package_clash(
        self, package_tuple: Tuple[str, str, str], resolver: Resolver
    ) -> None:
        """Test running steps with a dependency clash."""
        pypi = Source("https://pypi.org/simple")

        package_version1 = PackageVersion(
            name="tensorflow", version="==2.0.0", index=pypi, develop=False
        )
        package_version2 = PackageVersion(
            name="numpy", version="==1.1.1", index=pypi, develop=False
        )

        state = State(
            score=1.0,
            unresolved_dependencies=OrderedDict(
                [("flask", ("flask", "1.12.0", "https://pypi.org/simple"))]
            ),
            resolved_dependencies=OrderedDict([(package_tuple[0], package_tuple)]),
        )

        assert resolver.beam.size == 0
        assert (
            resolver._run_steps(
                state,
                {
                    package_version1.name: [package_version1],
                    package_version2.name: [package_version2],
                },
            )
            is None
        )
        assert resolver.beam.size == 0

    def test_run_steps_no_package_clash(self, resolver: Resolver) -> None:
        """Test running steps without any dependency clash."""
        pypi = Source("https://pypi.org/simple")

        package_version1 = PackageVersion(
            name="tensorflow", version="==2.0.0", index=pypi, develop=False
        )
        package_version2 = PackageVersion(
            name="numpy", version="==1.1.1", index=pypi, develop=False
        )

        state = State(
            score=1.0,
            unresolved_dependencies=OrderedDict(
                [("flask", ("flask", "1.12.0", "https://pypi.org/simple"))]
            ),
            resolved_dependencies=OrderedDict(
                [(package_version1.name, package_version1.to_tuple())]
            ),
        )

        assert (
            len(resolver.pipeline.steps) == 1
        ), "A pre-requisite for this test case is to have exactly one step in the pipeline configuration"
        assert (
            resolver.pipeline.steps[0].MULTI_PACKAGE_RESOLUTIONS is False
        ), "This test expect multi package resolution in pipeline step turned off"

        # Should be called only once with package_version2, no package_version1 call as
        # MULTI_PACKAGE_RESOLUTIONS is off.
        resolver.pipeline.steps[0].should_receive("run").with_args(
            state, package_version2
        ).and_return(None).once()

        resolver.should_receive("_report_shared_dependency").with_args(
            package_version1.to_tuple()
        ).and_return(None).once()

        assert resolver.beam.size == 0
        resolver._init_context()
        assert (
            resolver._run_steps(
                state,
                {
                    package_version1.name: [package_version1],
                    package_version2.name: [package_version2],
                },
            )
            is None
        )
        assert resolver.beam.size == 1
        assert resolver.beam.top().to_dict() == {
            "advised_runtime_environment": None,
            "iteration": 0,
            "iteration_states_added": 0,
            "latest_version_offset": 0,
            "justification": [],
            "resolved_dependencies": OrderedDict(
                [("tensorflow", ("tensorflow", "2.0.0", "https://pypi.org/simple"))]
            ),
            "score": 1.0,
            "unresolved_dependencies": OrderedDict(
                [
                    ("flask", ("flask", "1.12.0", "https://pypi.org/simple")),
                    ("numpy", ("numpy", "1.1.1", "https://pypi.org/simple")),
                ]
            ),
        }

    def test_multi_package_resolutions(self, resolver: Resolver) -> None:
        """Test resolutions of a same package and call of run method."""
        pypi = Source("https://pypi.org/simple")

        package_version1 = PackageVersion(
            name="tensorflow", version="==2.0.0", index=pypi, develop=False
        )

        state = State(
            score=1.0,
            unresolved_dependencies=OrderedDict(
                [("flask", ("flask", "1.12.0", "https://pypi.org/simple"))]
            ),
            resolved_dependencies=OrderedDict(
                [(package_version1.name, package_version1.to_tuple())]
            ),
        )

        assert (
            len(resolver.pipeline.steps) == 1
        ), "A pre-requisite for this test case is to have exactly one step in the pipeline configuration"

        resolver.pipeline.steps[0].MULTI_PACKAGE_RESOLUTIONS = True

        # Should be called only once with package_version2, no package_version1 call as
        # MULTI_PACKAGE_RESOLUTIONS is off.
        resolver.pipeline.steps[0].should_receive("run").with_args(
            state, package_version1
        ).and_return(None).once()

        # Make sure we report multi package resolution.
        resolver.should_receive("_report_shared_dependency").with_args(
            package_version1.to_tuple()
        ).and_return(None).once()

        resolver._init_context()
        assert resolver.beam.size == 0
        assert (
            resolver._run_steps(state, {package_version1.name: [package_version1]})
            is None
        )
        assert resolver.beam.size == 1
        assert resolver.beam.top().to_dict() == {
            "advised_runtime_environment": None,
            "iteration": 0,
            "iteration_states_added": 0,
            "latest_version_offset": 0,
            "justification": [],
            "resolved_dependencies": OrderedDict(
                [("tensorflow", ("tensorflow", "2.0.0", "https://pypi.org/simple"))]
            ),
            "score": 1.0,
            "unresolved_dependencies": OrderedDict(
                [("flask", ("flask", "1.12.0", "https://pypi.org/simple"))]
            ),
        }

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

        with pytest.raises(StepError):
            assert resolver._run_steps(
                state, {pv.name: [pv] for pv in package_versions[:3]}
            )

        assert original_state == state, "State is not untouched"

    @pytest.mark.parametrize("score", [float("inf"), float("nan")])
    def test_run_steps_inf_nan(
        self, score: float, resolver: Resolver, package_versions: List[PackageVersion]
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
            state, package_versions[0]
        ).and_return((score, [{"foo": "bar"}])).once()

        resolver.pipeline.steps = [steps.Step1()]

        with pytest.raises(StepError):
            assert resolver._run_steps(
                state, {pv.name: [pv] for pv in package_versions[:3]}
            )

        assert original_state == state, "State is not untouched"

    def test_run_steps_combinations(
        self,
        resolver: Resolver,
        tf_package_versions: List[PackageVersion],
        numpy_package_versions: List[PackageVersion],
    ) -> None:
        """Test running steps on all the combinations computed during backtracking runs."""
        state = State()

        # Lists are stored from oldest to newest, reverse order.
        tf_package_versions.reverse()
        numpy_package_versions.reverse()

        resolver._init_context()
        assert (
            resolver._run_steps(
                state,
                {
                    tf_package_versions[0].name: tf_package_versions,
                    numpy_package_versions[0].name: numpy_package_versions,
                },
            )
            is None
        )
        assert resolver.beam.size == len(tf_package_versions) * len(
            numpy_package_versions
        )

        run_steps_products = []
        for state in resolver.beam.iter_states_sorted():
            run_steps_products.append(
                [item for item in state.unresolved_dependencies.values()]
            )

        # The logic behind creating new states respects relative offset in releases.
        itertools_products_count = len(list(itertools.product(tf_package_versions, numpy_package_versions)))

        assert itertools_products_count == len(run_steps_products)
        assert run_steps_products == [
            [
                ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ("numpy", "1.17.3", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ("numpy", "1.17.2", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "1.9.0", "https://pypi.org/simple"),
                ("numpy", "1.17.3", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ("numpy", "1.17.1", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "1.9.0", "https://pypi.org/simple"),
                ("numpy", "1.17.2", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "1.9.0rc1", "https://pypi.org/simple"),
                ("numpy", "1.17.3", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ("numpy", "1.17.0", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "1.9.0", "https://pypi.org/simple"),
                ("numpy", "1.17.1", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "1.9.0rc1", "https://pypi.org/simple"),
                ("numpy", "1.17.2", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "1.9.0", "https://pypi.org/simple"),
                ("numpy", "1.17.0", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "1.9.0rc1", "https://pypi.org/simple"),
                ("numpy", "1.17.1", "https://pypi.org/simple"),
            ],
            [
                ("tensorflow", "1.9.0rc1", "https://pypi.org/simple"),
                ("numpy", "1.17.0", "https://pypi.org/simple"),
            ],
        ]

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

    def test_semver_sort_prepare_initial_states(
        self,
        resolver: Resolver,
        tf_package_versions: List[PackageVersion],
        flask_package_versions: List[PackageVersion],
    ) -> None:
        """Test no limit on latest versions in when sorting based on semver."""
        resolver.limit_latest_versions = None
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
        resolver._prepare_initial_states(with_devel=False)
        assert resolver.beam.size == len(tf_package_versions) * len(
            flask_package_versions
        )

    def test_limit_latest_versions(
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
        resolver._prepare_initial_states(with_devel=False)
        assert (
            resolver.beam.size == 2 * 2
        ), "List of packages was not reduced based on limit latest version configuration"

        for state in resolver.beam.iter_states():
            assert "flask" in state.unresolved_dependencies
            assert "tensorflow" in state.unresolved_dependencies

            assert state.unresolved_dependencies["tensorflow"][1] in [
                p.locked_version for p in tf_package_versions[:2]
            ], "Not two latest TensorFlow packages picked"

            assert state.unresolved_dependencies["flask"][1] in [
                p.locked_version for p in flask_package_versions[:2]
            ], "Not two latest Flask packages picked"

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
        resolver.should_receive("_run_sieves").with_args(object).and_yield(
            *numpy_package_versions
        ).ordered()
        resolver.should_receive("_run_sieves").with_args(object).and_yield(
            *tf_package_versions
        ).ordered()

        # Default steps do not filter out any state, let't produce them all in this case.
        resolver._init_context()
        assert resolver._prepare_initial_states(with_devel=True) is None

        for package_version in itertools.chain(
            numpy_package_versions, tf_package_versions
        ):
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

        assert resolver.beam.size == len(tf_package_versions) * len(
            numpy_package_versions
        ), "Incorrect number of initial states produced"

        for state in resolver.beam.iter_states():
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

    def test_expand_state_not_found(self, resolver: Resolver, state: State) -> None:
        """Test expanding a state when a package was not found."""
        to_expand_package_name = next(iter(state.unresolved_dependencies))
        to_expand_package_tuple = state.unresolved_dependencies[to_expand_package_name]

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
        ).and_raise(NotFoundError).once()
        assert resolver._expand_state(state=state) is None

    def test_expand_state_no_dependencies_final(
        self, resolver: Resolver, state: State
    ) -> None:
        """Test expanding a state when the given package has no dependencies producing final state."""
        to_expand_package_name = next(iter(state.unresolved_dependencies))
        to_expand_package_tuple = state.unresolved_dependencies[to_expand_package_name]

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
        ).and_return([]).once()

        assert (
            len(state.unresolved_dependencies) == 1
        ), "State in the test case should have only once dependency to resolve in order to check production of a final state"

        original_resolved_count = len(state.resolved_dependencies)

        assert (
            resolver._expand_state(state) is state
        ), "State returned is not the one passed"
        assert (
            to_expand_package_name in state.resolved_dependencies
        ), "Package not added to resolved dependencies"
        assert (
            state.resolved_dependencies[to_expand_package_name]
            == to_expand_package_tuple
        )
        assert (
            len(state.resolved_dependencies) == original_resolved_count + 1
        ), "State returned has no adjusted resolved dependencies"
        assert resolver.beam.size == 0, "Some adjustments to beam were made"

    def test_expand_state_no_dependencies_not_final(
        self, resolver: Resolver, state: State
    ) -> None:
        """Test expanding a state when the given package has no dependencies producing not final state."""
        to_expand_package_name = next(iter(state.unresolved_dependencies))
        to_expand_package_tuple = state.unresolved_dependencies[to_expand_package_name]

        # Add one more making sure there will be still some unresolved dependencies.
        assert (
            "flask" not in state.unresolved_dependencies
        ), "State cannot have package flask in unresolved for this test case"
        state.unresolved_dependencies["flask"] = (
            "flask",
            "0.12",
            "https://pypi.org/simple",
        )

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
        ).and_return([]).once()

        original_resolved_count = len(state.resolved_dependencies)

        returned_value = resolver._expand_state(state)

        assert returned_value is None, "No state should be returned"
        assert (
            to_expand_package_name in state.resolved_dependencies
        ), "Package not added to resolved dependencies"
        assert (
            state.resolved_dependencies[to_expand_package_name]
            == to_expand_package_tuple
        )
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
        to_expand_package_name = next(iter(state.unresolved_dependencies))
        to_expand_package_tuple = state.unresolved_dependencies[to_expand_package_name]

        assert to_expand_package_tuple[0] == "tensorflow"

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

        expected_state = state.clone()
        expected_state.resolved_dependencies[
            to_expand_package_name
        ] = to_expand_package_tuple
        expected_state.unresolved_dependencies.pop(to_expand_package_name)

        resolver.should_receive("_expand_state_add_dependencies").with_args(
            state=expected_state,
            package_version=package_version,
            dependencies=[(pv.name, pv.locked_version) for pv in dep_package_versions],
        ).and_return(None).once()

        assert resolver._expand_state(state) is None

    def test_expand_state_add_dependencies_marker_evaluation_result(
        self, resolver: Resolver
    ) -> None:
        """Test call to adding new dependencies behavior for marker evaluation result."""
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://pypi.org.simple"),
            extras=["s3"],
            develop=False,
        )

        resolver.project.runtime_environment.should_receive(
            "is_fully_specified"
        ).with_args().and_return(True)

        resolver.graph.should_receive(
            "get_python_environment_marker_evaluation_result"
        ).with_args(
            *package_version.to_tuple(),
            dependency_name="absl-py",
            dependency_version="0.8.1",
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(
            True
        ).once()

        # tensorboard==2.0.0 gets discarded
        resolver.graph.should_receive(
            "get_python_environment_marker_evaluation_result"
        ).with_args(
            *package_version.to_tuple(),
            dependency_name="tensorboard",
            dependency_version="2.0.0",
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(
            False
        ).once()

        resolver.graph.should_receive(
            "get_python_environment_marker_evaluation_result"
        ).with_args(
            *package_version.to_tuple(),
            dependency_name="tensorboard",
            dependency_version="2.0.1",
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(
            True
        ).once()

        tb_records = [
            {
                "package_name": "tensorboard",
                "package_version": "2.0.1",
                "index_url": "https://pypi.org/simple",
                "os_name": "linuxos",
                "os_version": "3",
                "python_version": "4.0",
            }
        ]

        absl_py_records = [
            {
                "package_name": "absl-py",
                "package_version": "0.8.1",
                "index_url": "https://pypi.org/simple",
                "os_name": "linuxos",
                "os_version": "3",
                "python_version": "4.0",
            },
            {
                "package_name": "absl-py",
                "package_version": "0.8.1",
                "index_url": "https://pypi.org/simple",
                "os_name": "featherlinux",
                "os_version": "1",
                "python_version": "4.2",
            },
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
            package_version="2.0.1",
            index_url=None,
            os_name=resolver.project.runtime_environment.operating_system.name,
            os_version=resolver.project.runtime_environment.operating_system.version,
            python_version=resolver.project.runtime_environment.python_version,
        ).and_return(tb_records).once()

        assert resolver.pipeline.sieves, "No sieves to run this test case with"
        for sieve in resolver.pipeline.sieves:
            # No sieve is called with the discarded package based on env marker.
            sieve.should_call("run").twice()

        assert resolver.pipeline.steps, "No steps to run this test case with"
        for step in resolver.pipeline.steps:
            step.should_call("run").twice()

        state = State(score=0.0)
        assert resolver.beam.size == 0

        resolver._init_context()
        resolver.context.register_package_version(package_version)
        resolver._expand_state_add_dependencies(
            state=state,
            package_version=package_version,
            dependencies=[
                ("absl-py", "0.8.1"),
                ("tensorboard", "2.0.0"),
                ("tensorboard", "2.0.1"),
            ],
        )

        # We end up with one state as tensorboard's marker evaluation is False in tensorboard==2.0.0.
        assert resolver.beam.size == 1
        assert resolver.beam.top().to_dict() == {
            "score": 0.0,
            "iteration": 0,
            "iteration_states_added": 0,
            "latest_version_offset": 0,
            "unresolved_dependencies": OrderedDict(
                [
                    ("absl-py", ("absl-py", "0.8.1", "https://pypi.org/simple")),
                    (
                        "tensorboard",
                        ("tensorboard", "2.0.1", "https://pypi.org/simple"),
                    ),
                ]
            ),
            "resolved_dependencies": OrderedDict(),
            "advised_runtime_environment": None,
            "justification": [],
        }
        assert resolver.beam.top() is not state, "State was not cloned"

        for record in itertools.chain(tb_records, absl_py_records):
            package_version = resolver.context.get_package_version(
                (record["package_name"], record["package_version"], record["index_url"])
            )
            assert package_version.extras is None
            assert package_version.markers is None
            assert not package_version.hashes
            assert package_version.develop is False

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

        # We end up with one state as tensorboard's marker evaluation is False in tensorboard==2.0.0.
        assert (
            resolver.beam.size == 0
        ), "A new state was added even the dependency sub-graph is not resolved"

    def test_expand_state_add_dependencies_combinations(
        self, resolver: Resolver
    ) -> None:
        """Test creation of combinations for state dependencies."""
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

        dependency_records = [
            {
                "package_name": "tensorboard",
                "package_version": "2.0.0",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "29",
                "python_version": "3.6",
            },
            {
                "package_name": "tensorboard",
                "package_version": "2.0.1",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "29",
                "python_version": "3.6",
            },
            {
                "package_name": "tensorboard",
                "package_version": "2.0.2",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "29",
                "python_version": "3.6",
            },
            {
                "package_name": "absl-py",
                "package_version": "0.8.1",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "29",
                "python_version": "3.6",
            },
            {
                "package_name": "absl-py",
                "package_version": "0.8.2",
                "index_url": "https://pypi.org/simple",
                "os_name": "fedora",
                "os_version": "29",
                "python_version": "3.6",
            },
        ]

        for dependency_record in dependency_records:
            resolver.graph.should_receive(
                "get_python_package_version_records"
            ).with_args(
                package_name=dependency_record["package_name"],
                package_version=dependency_record["package_version"],
                index_url=None,
                os_name=resolver.project.runtime_environment.operating_system.name,
                os_version=resolver.project.runtime_environment.operating_system.version,
                python_version=resolver.project.runtime_environment.python_version,
            ).and_return(
                [dependency_record]
            ).once()

        state = State(score=0.0)

        resolver._init_context()
        resolver.context.register_package_version(package_version)
        resolver._expand_state_add_dependencies(
            state=state,
            package_version=package_version,
            dependencies=[
                (rec["package_name"], rec["package_version"])
                for rec in dependency_records
            ],
        )

        assert resolver.beam.size == 3 * 2, "Wrong number of states computed"

        record_group = {}
        for record in dependency_records:
            if record["package_name"] not in record_group:
                record_group[record["package_name"]] = []

            record_group[record["package_name"]].append(
                (record["package_name"], record["package_version"], record["index_url"])
            )

        computed_combinations = [
            set(state.unresolved_dependencies.values())
            for state in resolver.beam.iter_states()
        ]
        for combination in itertools.product(*record_group.values()):
            combination = set(combination)
            assert (
                combination in computed_combinations
            ), f"Expected combination {combination!r} was not computed"

            for package_tuple in combination:
                assert resolver.context.get_package_version(package_tuple) is not None

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

        initial_state1 = State(score=0.0)
        initial_state2 = State(score=1.0)
        initial_state3 = State(score=2.0)

        flexmock(Beam)
        resolver.beam.should_receive("new_iteration").and_return(None).twice()
        resolver.beam.add_state(initial_state1)
        resolver.beam.add_state(initial_state2)
        resolver.beam.add_state(initial_state3)

        resolver.limit = 1
        resolver._init_context()

        for boot in resolver.pipeline.boots:
            boot.should_receive("run").with_args().and_return(None).once()

        for stride in resolver.pipeline.strides:
            stride.should_receive("run").with_args(final_state).and_return(None).once()

        for wrap in resolver.pipeline.wraps:
            wrap.should_receive("run").with_args(final_state).and_return(None).once()

        resolver.should_receive("_prepare_initial_states").with_args(
            with_devel=True
        ).and_return(resolver.beam).once()

        resolver.predictor.should_receive("run").with_args(
            resolver.context, resolver.beam
        ).and_return(initial_state2).and_return(initial_state1).twice()

        resolver.should_receive("_expand_state").with_args(initial_state2).and_return(
            None
        ).once()

        resolver.should_receive("_expand_state").with_args(initial_state1).and_return(
            final_state
        ).once()

        states = list(resolver._do_resolve_states(with_devel=True))
        assert states == [final_state]
        assert resolver.context.iteration == 2
        assert resolver.context.accepted_final_states_count == 1
        assert resolver.context.discarded_final_states_count == 0
        assert resolver.beam.size == 1
        assert resolver.beam.top() is initial_state3

    def test_expand_state_no_unresolved(self, resolver: Resolver) -> None:
        """Test expansion of a state that has no unresolved dependencies."""
        state = State(score=1.0, unresolved_dependencies=OrderedDict([]))
        assert resolver._expand_state(state) is state

    def test_marker_leaf_dep_node_marker_false_resolver(self, resolver: Resolver) -> None:
        """Add a check for leaf dependency nodes for which environment markers apply and remove dependencies."""
        package_tuple = ("hexsticker", "1.0.0", "https://pypi.org/simple")
        state = State(
            score=1.0,
            unresolved_dependencies=OrderedDict([(package_tuple[0], package_tuple)]),
        )
        resolver._init_context()

        resolver.graph.should_receive("get_depends_on").with_args(
                *package_tuple,
                os_name=None,
                os_version=None,
                python_version=None,
                extras=frozenset([None]),
        ).and_return({
            "enum34": [("enum34", "1.1.6")]
        }).once()

        resolver.project.runtime_environment.should_receive("is_fully_specified").and_return(True).once()

        resolver.graph.should_receive("get_python_environment_marker_evaluation_result").with_args(
            *package_tuple,
            dependency_name="enum34",
            dependency_version="1.1.6",
            os_name=None,
            os_version=None,
            python_version=None,
        ).and_return(False).once()

        resolver.context.register_package_tuple(
            package_tuple,
            develop=False,
            os_name=None,
            os_version=None,
            python_version=None,
        )
        resolver.should_receive("_run_steps").times(0)
        assert resolver._expand_state(state) is state

    def test_marker_leaf_dep_node_marker_true_unresolved(self, resolver: Resolver) -> None:
        """Add a check for leaf dependency nodes for which environment markers apply and remove dependencies."""
        package_tuple = ("hexsticker", "1.0.0", "https://pypi.org/simple")
        state = State(
            score=1.0,
            unresolved_dependencies=OrderedDict([
                (package_tuple[0], package_tuple),
                ("flask", ("flask", "1.0.0", "https://pypi.org/simple")),
            ]),
        )
        resolver._init_context()

        resolver.graph.should_receive("get_depends_on").with_args(
                *package_tuple,
                os_name=None,
                os_version=None,
                python_version=None,
                extras=frozenset([None]),
        ).and_return({
            "enum34": [("enum34", "1.1.6")]
        }).once()

        resolver.project.runtime_environment.should_receive("is_fully_specified").and_return(True).once()

        resolver.graph.should_receive("get_python_environment_marker_evaluation_result").with_args(
            *package_tuple,
            dependency_name="enum34",
            dependency_version="1.1.6",
            os_name=None,
            os_version=None,
            python_version=None,
        ).and_return(False).once()

        resolver.should_receive("_run_steps").times(0)

        resolver.context.register_package_tuple(
            package_tuple,
            develop=False,
            os_name=None,
            os_version=None,
            python_version=None,
        )
        assert resolver._expand_state(state) is None

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

        initial_state1 = State(score=0.0)
        initial_state2 = State(score=1.0)
        initial_state3 = State(score=2.0)

        resolver.beam.add_state(initial_state1)
        resolver.beam.add_state(initial_state2)
        resolver.beam.add_state(initial_state3)

        resolver._init_context()

        resolver.should_receive("_prepare_initial_states").with_args(
            with_devel=True
        ).and_return(None).once()

        resolver.predictor.should_receive("run").with_args(object, object).and_return(
            initial_state1
        ).and_return(initial_state2).and_return(initial_state3).times(3)

        resolver.should_receive("_expand_state").with_args(initial_state3).and_return(
            final_state
        ).once()

        resolver.should_receive("_expand_state").with_args(initial_state1).and_return(
            final_state
        ).once()

        resolver.should_receive("_expand_state").with_args(initial_state2).and_return(
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
        flexmock(Context).new_instances(flexmock(stack_info=stack_info))

        with pytest.raises(ValueError):
            assert resolver.context, "Context is already bound to resolver"

        report = resolver.resolve(with_devel=True)

        assert resolver.context is not None, "Context is not bound to resolver"
        assert report.product_count() == 1
        assert list(report.iter_products()) == [product]
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
