#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019 Fridolin Pokorny
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

"""Test dependency graph construction and sorted stacks output."""

import pytest

from base import AdviserTestCase

from thoth.adviser.python.dependency_graph import DependencyGraphWalker
from thoth.adviser.python.dependency_graph import NoDependenciesError
from thoth.adviser.python.dependency_graph import DependenciesCountOverflow


class TestDependencyGraphWalking(AdviserTestCase):

    def test_no_dependency_error(self):
        """Test there is raised an exception if there are no dependencies specified."""
        with pytest.raises(NoDependenciesError):
            DependencyGraphWalker(direct_dependencies=[], paths=[])

    def test_too_many_dependencies_error(self):
        """Test there is raised an exception if there are no dependencies specified."""
        direct_dependencies = [
            ("flask", "1.0." + str(i), "https://pypi.org/simple")
            for i in range(DependencyGraphWalker.MAX_DEPENDENCIES_COUNT + 1)
        ]
        with pytest.raises(DependenciesCountOverflow):
            DependencyGraphWalker(direct_dependencies=direct_dependencies, paths=[])

    def test_one_direct(self):
        """Test a stack with just one direct dependency."""
        direct_dependencies = [
            ("numpy", "1.15.4", "https://pypi.org/simple"),
        ]
        expected_result = [direct_dependencies]

        dependency_graph = DependencyGraphWalker(
            direct_dependencies=direct_dependencies, paths=[]
        )
        walk_result = list(dependency_graph.walk())

        assert walk_result == expected_result

    def test_only_direct(self):
        """Test a stack with just direct dependencies - the returned values should be ordered correctly."""
        direct_dependencies = [
            ("numpy", "1.15.4", "https://pypi.org/simple"),
            ("numpy", "1.16.0", "https://pypi.org/simple"),
            ("numpy", "1.16.1", "https://pypi.org/simple"),
            ("numpy", "1.16.2", "https://pypi.org/simple"),
        ]
        expected_result = [
            [("numpy", "1.16.2", "https://pypi.org/simple")],
            [("numpy", "1.16.1", "https://pypi.org/simple")],
            [("numpy", "1.16.0", "https://pypi.org/simple")],
            [("numpy", "1.15.4", "https://pypi.org/simple")],
        ]
        dependency_graph = DependencyGraphWalker(
            direct_dependencies=direct_dependencies, paths=[]
        )
        walk_result = list(dependency_graph.walk())

        assert walk_result == expected_result

    def test_sorted_results_1(self):
        """Test a stack resolution with sorted dependencies - leaf ones."""
        direct_dependencies = [("flask", "0.12.3", "https://pypi.org/simple")]
        paths = [
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.9", "https://pypi.org/simple"),
                ("markupsafe", "1.1", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.9", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            ],
        ]
        dependency_graph = DependencyGraphWalker(
            direct_dependencies=direct_dependencies, paths=paths
        )

        walk_result = list(dependency_graph.walk())
        assert list(set(item) for item in walk_result) == list(
            reversed([set(item) for item in paths])
        )

    def test_sorted_results_duplicate(self):
        """Test removal of duplicates in direct dependencies and paths."""
        direct_dependencies = [
            ("flask", "0.12.3", "https://pypi.org/simple"),
            ("flask", "0.12.3", "https://pypi.org/simple"),
        ]
        paths = [
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            ],
        ]
        dependency_graph = DependencyGraphWalker(
            direct_dependencies=direct_dependencies, paths=paths
        )

        walk_result = list(dependency_graph.walk())
        assert len(walk_result) == 1
        assert set(walk_result[0]) == set(paths[0])

    def test_sorted_results_2(self):
        """Test resolution of stacks based with two separable paths."""
        direct_dependencies = [("flask", "0.12.3", "https://pypi.org/simple")]
        paths = [
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.1", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("werkzeug", "0.14.1", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("werkzeug", "0.14.2", "https://pypi.org/simple"),
            ],
        ]
        expected_result = [
            {
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.1", "https://pypi.org/simple"),
                ("werkzeug", "0.14.2", "https://pypi.org/simple"),
            },
            {
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
                ("werkzeug", "0.14.2", "https://pypi.org/simple"),
            },
            {
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.1", "https://pypi.org/simple"),
                ("werkzeug", "0.14.1", "https://pypi.org/simple"),
            },
            {
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
                ("werkzeug", "0.14.1", "https://pypi.org/simple"),
            },
        ]
        dependency_graph = DependencyGraphWalker(
            direct_dependencies=direct_dependencies, paths=paths
        )

        walk_result = list(set(item) for item in dependency_graph.walk())
        assert walk_result == expected_result

    def test_sorted_results_3(self):
        """Test sorting of results - multiple direct dependencies in different versions."""
        direct_dependencies = [
            ("flask", "0.12.2", "https://pypi.org/simple"),
            ("flask", "0.12.3", "https://pypi.org/simple"),
        ]
        paths = [
            [
                ("flask", "0.12.2", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.2", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.1", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.1", "https://pypi.org/simple"),
            ],
        ]
        expected_result = [
            {
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.1", "https://pypi.org/simple"),
            },
            {
                ("flask", "0.12.3", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            },
            {
                ("flask", "0.12.2", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.1", "https://pypi.org/simple"),
            },
            {
                ("flask", "0.12.2", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            },
        ]
        dependency_graph = DependencyGraphWalker(
            direct_dependencies=direct_dependencies, paths=paths
        )

        walk_result = list(set(item) for item in dependency_graph.walk())
        assert walk_result == expected_result

    def test_sorted_results_4(self):
        """Test resolution when leaf nodes are shared."""
        direct_dependencies = [("flask", "0.12.2", "https://pypi.org/simple")]
        paths = [
            [
                ("flask", "0.12.2", "https://pypi.org/simple"),
                ("jinja2", "2.7", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.2", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            ],
        ]
        expected_result = [
            {
                ("flask", "0.12.2", "https://pypi.org/simple"),
                ("jinja2", "2.8", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            },
            {
                ("flask", "0.12.2", "https://pypi.org/simple"),
                ("jinja2", "2.7", "https://pypi.org/simple"),
                ("markupsafe", "1.0", "https://pypi.org/simple"),
            },
        ]
        dependency_graph = DependencyGraphWalker(
            direct_dependencies=direct_dependencies, paths=paths
        )

        walk_result = list(set(item) for item in dependency_graph.walk())
        assert walk_result == expected_result
