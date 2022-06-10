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

"""Test a boot that notifies about labels used."""

from thoth.common import get_justification_link as jl

from thoth.adviser.boots import LabelsBoot
from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from ..base import AdviserUnitTestCase


class TestLabelsBoot(AdviserUnitTestCase):
    """Test a boot that notifies about labels used."""

    UNIT_TESTED = LabelsBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project.runtime_environment.should_receive("is_fully_specified").with_args().and_return(True)
        builder_context.labels = {"foo": "bar"}
        self.verify_multiple_should_include(builder_context)

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit if labels are used."""
        builder_context.labels = {"foo": "bar"}
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]
        builder_context.add_unit(self.UNIT_TESTED())
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_should_include_no_labels(self, builder_context: PipelineBuilderContext) -> None:
        """Test not registering this unit if supplied software environment is not fully specified."""
        assert not builder_context.labels
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_run(self, context: Context) -> None:
        """Test if the given software environment is solved."""
        context.labels = {"foo": "bar", "baz": "qux", "allow-cve": "pysec-2014-10,PYSEC-2014-22"}

        assert not context.stack_info

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            assert unit.run() is None

        assert context.stack_info == [
            {"link": jl("labels"), "message": "Considering label foo=bar in the resolution process", "type": "INFO"},
            {"link": jl("labels"), "message": "Considering label baz=qux in the resolution process", "type": "INFO"},
            {
                "link": jl("allow_cve"),
                "message": "Allowing CVE 'PYSEC-2014-10' to be present in the application",
                "type": "WARNING",
            },
            {
                "link": jl("allow_cve"),
                "message": "Allowing CVE 'PYSEC-2014-22' to be present in the application",
                "type": "WARNING",
            },
        ]
