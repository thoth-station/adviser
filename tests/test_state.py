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

"""Test state representation."""

import pytest
from collections import OrderedDict

from thoth.adviser.state import State
from thoth.common import RuntimeEnvironment
from .base import AdviserTestCase


@pytest.fixture
def state() -> State:
    """A fixture for a non-final state."""
    state = State(
        score=0.1,
        unresolved_dependencies=OrderedDict(
            {"flask": ("flask", "1.1.1", "https://pypi.org/simple")}
        ),
        resolved_dependencies=OrderedDict(
            {"hexsticker": ("hexsticker", "1.0.0", "https://pypi.org/simple")}
        ),
        advised_runtime_environment=RuntimeEnvironment.from_dict(
            {"python_version": "3.6"}
        ),
    )
    state.add_justification([{"foo": "bar"}, {"bar": "baz"}])
    return state


@pytest.fixture
def final_state() -> State:
    """A fixture for a final state."""
    state = State(
        score=0.5,
        resolved_dependencies=OrderedDict(
            {"daiquiri": ("daiquiri", "1.6.0", "https://pypi.org/simple")}
        ),
        unresolved_dependencies=OrderedDict(),
        advised_runtime_environment=None,
    )
    state.add_justification([{"foo": "bar"}])
    return state


class TestState(AdviserTestCase):
    """Test state representation and manipulation."""

    def test_justification(self, final_state: State) -> None:
        """Test manipulation with state justification."""
        assert final_state.justification == [{"foo": "bar"}]
        final_state.add_justification([{"hello": "thoth"}])
        assert final_state.justification == [{"foo": "bar"}, {"hello": "thoth"}]

    def test_is_final(self, state: State, final_state: State) -> None:
        """Test checks for final states."""
        assert final_state.is_final()
        assert not state.is_final()
        state.unresolved_dependencies.pop("flask")
        assert state.is_final()

    def test_add_unresolved_dependency(self, final_state: State) -> None:
        """Test adding unresolved dependencies into a state."""
        # This is actually never done in the code (from final state to a non-final state), but
        # let's test turning the switch.
        assert final_state.is_final()
        final_state.add_unresolved_dependency(
            ("selinon", "1.0.0", "https://pypi.org/simple")
        )
        assert not final_state.is_final()
        final_state.unresolved_dependencies.pop("selinon")
        assert final_state.is_final()

    def test_clone(self, state: State) -> None:
        """Test cloning of states and their memory footprints."""
        cloned_state = state.clone()
        assert cloned_state is not state
        assert cloned_state.score == state.score

        # Check swallow copies.
        assert cloned_state.unresolved_dependencies is not state.unresolved_dependencies
        assert cloned_state.unresolved_dependencies == state.unresolved_dependencies
        assert cloned_state.resolved_dependencies is not state.resolved_dependencies
        assert cloned_state.resolved_dependencies == state.resolved_dependencies
        assert (
            cloned_state.advised_runtime_environment
            is not state.advised_runtime_environment
        )
        assert (
            cloned_state.advised_runtime_environment
            == state.advised_runtime_environment
        )
        assert cloned_state.justification is not state.justification
        assert cloned_state.justification == state.justification
