#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""Test implementation of predictor approximating latest resolution."""

from typing import Callable
from collections import OrderedDict

import flexmock
from hypothesis import given
from hypothesis.strategies import integers

from thoth.adviser.beam import Beam
from thoth.adviser.predictors import ApproximatingLatest
from thoth.adviser.state import State

from ..base import AdviserTestCase


class TestApproximatingLatest(AdviserTestCase):
    """Test implementation of predictor approximating latest resolution."""

    @given(integers(min_value=1, max_value=256),)
    def test_run(self, state_factory: Callable[[], State], state_count: int) -> None:
        """Test running the approximating latest method."""
        state = state_factory()
        beam = Beam()
        for _ in range(state_count):
            cloned_state = state.clone()
            cloned_state.iteration = state.iteration + 1
            beam.add_state(cloned_state)

        predictor = ApproximatingLatest()
        # Add an item to the heat up entry so that assume the heat-up process was already done.
        predictor._packages_heated_up = {"some-package"}
        context = flexmock(accepted_final_states_count=33, beam=beam)
        with predictor.assigned_context(context):
            next_state, package_tuple = predictor.run()
            assert next_state is not None
            assert next_state in beam.iter_states()
            assert package_tuple[0] in next_state.unresolved_dependencies
            assert package_tuple in next_state.unresolved_dependencies[package_tuple[0]].values()

    def test_heat_up(self) -> None:
        """Test the heat up phase."""
        beam = Beam()

        dependency_tuple_1 = ("tensorflow", "2.1.0", "https://pypi.org/simple")
        dependency_tuple_2 = ("tensorflow", "2.0.0", "https://pypi.org/simple")
        dependency_tuple_3 = ("tensorflow", "1.15.0", "https://pypi.org/simple")
        dependency_tuple_4 = ("flask", "1.1.1", "https://pypi.org/simple")
        dependency_tuple_5 = ("flask", "1.0", "https://pypi.org/simple")

        state = State(
            score=0.999,
            resolved_dependencies=OrderedDict(),
            unresolved_dependencies=OrderedDict(
                (
                    (
                        "tensorflow",
                        OrderedDict(
                            (
                                (hash(dependency_tuple_1), dependency_tuple_1),
                                (hash(dependency_tuple_2), dependency_tuple_2),
                                (hash(dependency_tuple_3), dependency_tuple_3),
                            )
                        ),
                    ),
                    (
                        "flask",
                        OrderedDict(
                            (
                                (hash(dependency_tuple_4), dependency_tuple_4),
                                (hash(dependency_tuple_5), dependency_tuple_5),
                            )
                        ),
                    ),
                )
            ),
        )

        beam.add_state(state)

        predictor = ApproximatingLatest()
        context = flexmock(accepted_final_states_count=0, beam=beam)

        assert not predictor._packages_heated_up
        with predictor.assigned_context(context):
            next_state, package_tuple = predictor.run()

        assert next_state is state
        assert "tensorflow" in predictor._packages_heated_up
        assert package_tuple is dependency_tuple_1

        with predictor.assigned_context(context):
            next_state, package_tuple = predictor.run()

        assert next_state is state
        assert "tensorflow" in predictor._packages_heated_up
        assert "flask" in predictor._packages_heated_up
        assert package_tuple is dependency_tuple_4

    def test_heat_up_end(self) -> None:
        """Test the end of the heat up phase."""
        flexmock(Beam)
        beam = Beam()

        dependency_tuple_1 = ("tensorflow", "2.1.0", "https://pypi.org/simple")
        dependency_tuple_2 = ("tensorflow", "2.0.0", "https://pypi.org/simple")
        dependency_tuple_3 = ("tensorflow", "1.15.0", "https://pypi.org/simple")
        dependency_tuple_4 = ("flask", "1.1.1", "https://pypi.org/simple")
        dependency_tuple_5 = ("flask", "1.0", "https://pypi.org/simple")

        state = State(
            score=0.999,
            resolved_dependencies=OrderedDict(),
            unresolved_dependencies=OrderedDict(
                (
                    (
                        "tensorflow",
                        OrderedDict(
                            (
                                (hash(dependency_tuple_1), dependency_tuple_1),
                                (hash(dependency_tuple_2), dependency_tuple_2),
                                (hash(dependency_tuple_3), dependency_tuple_3),
                            )
                        ),
                    ),
                    (
                        "flask",
                        OrderedDict(
                            (
                                (hash(dependency_tuple_4), dependency_tuple_4),
                                (hash(dependency_tuple_5), dependency_tuple_5),
                            )
                        ),
                    ),
                )
            ),
        )

        beam.add_state(state)

        last_state = flexmock(score=100)
        first_unresolved_dependency = flexmock()
        last_state.should_receive("get_first_unresolved_dependency").and_return(first_unresolved_dependency).once()
        beam.should_receive("get_last").and_return(last_state).once()

        flexmock(ApproximatingLatest)
        predictor = ApproximatingLatest()
        predictor._initial_state = state
        context = flexmock(accepted_final_states_count=0, beam=beam)

        predictor._packages_heated_up.add("tensorflow")
        predictor._packages_heated_up.add("flask")

        with predictor.assigned_context(context):
            next_state, package_tuple = predictor.run()

        assert package_tuple is first_unresolved_dependency
        assert next_state is last_state
