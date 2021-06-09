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

"""Test notifying about runtime environments not supported by solvers enabled in a deployment."""

from thoth.adviser.boots import SolversConfiguredBoot
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.common import get_justification_link as jl

from ..base import AdviserUnitTestCase


class TestFullySpecifiedEnvironment(AdviserUnitTestCase):
    """Test notifying about runtime environments not supported by solvers enabled in a deployment."""

    UNIT_TESTED = SolversConfiguredBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.project.runtime_environment.operating_system.name = "rhel"
        builder_context.project.runtime_environment.operating_system.version = "8"
        builder_context.project.runtime_environment.python_version = "3.8"

        try:
            self.UNIT_TESTED._SOLVERS_CONFIGURED = "\n\nsolver-fedora-31-py36\n\n"
            self.verify_multiple_should_include(builder_context)
        finally:
            self.UNIT_TESTED._SOLVERS_CONFIGURED = None

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit for adviser runs."""
        builder_context.project.runtime_environment.operating_system.name = "rhel"
        builder_context.project.runtime_environment.operating_system.version = "8"
        builder_context.project.runtime_environment.python_version = "3.8"

        try:
            self.UNIT_TESTED._SOLVERS_CONFIGURED = "\n\nsolver-fedora-31-py36\n\n"
            assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]
        finally:
            self.UNIT_TESTED._SOLVERS_CONFIGURED = None

    def test_should_include_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test not registering the pipeline unit."""
        builder_context.project.runtime_environment.operating_system.name = "rhel"
        builder_context.project.runtime_environment.operating_system.version = "8"
        builder_context.project.runtime_environment.python_version = "3.8"

        try:
            self.UNIT_TESTED._SOLVERS_CONFIGURED = """
                solver-fedora-31-py36\n
                solver-rhel-8-py36\n\n\n
            """
            assert list(self.UNIT_TESTED.should_include(builder_context)) == []
        finally:
            self.UNIT_TESTED._SOLVERS_CONFIGURED = None

    def test_run(self, context: Context) -> None:
        """Test if the pipeline unit properly notifies users.."""
        assert not context.stack_info

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            assert unit.run() is None

        assert context.stack_info == [
            {
                "link": jl("eol_env"),
                "message": "Runtime environment used is no longer supported, it is "
                "recommended to switch to another runtime environment",
                "type": "WARNING",
            },
        ]
