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

from .base import AdviserTestCase


class TestResolver(AdviserTestCase):
    """Test resolution algorithm and its compatibility with Python ecosystem."""

    def test_run_boots(self) -> None:
        """Test running pipeline boots."""

    def test_run_sieves(self) -> None:
        """Test running pipeline sieves."""

    def test_run_steps(self) -> None:
        """Test running pipeline steps."""

    def test_run_strides(self) -> None:
        """Test running pipeline strides."""

    def test_run_wraps(self) -> None:
        """Test running pipeline wraps."""

    def test_resolve_direct_dependencies_single(self) -> None:
        """Test resolving a single direct dependency."""

    def test_resolve_direct_dependencies_multi(self) -> None:
        """Test resolving multiple direct dependencies."""

    def test_resolve_direct_dependencies_error(self) -> None:
        """Test resolving direct dependencies causes an error if not all direct dependencies are resolved."""

    def test_semver_sort_and_limit_latest_versions(self) -> None:
        pass

    def test_prepare_initial_state_single(self) -> None:
        """Test preparing initial state for ASA - a single package."""

    def test_prepare_initial_state_multi(self) -> None:
        """Test preparing initial state for ASA - multiple packages."""

    def test_expand_state(self) -> None:
        """Test expanding a states."""

    def test_resolve_states(self) -> None:
        """Resolve states."""

    def test_resolve_products(self) -> None:
        """Test resolving products."""

    def test_resolve(self) -> None:
        """Test resolution."""

    def test_get_adviser_instance(self) -> None:
        """Test getting a resolver for adviser."""

    def test_get_dependency_monkey_instance(self) -> None:
        """Test getting a resolver for dependency monkey."""
