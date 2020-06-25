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

"""Test handling of platform information."""

import pytest

from thoth.adviser.boots import PlatformBoot
from thoth.adviser.context import Context
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from ..base import AdviserTestCase


class TestPlatformBoot(AdviserTestCase):
    """Test platform boot."""

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit."""
        builder_context.should_receive("is_included").and_return(False)
        assert PlatformBoot.should_include(builder_context) == {}

        builder_context.should_receive("is_included").and_return(True)
        assert PlatformBoot.should_include(builder_context) is None

    def test_adjust(self, context: Context) -> None:
        """Test adjusting the runtime environment to a default if not provided explicitly."""
        default_platform = "linux-x86_64"
        context.project.runtime_environment.platform = None
        context.graph.should_receive("python_package_version_depends_on_platform_exists").with_args(
            default_platform
        ).and_return(True).once()

        unit = PlatformBoot()
        with unit.assigned_context(context):
            assert unit.run() is None

        assert context.project.runtime_environment.platform == default_platform

    def test_no_platform(self, context: Context) -> None:
        """Test raising an exception if the given platform was not found in the database."""
        platform = "foo-bar"
        context.project.runtime_environment.platform = platform
        context.graph.should_receive("python_package_version_depends_on_platform_exists").with_args(
            platform
        ).and_return(False).once()

        unit = PlatformBoot()
        with unit.assigned_context(context):
            with pytest.raises(NotAcceptable, match="No platform conforming to 'foo-bar' found in the database"):
                unit.run()

    def test_no_adjust(self, context: Context) -> None:
        """Test no adjustment if the runtime environment provides platform info."""
        platform = "linux-i586"
        context.project.runtime_environment.platform = platform
        context.graph.should_receive("python_package_version_depends_on_platform_exists").with_args(
            platform
        ).and_return(True).once()

        unit = PlatformBoot()
        with unit.assigned_context(context):
            assert unit.run() is None

        assert context.project.runtime_environment.platform == platform
