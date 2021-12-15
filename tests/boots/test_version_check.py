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

"""Test version checking boot."""

from thoth.adviser.boots import VersionCheckBoot
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.enums import RecommendationType
from thoth.common import get_justification_link as jl

from ..base import AdviserUnitTestCase


class TestVersionCheckBoot(AdviserUnitTestCase):
    """A boot that checks if versions are too lax."""

    UNIT_TESTED = VersionCheckBoot

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)
        self.verify_multiple_should_include(builder_context)

    def test_no_version(self, context: Context) -> None:
        """Test providing stack information if there is no version identifier."""
        context.project.pipfile.packages.packages.clear()
        context.project.pipfile.dev_packages.packages.clear()

        context.project.add_package("flask")
        assert not context.stack_info

        boot = self.UNIT_TESTED()
        with boot.assigned_context(context):
            boot.run()

        assert context.stack_info == [
            {
                "link": jl("lax_version"),
                "message": "No version range specifier for 'flask' found, it is recommended to "
                "specify version ranges in requirements",
                "type": "WARNING",
            },
        ]

    def test_lax_version(self, context: Context) -> None:
        """Test providing stack information if the used version is too lax."""
        context.project.pipfile.packages.packages.clear()
        context.project.pipfile.dev_packages.packages.clear()

        context.project.add_package("flask", ">=0.12")
        assert not context.stack_info

        boot = self.UNIT_TESTED()
        with boot.assigned_context(context):
            boot.run()

        assert context.stack_info == [
            {
                "link": jl("lax_version"),
                "message": "Version range specifier ('>=0.12') for 'flask' might be too lax",
                "type": "WARNING",
            },
        ]

    def test_version_ok(self, context: Context) -> None:
        """Test not providing stack information if the used version is okay."""
        context.project.pipfile.packages.packages.clear()
        context.project.pipfile.dev_packages.packages.clear()

        context.project.add_package("flask", ">=0.12,<2.0.0")
        assert not context.stack_info

        boot = self.UNIT_TESTED()
        with boot.assigned_context(context):
            boot.run()

        assert context.stack_info == []
