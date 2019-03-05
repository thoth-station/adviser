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

import pytest

from thoth.adviser.python import PythonGraphSolver
from thoth.adviser.python import PythonPackageGraphSolver
from thoth.python import PackageVersion
from thoth.solver.python.base import SolverException
from graph_mock import MockedGraphDatabase

from base import AdviserTestCase


class TestSolver(AdviserTestCase):
    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_raises(self, graph):
        """Check that there is raised an exception if no releases were found."""
        with pytest.raises(SolverException):
            PythonGraphSolver(graph_db=graph).solve(
                [
                    PackageVersion(
                        name="nonexisting-foo",
                        version="==1.0.0",
                        index=None,
                        develop=False,
                    )
                ],
                graceful=False,
            )

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_latest(self, graph):
        """Check that resolving gets always the latest version (relying on internal python logic)."""
        assert PythonGraphSolver(graph_db=graph).solve(
            [PackageVersion(name="a", version="*", index=None, develop=False)],
            graceful=False,
        ) == {"a": ("1.2.0", "index2")}

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_all_versions(self, graph):
        """Check that resolving can gather all versions available in the graph database."""
        resolved = PythonGraphSolver(graph_db=graph).solve(
            [PackageVersion(name="a", version="*", index=None, develop=False)],
            graceful=False,
            all_versions=True,
        )
        assert len(resolved) == 1
        assert "a" in resolved
        assert resolved == {
            "a": [("1.0.0", "index1"), ("1.1.0", "index1"), ("1.2.0", "index2")]
        }

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_multiple(self, graph):
        """Check that resolving can resolve multiple Python packages."""
        resolved = PythonGraphSolver(graph_db=graph).solve(
            [
                PackageVersion(name="a", version="*", index=None, develop=False),
                PackageVersion(name="b", version=">1.0.0", index=None, develop=False),
            ],
            graceful=False,
            all_versions=True,
        )
        assert len(resolved) == 2
        assert resolved == {
            "a": [("1.0.0", "index1"), ("1.1.0", "index1"), ("1.2.0", "index2")],
            "b": [("2.0.0", "index1"), ("3.0.0", "index2")],
        }

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_package_raises(self, graph):
        """Check that there is raised an exception if no releases were found."""
        with pytest.raises(SolverException):
            PythonPackageGraphSolver(graph_db=graph).solve(
                [
                    PackageVersion(
                        name="nonexisting-foo",
                        version="==1.0.0",
                        index=None,
                        develop=False,
                    )
                ],
                graceful=False,
            )

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_package_latest(self, graph):
        """Check that resolving gets always the latest version (relying on internal python logic)."""
        resolved = PythonPackageGraphSolver(graph_db=graph).solve(
            [PackageVersion(name="a", version="*", index=None, develop=False)],
            graceful=False,
        )
        assert len(resolved) == 1
        assert resolved["a"][0].name == "a"
        assert resolved["a"][0].version == "==1.2.0"

    @pytest.mark.parametrize("graph", [MockedGraphDatabase("db_0.yaml")])
    def test_db_0_all_package_versions(self, graph):
        """Check that resolving can gather all versions available in the graph database."""
        resolved = PythonPackageGraphSolver(graph_db=graph).solve(
            [PackageVersion(name="a", version="*", index=None, develop=False)],
            graceful=False,
            all_versions=True,
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
    def test_db_0_package_multiple(self, graph):
        """Check that resolving can resolve multiple Python packages."""
        resolved = PythonPackageGraphSolver(graph_db=graph).solve(
            [
                PackageVersion(name="a", version="*", index=None, develop=False),
                PackageVersion(name="b", version=">1.0.0", index=None, develop=False),
            ],
            graceful=False,
            all_versions=True,
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
    def test_db_0_multiple_times_error(self, graph):
        """Check that resolving can resolve multiple Python packages."""
        from thoth.solver.python.base import SolverException

        with pytest.raises(SolverException):
            PythonPackageGraphSolver(graph_db=graph).solve(
                [
                    PackageVersion(
                        name="a", version="<=1.2.0", index=None, develop=False
                    ),
                    PackageVersion(
                        name="a", version=">1.0.0", index=None, develop=False
                    ),
                ],
                graceful=False,
                all_versions=True,
            )
