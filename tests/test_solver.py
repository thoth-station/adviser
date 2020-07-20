#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019, 2020 Fridolin Pokorny
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

"""Test solver implementation on top Thoth's knowledge graph."""

import pytest

from thoth.adviser.solver import PythonGraphSolver
from thoth.adviser.solver import PythonPackageGraphSolver
from thoth.adviser.solver import GraphReleasesFetcher
from thoth.adviser.solver import PackageVersionDependencyParser
from thoth.python import PackageVersion
from thoth.solver.python.base import SolverException

from .base import AdviserTestCase
from .graph_mock import MockedGraphDatabase


class TestSolver(AdviserTestCase):
    """Test Thoth's solver implementation on top of Thoth's knowledge graph."""

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_raises(self, graph: MockedGraphDatabase) -> None:
        """Check that there is raised an exception if no releases were found."""
        with pytest.raises(SolverException):
            PythonGraphSolver(
                dependency_parser=PackageVersionDependencyParser(), releases_fetcher=GraphReleasesFetcher(graph=graph),
            ).solve(
                [PackageVersion(name="nonexisting-foo", version="==1.0.0", index=None, develop=False,)], graceful=False,
            )

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0(self, graph: MockedGraphDatabase) -> None:
        """Check that resolving can gather all versions available in the graph database."""
        resolved = PythonGraphSolver(
            dependency_parser=PackageVersionDependencyParser(), releases_fetcher=GraphReleasesFetcher(graph=graph),
        ).solve([PackageVersion(name="a", version="*", index=None, develop=False)], graceful=False,)
        assert len(resolved) == 1
        assert "a" in resolved
        assert set(resolved["a"]) == {
            ("1.0.0", "index1"),
            ("1.1.0", "index1"),
            ("1.2.0", "index2"),
        }

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_multiple(self, graph: MockedGraphDatabase) -> None:
        """Check that resolving can resolve multiple Python packages."""
        resolved = PythonGraphSolver(
            dependency_parser=PackageVersionDependencyParser(), releases_fetcher=GraphReleasesFetcher(graph=graph),
        ).solve(
            [
                PackageVersion(name="a", version="*", index=None, develop=False),
                PackageVersion(name="b", version=">1.0.0", index=None, develop=False),
            ],
            graceful=False,
        )

        assert len(resolved) == 2

        assert "a" in resolved
        assert set(resolved["a"]) == {
            ("1.0.0", "index1"),
            ("1.1.0", "index1"),
            ("1.2.0", "index2"),
        }

        assert "b" in resolved
        assert set(resolved["b"]) == {("2.0.0", "index1"), ("3.0.0", "index2")}

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_package_raises(self, graph: MockedGraphDatabase) -> None:
        """Check that there is raised an exception if no releases were found."""
        with pytest.raises(SolverException):
            PythonPackageGraphSolver(graph=graph).solve(
                [PackageVersion(name="nonexisting-foo", version="==1.0.0", index=None, develop=False,)], graceful=False,
            )

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_all_package_versions(self, graph: MockedGraphDatabase) -> None:
        """Check that resolving can gather all versions available in the graph database."""
        resolved = PythonPackageGraphSolver(graph=graph).solve(
            [PackageVersion(name="a", version="*", index=None, develop=False)], graceful=False,
        )

        assert len(resolved) == 1
        assert "a" in resolved
        # 1.0.0, 1.1.0, 1.2.0
        assert len(resolved["a"]) == 3

        assert all(package_version.name == "a" for package_version in resolved["a"])
        assert set(package_version.version for package_version in resolved["a"]) == {
            "==1.0.0",
            "==1.1.0",
            "==1.2.0",
        }

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_package_multiple(self, graph: MockedGraphDatabase) -> None:
        """Check that resolving can resolve multiple Python packages."""
        resolved = PythonPackageGraphSolver(graph=graph).solve(
            [
                PackageVersion(name="a", version="*", index=None, develop=False),
                PackageVersion(name="b", version=">1.0.0", index=None, develop=False),
            ],
            graceful=False,
        )
        assert len(resolved) == 2
        assert "a" in resolved
        assert "b" in resolved

        assert all(package_version.name == "a" for package_version in resolved["a"])
        assert all(package_version.name == "b" for package_version in resolved["b"])
        assert set(package_version.version for package_version in resolved["a"]) == {
            "==1.0.0",
            "==1.1.0",
            "==1.2.0",
        }
        assert set(package_version.version for package_version in resolved["b"]) == {
            "==2.0.0",
            "==3.0.0",
        }

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_multiple_times_error(self, graph: MockedGraphDatabase) -> None:
        """Check that resolving can resolve multiple Python packages."""
        from thoth.solver.python.base import SolverException

        with pytest.raises(SolverException):
            PythonPackageGraphSolver(graph=graph).solve(
                [
                    PackageVersion(name="a", version="<=1.2.0", index=None, develop=False),
                    PackageVersion(name="a", version=">1.0.0", index=None, develop=False),
                ],
                graceful=False,
            )
