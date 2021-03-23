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

"""Test boot adding information about Thoth s2i."""

import pytest
from typing import Optional

from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.boots import ThothS2IInfoBoot

from ..base import AdviserUnitTestCase


class TestThothS2IBoot(AdviserUnitTestCase):
    """Test adding information about Thoth s2i."""

    UNIT_TESTED = ThothS2IInfoBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38:v0.23.0"
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize("base_image", [None, "fedora:33", "quay.io/thoth-station/solver-ubi8-py38:v0.23.0"])
    def test_no_include(self, base_image: Optional[str], builder_context: PipelineBuilderContext) -> None:
        """Test not including the pipeline unit."""
        builder_context.project.runtime_environment.base_image = base_image
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_run(self, context: Context) -> None:
        """Test running and recommending to use Thoth's s2i base image."""
        assert not context.stack_info

        unit = self.UNIT_TESTED()
        justification = {
            "type": "INFO",
            "message": "foo",
            "link": "https://bar.baz/",
        }
        unit.update_configuration(justification)

        with self.UNIT_TESTED.assigned_context(context):
            assert unit.run() is None

        assert len(context.stack_info) == 1
        self.verify_justification_schema(context.stack_info)

    def test_default_configuration(self) -> None:
        """Test default configuration of dropout pipeline step."""
        assert self.UNIT_TESTED.CONFIGURATION_DEFAULT == {
            "message": None,
            "link": None,
            "type": "INFO",
        }
