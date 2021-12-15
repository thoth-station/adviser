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

"""Test a boot that provides a link to Thoth Search UI."""

import random

from thoth.adviser.boots import ThothSearchBoot
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from ..base import AdviserUnitTestCase


class TestThothSearchBoot(AdviserUnitTestCase):
    """Test a boot that provides a link to Thoth Search UI."""

    UNIT_TESTED = ThothSearchBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.verify_multiple_should_include(builder_context)

    def test_run(self, context: Context) -> None:
        """Test propagating a link to Thoth Search UI."""
        assert not context.stack_info

        document_id = f"adviser-foo-bar-{random.randint(0, 1000)}"
        search_url = "https://thoth-station.ninja/some/nice/url/to/search/{document_id}/summary/link"

        unit = self.UNIT_TESTED(document_id=document_id, search_url=search_url)
        with unit.assigned_context(context):
            assert unit.run() is None

        expected_link = search_url.format(document_id=document_id)
        assert context.stack_info == [
            {
                "type": "INFO",
                "message": "Results can be browsed in Thoth search",
                "link": expected_link,
            }
        ]
