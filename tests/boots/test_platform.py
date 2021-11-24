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

"""Test handling checks of supported platforms."""

import pytest

from thoth.adviser.boots import PlatformBoot
from thoth.adviser.context import Context
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.common import get_justification_link as jl
from ..base import AdviserUnitTestCase


class TestPlatformBoot(AdviserUnitTestCase):
    """Test platform boot."""

    UNIT_TESTED = PlatformBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.project.runtime_environment.platform = "aarch64"
        self.verify_multiple_should_include(builder_context)

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit."""
        builder_context.should_receive("is_included").and_return(False)
        builder_context.project.runtime_environment.platform = "aarch64"
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

        builder_context.should_receive("is_included").and_return(True)
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_not_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including the pipeline unit when supported platforms are used."""
        builder_context.should_receive("is_included").and_return(False)
        builder_context.project.runtime_environment.platform = "linux-x86_64"
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_not_acceptable(self, context: Context) -> None:
        """Test raising an exception when the pipeline unit is included."""
        unit = self.UNIT_TESTED()

        context.project.runtime_environment.platform = "aarch64"

        assert not context.stack_info

        # The unit always raises, no need to explicitly assign platform here.
        with unit.assigned_context(context):
            with pytest.raises(
                NotAcceptable, match="Platform 'aarch64' is not supported, possible platforms are: linux-x86_64"
            ):
                unit.run()

        assert self.verify_justification_schema(context.stack_info)
        assert context.stack_info == [
            {
                "link": jl("platform"),
                "message": "Platform 'aarch64' is not supported, possible platforms are: " "linux-x86_64",
                "type": "ERROR",
            },
        ]
