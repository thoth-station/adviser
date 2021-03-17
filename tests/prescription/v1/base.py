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

"""Test implementation of generic v1 prescription unit handling."""

import logging
from typing import Type

import pytest

from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.exceptions import EagerStopPipeline
from thoth.adviser.context import Context
from thoth.adviser.prescription.v1 import UnitPrescription

from ...base import AdviserTestCase


class AdviserUnitPrescriptionTestCase(AdviserTestCase):
    """Test implementation of generic v1 prescription unit handling."""

    @staticmethod
    def setup_method() -> None:
        """Make sure prescription is not assigned before any test."""
        UnitPrescription._PRESCRIPTION = None

    @staticmethod
    def teardown_method() -> None:
        """Make sure prescription is not assigned before any test."""
        UnitPrescription._PRESCRIPTION = None

    def check_run_stack_info(self, context, unit_class: Type[UnitPrescription], **kwargs) -> None:
        """Check assigning stack info."""
        assert not context.stack_info

        unit = unit_class()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(**kwargs)
            if result is not None:
                list(result)

        assert self.verify_justification_schema(context.stack_info)
        assert context.stack_info == unit.run_prescription["stack_info"]

    @staticmethod
    def check_run_eager_stop_pipeline(context: Context, unit_class: Type[UnitPrescription], **kwargs) -> None:
        """Check eager stop pipeline configuration."""
        unit = unit_class()
        unit.pre_run()
        with unit.assigned_context(context):
            with pytest.raises(EagerStopPipeline, match=unit.run_prescription["eager_stop_pipeline"]):
                result = unit.run(**kwargs)
                if result is not None:
                    list(result)

    @staticmethod
    def check_run_not_acceptable(context: Context, unit_class: Type[UnitPrescription], **kwargs) -> None:
        """Check raising not acceptable."""
        unit = unit_class()
        unit.pre_run()
        with unit.assigned_context(context):
            with pytest.raises(NotAcceptable, match=unit.run_prescription["not_acceptable"]):
                result = unit.run(**kwargs)
                if result is not None:
                    list(result)

    @staticmethod
    def check_run_log(caplog, context: Context, log_level: str, unit_class: Type[UnitPrescription], **kwargs) -> None:
        """Check raising not acceptable."""
        unit = unit_class()
        unit.pre_run()
        with unit.assigned_context(context):
            with caplog.at_level(getattr(logging, log_level)):
                result = unit.run(**kwargs)
                if result is not None:
                    list(result)

        assert f"{unit.get_unit_name()}: {unit.run_prescription['log']['message']}" in caplog.messages
