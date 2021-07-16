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

"""Test adding information about prescription release."""

from thoth.adviser.boots import PrescriptionReleaseBoot
from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.prescription import Prescription

from ..base import AdviserUnitTestCase


class TestPrescriptionReleaseBoot(AdviserUnitTestCase):
    """Test adding information about prescription release."""

    UNIT_TESTED = PrescriptionReleaseBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        prescription_path = str(self.data_dir / "prescriptions")
        builder_context.prescription = Prescription.load(prescription_path)
        self.verify_multiple_should_include(builder_context)

    def test_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including this pipeline unit."""
        builder_context.prescription = None
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test including this pipeline unit."""
        prescription_path = str(self.data_dir / "prescriptions")
        builder_context.prescription = Prescription.load(prescription_path)
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

    def test_run(self, context: Context) -> None:
        """Test remapping UBI to RHEL."""
        assert not context.stack_info

        prescription_path = str(self.data_dir / "prescriptions")
        context.prescription = Prescription.load(prescription_path)

        unit = self.UNIT_TESTED()
        unit.pre_run()
        with self.UNIT_TESTED.assigned_context(context):
            unit.run()

        assert context.stack_info, "No stack info provided"
        assert len(context.stack_info) == 1
        assert context.stack_info[0]["type"] == "INFO"
        assert context.stack_info[0]["message"] == "Using prescriptions 'thoth' release '2021.06.15.dev'"
        assert self.verify_justification_schema(context.stack_info) is True
