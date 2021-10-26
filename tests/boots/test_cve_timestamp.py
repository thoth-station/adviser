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

"""A boot to provide information about the last CVE update."""

import pytest

from datetime import datetime
from datetime import timedelta

from thoth.adviser.boots import CveTimestampBoot
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.enums import RecommendationType
from thoth.common import datetime2datetime_str
from thoth.common import get_justification_link as jl
from ..base import AdviserUnitTestCase


class TestCveTimestampBoot(AdviserUnitTestCase):
    """Test providing information about the last CVE update."""

    UNIT_TESTED = CveTimestampBoot

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)
        self.verify_multiple_should_include(builder_context)

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit for adviser runs."""
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

        builder_context.add_unit(self.UNIT_TESTED())

        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    @pytest.mark.parametrize(
        "timestamp,type_severity",
        [(datetime.utcnow() - timedelta(days=1), "INFO"), (datetime.utcnow() - timedelta(days=1000), "WARNING")],
    )
    def test_run_info(self, context: Context, timestamp: datetime, type_severity: str) -> None:
        """Test providing CVE update timestamp to users."""
        context.graph.should_receive("get_cve_timestamp").and_return(timestamp).once()
        unit = self.UNIT_TESTED()

        assert not context.stack_info
        with unit.assigned_context(context):
            unit.run()

        assert len(context.stack_info) == 1
        assert set(context.stack_info[0]) == {"link", "message", "type"}
        assert self.verify_justification_schema(context.stack_info)
        assert context.stack_info[0]["link"] == jl("cve_timestamp")
        assert (
            context.stack_info[0]["message"] == f"CVE database of known vulnerabilities for Python packages "
            f"was updated at {datetime2datetime_str(timestamp)!r}"
        )
        assert context.stack_info[0]["type"] == type_severity

    def test_run_no_cve_timestamp(self, context: Context) -> None:
        """Test warning if CVE timestamp is not recorded in the database."""
        context.graph.should_receive("get_cve_timestamp").and_return(None).once()
        unit = self.UNIT_TESTED()

        assert not context.stack_info
        with unit.assigned_context(context):
            unit.run()

        assert len(context.stack_info) == 1
        assert set(context.stack_info[0]) == {"link", "message", "type"}
        assert self.verify_justification_schema(context.stack_info)
        assert context.stack_info[0] == {
            "link": jl("no_cve_timestamp"),
            "message": "No CVE timestamp information found in the database",
            "type": "WARNING",
        }
