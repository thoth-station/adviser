#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.boots import SolvedSoftwareEnvironmentBoot
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from ..base import AdviserTestCase


class TestSolvedSoftwareEnvironmentBoot(AdviserTestCase):
    """Test solved software environment boot."""

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit if supplied software environment is fully specified."""
        builder_context.project.runtime_environment.should_receive("is_fully_specified").with_args().and_return(
            True
        ).twice()
        assert SolvedSoftwareEnvironmentBoot.should_include(builder_context) == {}
        builder_context.add_unit(SolvedSoftwareEnvironmentBoot())
        assert SolvedSoftwareEnvironmentBoot.should_include(builder_context) is None

    def test_should_include_not_fully_specified(self, builder_context: PipelineBuilderContext) -> None:
        """Test not registering this unit if supplied software environment is not fully specified."""
        builder_context.project.runtime_environment.should_receive("is_fully_specified").with_args().and_return(
            False
        ).once()
        assert SolvedSoftwareEnvironmentBoot.should_include(builder_context) is None

    def test_run(self, context: Context) -> None:
        """Test if the given software environment is solved."""
        context.project.runtime_environment.operating_system.name = "fedora"
        context.project.runtime_environment.operating_system.version = "32"
        context.project.runtime_environment.python_version = "3.8"
        context.graph.should_receive("solved_software_environment_exists").with_args(
            os_name="fedora", os_version="32", python_version="3.8"
        ).and_return(True).once()

        unit = SolvedSoftwareEnvironmentBoot()
        with unit.assigned_context(context):
            assert unit.run() is None

    def test_run_error(self, context: Context) -> None:
        """Test raising no exception raised if the given software environment is not solved."""
        context.project.runtime_environment.operating_system.name = "fedora"
        context.project.runtime_environment.operating_system.version = "32"
        context.project.runtime_environment.python_version = "3.8"
        context.graph.should_receive("solved_software_environment_exists").with_args(
            os_name="fedora", os_version="32", python_version="3.8"
        ).and_return(False).once()
        context.graph.should_receive(
            "get_solved_python_package_versions_software_environment_all"
        ).with_args().and_return(
            [
                {"os_name": "rhel", "os_version": "9.0", "python_version": "3.8"},
                {"os_name": "fedora", "os_version": "31", "python_version": "3.7"},
            ]
        ).once()

        unit = SolvedSoftwareEnvironmentBoot()
        with pytest.raises(NotAcceptable):
            with unit.assigned_context(context):
                unit.run()
