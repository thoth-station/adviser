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

"""Test adviser's context passed to pipeline units."""

from typing import Tuple

import pytest

from thoth.python import PackageVersion
from thoth.python import Source

from thoth.adviser.state import State
from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import DecisionType
from thoth.adviser.exceptions import NotFound

from .base import AdviserTestCase


@pytest.fixture
def package_version() -> PackageVersion:  # noqa: D401
    """A fixture for a package version representative."""
    return PackageVersion(name="selinon", version="==1.0.0", index=Source("https://pypi.org/simple"), develop=False,)


@pytest.fixture
def package_tuple() -> Tuple[str, str, str]:  # noqa: D401
    """A fixture for a package tuple representative."""
    return "selinon", "1.0.0", "https://pypi.org/simple"


class TestContext(AdviserTestCase):
    """Test context carried within resolution."""

    def test_get_package_version(self, context: Context, package_version: PackageVersion) -> None:
        """Test getting registering and getting a package version."""
        with pytest.raises(NotFound):
            context.get_package_version(package_version.to_tuple())

        assert context.register_package_version(package_version) is False
        assert context.get_package_version(package_version.to_tuple()) is package_version

    def test_get_package_version_graceful(self, context: Context, package_version: PackageVersion) -> None:
        """Test getting registered package version, gracefully."""
        assert context.get_package_version(package_version.to_tuple(), graceful=True) is None
        with pytest.raises(NotFound):
            context.get_package_version(package_version.to_tuple(), graceful=False)

        assert context.register_package_version(package_version) is False

        assert context.get_package_version(package_version.to_tuple(), graceful=True) is package_version
        assert context.get_package_version(package_version.to_tuple(), graceful=False) is package_version

    def test_get_top_accepted_final_state(self, context: Context) -> None:
        """Test retrieval of top accepted final state."""
        context.count = 10

        assert context.get_top_accepted_final_state() is None

        state1 = State(score=0.0)
        assert context.register_accepted_final_state(state1) is None
        assert context.get_top_accepted_final_state() is state1

        state2 = State(score=1.0)
        assert context.register_accepted_final_state(state2) is None
        assert context.get_top_accepted_final_state() is state2

        state3 = State(score=2.0)
        assert context.register_accepted_final_state(state3) is None
        assert context.get_top_accepted_final_state() is state3

        state4 = State(score=0.5)
        assert context.register_accepted_final_state(state4) is None
        assert context.get_top_accepted_final_state() is state3

    def test_register_accepted_final_state(self, context: Context) -> None:
        """Test registering accepted final state and final state manipulation."""
        context.count = 2

        state1 = State(score=0.0)
        assert context.register_accepted_final_state(state1) is None
        assert state1 in context.iter_accepted_final_states()
        assert list(context.iter_accepted_final_states()) == [state1]

        state2 = State(score=1.0)
        assert context.register_accepted_final_state(state2) is None
        assert state1 in context.iter_accepted_final_states()
        assert state2 in context.iter_accepted_final_states()
        assert list(context.iter_accepted_final_states_sorted()) == [state2, state1]
        assert list(context.iter_accepted_final_states_sorted(reverse=True)) == [state2, state1]
        assert list(context.iter_accepted_final_states_sorted(reverse=False)) == [state1, state2]

        state3 = State(score=3.0)
        assert context.register_accepted_final_state(state3) is None
        assert state3 in context.iter_accepted_final_states_sorted()
        assert state2 in context.iter_accepted_final_states_sorted()
        assert list(context.iter_accepted_final_states_sorted()) == [state3, state2]
        assert list(context.iter_accepted_final_states_sorted(reverse=True)) == [state3, state2]
        assert list(context.iter_accepted_final_states_sorted(reverse=False)) == [state2, state3]

        state4 = State(score=2.0)
        assert context.register_accepted_final_state(state4) is None
        assert state3 in context.iter_accepted_final_states()
        assert state4 in context.iter_accepted_final_states()
        assert list(context.iter_accepted_final_states_sorted()) == [state3, state4]
        assert list(context.iter_accepted_final_states_sorted(reverse=True)) == [state3, state4]
        assert list(context.iter_accepted_final_states_sorted(reverse=False)) == [state4, state3]

        state5 = State(score=0.1)
        assert context.register_accepted_final_state(state5) is None
        assert state3 in context.iter_accepted_final_states()
        assert state4 in context.iter_accepted_final_states()
        assert list(context.iter_accepted_final_states_sorted()) == [state3, state4]
        assert list(context.iter_accepted_final_states_sorted(reverse=True)) == [state3, state4]
        assert list(context.iter_accepted_final_states_sorted(reverse=False)) == [state4, state3]

    def test_register_package_version_existing(self, context: Context, package_version: PackageVersion) -> None:
        """Test registering an existing package version to context."""
        assert context.register_package_version(package_version) is False
        assert context.get_package_version(package_version.to_tuple()) is package_version
        assert context.register_package_version(package_version) is True

    def test_register_package_tuple_new(self, context: Context, package_tuple: Tuple[str, str, str]) -> None:
        """Test registering a new package tuple to the context."""
        with pytest.raises(NotFound):
            context.get_package_version(package_tuple)

        extras = ["postgresql"]

        assert (
            context.register_package_tuple(
                package_tuple, develop=True, extras=extras, os_name="rhel", os_version="8.1", python_version="3.6"
            )
            is not None
        )

        package_version = context.get_package_version(package_tuple)

        assert package_version.name == "selinon"
        assert package_version.version == "==1.0.0"
        assert package_version.develop is True
        assert package_version.index is not None
        assert package_version.index.url == "https://pypi.org/simple"
        assert package_version.markers is None
        assert package_version.extras == extras

    def test_register_package_tuple_existing(self, context: Context, package_tuple: Tuple[str, str, str]) -> None:
        """Check registering an existing package tuple does not instantiate a new one."""
        with pytest.raises(NotFound):
            context.get_package_version(package_tuple)

        extras = ["postgresql"]

        package_version_registered = context.register_package_tuple(
            package_tuple, develop=True, extras=extras, os_name="fedora", os_version="31", python_version="3.7"
        )

        assert package_version_registered is not None

        package_version_another = context.register_package_tuple(
            package_tuple, develop=True, extras=extras, os_name="fedora", os_version="31", python_version="3.7"
        )

        assert package_version_registered is package_version_another, "Different instances returned"

    def test_note_dependencies(self, context: Context) -> None:
        """Test noting dependencies to the context."""
        dependency_tuple = ("tensorboard", "2.1.0", "https://pypi.org/simple")
        package_tuple = ("tensorflow", "2.0.0", "https://pypi.org/simple")

        context.register_package_version(
            PackageVersion(
                name=package_tuple[0], version="==" + package_tuple[1], index=Source(package_tuple[2]), develop=False,
            )
        )

        context.register_package_tuple(
            dependency_tuple,
            develop=True,
            extras=None,
            dependent_tuple=package_tuple,
            os_name="fedora",
            os_version="31",
            python_version="3.7",
        )

        package_version = context.get_package_version(package_tuple)
        assert package_version is not None
        assert package_version.name == package_tuple[0]
        assert package_version.locked_version == package_tuple[1]
        assert package_version.index.url == package_tuple[2]

        package_version = context.get_package_version(dependency_tuple)
        assert package_version is not None
        assert package_version.name == dependency_tuple[0]
        assert package_version.locked_version == dependency_tuple[1]
        assert package_version.index.url == dependency_tuple[2]

        assert package_tuple[0] in context.dependencies
        assert package_tuple in context.dependencies[package_tuple[0]]
        assert dependency_tuple in context.dependencies[package_tuple[0]][package_tuple]

        assert dependency_tuple[0] in context.dependents
        assert dependency_tuple in context.dependents[dependency_tuple[0]]
        entry = context.dependents[dependency_tuple[0]][dependency_tuple]
        assert entry == {(package_tuple, "fedora", "31", "3.7")}

        # By calling register_package_version we get a notion about direct dependency.
        assert package_tuple[0] in context.dependents
        assert package_tuple in context.dependents[package_tuple[0]]
        assert context.dependents[package_tuple[0]][package_tuple] == set()

    def test_is_dependency_monkey(self) -> None:
        """Test checking if the given context is an adviser context."""
        context = Context(
            project=None,
            graph=None,
            library_usage=None,
            limit=None,
            count=None,
            beam=None,
            recommendation_type=None,
            decision_type=DecisionType.ALL,
        )

        assert context.is_dependency_monkey() is True
        assert context.is_adviser() is False

    def test_is_adviser(self) -> None:
        """Test checking if the given context is an adviser context."""
        context = Context(
            project=None,
            graph=None,
            library_usage=None,
            limit=None,
            count=None,
            beam=None,
            recommendation_type=RecommendationType.LATEST,
            decision_type=None,
        )

        assert context.is_adviser() is True
        assert context.is_dependency_monkey() is False

    def test_invalid_context_no_type(self) -> None:
        """Exactly one type (recommendation/decision) has to be provided on instantiation."""
        with pytest.raises(ValueError):
            Context(
                project=None,
                graph=None,
                library_usage=None,
                limit=None,
                count=None,
                beam=None,
                # Decision type and recommendation type cannot be set to None at the same time.
                recommendation_type=None,
                decision_type=None,
            )

    def test_invalid_context_type(self) -> None:
        """Context type cannot capture both adviser and dependency monkey type."""
        with pytest.raises(ValueError):
            Context(
                project=None,
                graph=None,
                library_usage=None,
                limit=None,
                count=None,
                beam=None,
                # Decision type and recommendation type cannot be set at the same time.
                recommendation_type=RecommendationType.LATEST,
                decision_type=DecisionType.ALL,
            )
