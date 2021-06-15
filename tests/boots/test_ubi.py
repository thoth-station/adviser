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

"""Test UBI to RHEL mapping boot."""

from thoth.adviser.boots import UbiBoot
from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.python import Project

from ..base import AdviserUnitTestCase


class TestUbiBoot(AdviserUnitTestCase):
    """Test UBI to RHEL mapping boot."""

    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"
"""

    UNIT_TESTED = UbiBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project.runtime_environment.operating_system.name = "ubi"
        self.verify_multiple_should_include(builder_context)

    def test_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including this pipeline unit."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project.runtime_environment.operating_system.name = "fedora"
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_run(self, context: Context) -> None:
        """Test remapping UBI to RHEL."""
        context.project = Project.from_strings(self._CASE_PIPFILE)
        context.project.runtime_environment.operating_system.name = "ubi"

        boot = UbiBoot()
        with UbiBoot.assigned_context(context):
            boot.run()

        assert context.project.runtime_environment.operating_system.name == "rhel"
        assert context.stack_info, "No stack info provided"
        assert self.verify_justification_schema(context.stack_info) is True
