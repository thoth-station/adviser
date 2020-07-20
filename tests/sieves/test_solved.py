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

"""Tests related to filtering out unsolved packages and packages with build-time error (installation issues)."""

import flexmock
from typing import Tuple

from thoth.adviser.sieves import SolvedSieve
from thoth.common import RuntimeEnvironment
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.python import Project
from thoth.storages import GraphDatabase
from thoth.storages.exceptions import NotFoundError

from ..base import AdviserTestCase


class TestSolvedSieve(AdviserTestCase):
    """Test removing dependencies based on information coming from Thoth's solver capturing installation issues."""

    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"
"""

    def _get_case(self) -> Tuple[PackageVersion, Project]:
        """Get all the objects needed for a test case for this sieve."""
        project = Project.from_strings(self._CASE_PIPFILE)
        flexmock(GraphDatabase)
        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://pypi.org/simple"), develop=False,
        )
        return package_version, project

    def test_not_found(self) -> None:
        """Test a not found package is not accepted by sieve."""
        package_version, project = self._get_case()
        (
            GraphDatabase.should_receive("has_python_solver_error")
            .with_args(
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
                os_name=None,
                os_version=None,
                python_version=None,
            )
            .and_raise(NotFoundError)
            .once()
        )

        context = flexmock(
            graph=GraphDatabase(), project=flexmock(runtime_environment=RuntimeEnvironment.from_dict({})),
        )
        with SolvedSieve.assigned_context(context):
            sieve = SolvedSieve()
            assert list(sieve.run(p for p in [package_version])) == []

    def test_not_solved_without_error(self) -> None:
        """Test a not found package is not accepted by sieve."""
        package_version, project = self._get_case()
        (
            GraphDatabase.should_receive("has_python_solver_error")
            .with_args(
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
                os_name=None,
                os_version=None,
                python_version=None,
            )
            .and_return(True)
            .once()
        )

        context = flexmock(
            graph=GraphDatabase(), project=flexmock(runtime_environment=RuntimeEnvironment.from_dict({})),
        )
        with SolvedSieve.assigned_context(context):
            sieve = SolvedSieve()
            assert list(sieve.run(p for p in [package_version])) == []

    def test_acceptable_with_error(self) -> None:
        """Test accepted with an error."""
        package_version, project = self._get_case()
        (
            GraphDatabase.should_receive("has_python_solver_error")
            .with_args(
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
                os_name=None,
                os_version=None,
                python_version=None,
            )
            .and_return(True)
            .once()
        )

        context = flexmock(
            graph=GraphDatabase(), project=flexmock(runtime_environment=RuntimeEnvironment.from_dict({})),
        )
        with SolvedSieve.assigned_context(context):
            sieve = SolvedSieve()
            sieve.update_configuration({"without_error": False})
            assert list(sieve.run(p for p in [package_version])) == [package_version]

    def test_default_configuration(self) -> None:
        """Test default configuration for an instantiated sieve."""
        sieve = SolvedSieve()
        assert sieve.configuration == {"without_error": True}
