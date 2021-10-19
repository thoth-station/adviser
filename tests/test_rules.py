#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""Tests related to filtering out Python packages that have rules assigned."""

from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import SolverRulesSieve
from thoth.adviser.context import Context
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.storages import GraphDatabase

from .base import AdviserUnitTestCase


class TestSolvedSieve(AdviserUnitTestCase):
    """Tests related to filtering out Python packages that have rules assigned."""

    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
flask = "*"
"""

    UNIT_TESTED = SolverRulesSieve

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)
        self.verify_multiple_should_include(builder_context)

    def test_no_rule(self, context: Context) -> None:
        """Test if no rule is configured for the given package."""
        package_version = PackageVersion(
            name="flask", version="==1.1.2", index=Source("https://pypi.org/simple"), develop=False
        )
        (
            GraphDatabase.should_receive("get_python_package_version_solver_rules_all")
            .with_args(
                "flask",
                "1.1.2",
                "https://pypi.org/simple",
            )
            .and_return([])
        )
        (
            GraphDatabase.should_receive("get_python_package_version_solver_rules_all")
            .with_args(
                "flask",
                "1.1.2",
            )
            .and_return([])
        )

        context.graph = GraphDatabase()

        assert not context.stack_info, "No stack info should be provided before test run"

        sieve = self.UNIT_TESTED()
        sieve.pre_run()

        with self.UNIT_TESTED.assigned_context(context):
            assert list(sieve.run(p for p in [package_version])) == [package_version]

        assert not context.stack_info, "No stack info should be provided by the pipeline unit"

    def test_rule(self, context: Context) -> None:
        """Test if a rule is assigned to a package."""
        package_version = PackageVersion(
            name="flask", version="==1.1.2", index=Source("https://pypi.org/simple"), develop=False
        )
        (
            GraphDatabase.should_receive("get_python_package_version_solver_rules_all")
            .with_args(
                "flask",
                "1.1.2",
                "https://pypi.org/simple",
            )
            .and_return([(1, "<2.0.0", None, "foo")])
        )
        (
            GraphDatabase.should_receive("get_python_package_version_solver_rules_all")
            .with_args(
                "flask",
                "1.1.2",
            )
            .and_return([(2, None, "https://pypi.org/simple", "bar")])
        )

        context.graph = GraphDatabase()

        assert not context.stack_info, "No stack info should be provided before test run"

        sieve = self.UNIT_TESTED()
        sieve.pre_run()

        with self.UNIT_TESTED.assigned_context(context):
            assert list(sieve.run(p for p in [package_version])) == []

        assert context.stack_info == [
            {
                "link": "https://thoth-station.ninja/j/rules",
                "message": "Removing package 'flask' in versions '<2.0.0' from all registered "
                "indexes based on rule: foo",
                "type": "WARNING",
            },
            {
                "link": "https://thoth-station.ninja/j/rules",
                "message": "Removing package 'flask' in all versions "
                "from index 'https://pypi.org/simple' based on rule: bar",
                "type": "WARNING",
            },
        ]
        assert self.verify_justification_schema(context.stack_info) is True
