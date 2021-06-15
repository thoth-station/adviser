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

"""Test state representation."""

import gc
import pytest
import random
import string
from itertools import chain

from thoth.adviser.state import State
from .base import AdviserTestCase


@pytest.fixture
def final_state() -> State:  # noqa: D401
    """A fixture for a final state."""
    state = State(
        score=0.5,
        resolved_dependencies={"daiquiri": ("daiquiri", "1.6.0", "https://pypi.org/simple")},
        unresolved_dependencies={},
        advised_runtime_environment=None,
    )
    state.add_justification(AdviserTestCase.JUSTIFICATION_SAMPLE_1)
    return state


class TestState(AdviserTestCase):
    """Test state representation and manipulation."""

    def test_justification(self, final_state: State) -> None:
        """Test manipulation with state justification."""
        assert final_state.justification == self.JUSTIFICATION_SAMPLE_1
        final_state.add_justification(self.JUSTIFICATION_SAMPLE_2)
        assert final_state.justification == list(chain(self.JUSTIFICATION_SAMPLE_1, self.JUSTIFICATION_SAMPLE_2))

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
        final_state.add_unresolved_dependency(("selinon", "1.0.0", "https://pypi.org/simple"))
        assert not final_state.is_final()
        final_state.unresolved_dependencies.pop("selinon")
        assert final_state.is_final()

    def test_get_random_first_unresolved_dependency(self) -> None:
        """Test getting random first unresolved dependency."""
        state = State(score=1.0)
        package_tuple1 = ("tensorflow", "2.1.0", "https://pypi.org/simple")
        package_tuple2 = ("selinon", "1.0.0", "https://pypi.org/simple")

        state.add_unresolved_dependency(package_tuple1)

        assert state.get_random_first_unresolved_dependency() is package_tuple1

        state.add_unresolved_dependency(package_tuple2)

        random_state = random.getstate()
        try:
            random.seed(42)
            assert state.get_random_first_unresolved_dependency() is package_tuple1
            assert state.get_random_first_unresolved_dependency() is package_tuple1
            assert state.get_random_first_unresolved_dependency() is package_tuple2
            assert state.get_random_first_unresolved_dependency() is package_tuple1
        finally:
            random.setstate(random_state)

    def test_get_random_first_unresolved_dependency_error(self) -> None:
        """Test raising an error on random first unresolved dependency if no dependency is available."""
        state = State(score=1.0)
        with pytest.raises(IndexError):
            state.get_random_first_unresolved_dependency()

    def test_clone(self, state: State) -> None:
        """Test cloning of states and their memory footprints."""
        cloned_state = state.clone()
        assert cloned_state is not state
        assert cloned_state.score == state.score

        # Check swallow copies.
        assert cloned_state.unresolved_dependencies is not state.unresolved_dependencies
        assert cloned_state.unresolved_dependencies == state.unresolved_dependencies

        for dependency_name in cloned_state.unresolved_dependencies:
            assert (
                cloned_state.unresolved_dependencies[dependency_name] == state.unresolved_dependencies[dependency_name]
            )
            assert (
                cloned_state.unresolved_dependencies[dependency_name]
                is not state.unresolved_dependencies[dependency_name]
            )

        assert cloned_state.resolved_dependencies is not state.resolved_dependencies
        assert cloned_state.resolved_dependencies == state.resolved_dependencies
        assert cloned_state.advised_runtime_environment is not state.advised_runtime_environment
        assert cloned_state.advised_runtime_environment == state.advised_runtime_environment
        assert cloned_state.justification is not state.justification
        assert cloned_state.justification == state.justification
        assert cloned_state.advised_manifest_changes is not state.advised_manifest_changes

    def test_parent(self) -> None:
        """Test referencing parent and weak reference handling."""
        state = State()
        cloned_state = state.clone()

        assert cloned_state.parent is state

        del state
        gc.collect()

        assert cloned_state.parent is None

    @pytest.mark.parametrize("n", range(5))
    def test_dict_order(self, n: int) -> None:
        """Test relative insertion into dict preserves order.

        This is an implementation detail for Python3.6 dict implementation and
        requirement for Python 3.7. Make sure the running interpreter obeys
        this.
        """
        items = []
        seen = set()
        for i in range(10):
            key = "".join(random.choice(string.ascii_letters) for i in range(n))
            if key in seen:
                continue

            seen.add(key)
            items.append((key, i))

        dict_ = dict(items)
        assert list(dict_.items()) == items, "Order of items in dict is not preserved"

        dict_["foo"] = 3003
        assert list(dict_.items())[-1] == ("foo", 3003), "Last item added to dict is not last obtained"
