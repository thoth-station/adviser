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

"""Tests related to filtering out unsolved packages and packages with build-time error (installation issues)."""

from flexmock import flexmock
from typing import Tuple

from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import SolvedSieve
from thoth.adviser.context import Context
from thoth.common import get_justification_link as jl
from thoth.common import RuntimeEnvironment
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.python import Project
from thoth.storages import GraphDatabase
from thoth.storages.exceptions import NotFoundError

from ..base import AdviserUnitTestCase


class TestSolvedSieve(AdviserUnitTestCase):
    """Test removing dependencies based on information coming from Thoth's solver capturing installation issues."""

    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"
"""

    UNIT_TESTED = SolvedSieve

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)
        self.verify_multiple_should_include(builder_context)

    def _get_case(self) -> Tuple[PackageVersion, Project]:
        """Get all the objects needed for a test case for this sieve."""
        project = Project.from_strings(self._CASE_PIPFILE)
        flexmock(GraphDatabase)
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
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
            graph=GraphDatabase(),
            project=flexmock(runtime_environment=RuntimeEnvironment.from_dict({})),
        )
        with SolvedSieve.assigned_context(context):
            sieve = SolvedSieve()
            assert list(sieve.run(p for p in [package_version])) == []

    def test_not_solved_without_error(self, context: Context) -> None:
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

        context.graph = GraphDatabase()
        context.project = flexmock(runtime_environment=RuntimeEnvironment.from_dict({}))

        assert not context.stack_info, "No stack info should be provided before test run"

        sieve = SolvedSieve()
        sieve.pre_run()

        with SolvedSieve.assigned_context(context):
            assert list(sieve.run(p for p in [package_version])) == []
            sieve.post_run()

        assert context.stack_info, "No stack info provided by the pipeline unit"
        assert context.stack_info == [
            {
                "link": jl("install_error"),
                "message": "The following versions of 'tensorflow' from "
                "'https://pypi.org/simple' were removed due to installation "
                "issues in the target environment: 2.0.0",
                "type": "WARNING",
            }
        ]

        assert self.verify_justification_schema(context.stack_info) is True

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
            graph=GraphDatabase(),
            project=flexmock(runtime_environment=RuntimeEnvironment.from_dict({})),
        )
        with SolvedSieve.assigned_context(context):
            sieve = SolvedSieve()
            sieve.update_configuration({"without_error": False})
            assert list(sieve.run(p for p in [package_version])) == [package_version]

    def test_default_configuration(self) -> None:
        """Test default configuration for an instantiated sieve."""
        sieve = SolvedSieve()
        assert sieve.configuration == {"without_error": True, "package_name": None}
