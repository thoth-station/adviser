#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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

"""Test a boot to check for solved software environments."""

import pytest

from thoth.adviser.boots import SolvedSoftwareEnvironmentBoot
from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from ..base import AdviserUnitTestCase

from thoth.common import get_justification_link as jl


class TestSolvedSoftwareEnvironmentBoot(AdviserUnitTestCase):
    """Test solved software environment boot."""

    UNIT_TESTED = SolvedSoftwareEnvironmentBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project.runtime_environment.should_receive("is_fully_specified").with_args().and_return(True)
        self.verify_multiple_should_include(builder_context)

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit if supplied software environment is fully specified."""
        builder_context.project.runtime_environment.should_receive("is_fully_specified").with_args().and_return(
            True
        ).twice()
        assert list(SolvedSoftwareEnvironmentBoot.should_include(builder_context)) == [{}]
        builder_context.add_unit(SolvedSoftwareEnvironmentBoot())
        assert list(SolvedSoftwareEnvironmentBoot.should_include(builder_context)) == []

    def test_should_include_not_fully_specified(self, builder_context: PipelineBuilderContext) -> None:
        """Test not registering this unit if supplied software environment is not fully specified."""
        builder_context.project.runtime_environment.should_receive("is_fully_specified").with_args().and_return(
            False
        ).once()
        assert list(SolvedSoftwareEnvironmentBoot.should_include(builder_context)) == []

    def test_run(self, context: Context) -> None:
        """Test if the given software environment is solved."""
        context.project.runtime_environment.operating_system.name = "fedora"
        context.project.runtime_environment.operating_system.version = "32"
        context.project.runtime_environment.python_version = "3.8"
        context.graph.should_receive("solved_software_environment_exists").with_args(
            os_name="fedora", os_version="32", python_version="3.8"
        ).and_return(True).once()

        assert not context.stack_info

        unit = SolvedSoftwareEnvironmentBoot()
        with unit.assigned_context(context):
            assert unit.run() is None

        assert not context.stack_info, "No stack information should be supplied"

    def test_run_error(self, context: Context) -> None:
        """Test raising no exception raised if the given software environment is not solved."""
        context.project.runtime_environment.operating_system.name = "fedora"
        context.project.runtime_environment.operating_system.version = "32"
        context.project.runtime_environment.python_version = "3.8"
        context.graph.should_receive("solved_software_environment_exists").with_args(
            os_name="fedora", os_version="32", python_version="3.8"
        ).and_return(False).once()

        assert not context.stack_info

        solvers_configured = SolvedSoftwareEnvironmentBoot._THOTH_ADVISER_DEPLOYMENT_CONFIGURED_SOLVERS
        try:
            SolvedSoftwareEnvironmentBoot._THOTH_ADVISER_DEPLOYMENT_CONFIGURED_SOLVERS = "\nsolver-ubi-8-py39\n"
            unit = SolvedSoftwareEnvironmentBoot()
            with pytest.raises(NotAcceptable):
                with unit.assigned_context(context):
                    unit.run()
        finally:
            SolvedSoftwareEnvironmentBoot._THOTH_ADVISER_DEPLOYMENT_CONFIGURED_SOLVERS = solvers_configured

        assert context.stack_info == [
            {
                "type": "ERROR",
                "message": "No observations found for 'fedora' in version '32' using Python '3.8'",
                "link": jl("solved_sw_env"),
            },
            {
                "message": "Consider using 'ubi' in version '8' with Python 3.9",
                "type": "ERROR",
                "link": jl("solved_sw_env"),
            },
        ]
