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

"""Test implementation of skip package sieve."""

import yaml

from flexmock import flexmock
import pytest

from thoth.adviser.exceptions import SkipPackage
from thoth.adviser.context import Context
from thoth.adviser.prescription.v1 import SkipPackageSievePrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_SKIP_PACKAGE_SIEVE_SCHEMA

from .base import AdviserUnitPrescriptionTestCase


class TestSkipPackageSievePrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to skip package prescription."""

    def test_run(self, context: Context) -> None:
        """Test running this pipeline unit."""
        prescription_str = """
name: SkipPackageSieve
type: sieve.SkipPackage
should_include:
  adviser_pipeline: true
match:
  package_name: flask
run:
  stack_info:
    - type: INFO
      message: Skip package info stack info
      link: https://thoth-station.ninja
  log:
    message: Skip package info message
    type: INFO
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SKIP_PACKAGE_SIEVE_SCHEMA(prescription)
        SkipPackageSievePrescription.set_prescription(prescription)

        context.stack_info.clear()

        unit = SkipPackageSievePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            with pytest.raises(SkipPackage):
                unit.run((i for i in (flexmock(),)))

            # Run multiple times to verify stack_info is adjusted just once.
            with pytest.raises(SkipPackage):
                unit.run((i for i in (flexmock(),)))

        assert context.stack_info == [
            {
                "type": "INFO",
                "message": "Skip package info stack info",
                "link": "https://thoth-station.ninja",
            }
        ]

    def test_run_list(self, context: Context) -> None:
        """Test running this pipeline unit."""
        prescription_str = """
name: SkipPackageSieve
type: sieve.SkipPackage
should_include:
  adviser_pipeline: true
match:
  - package_name: flask
  - package_name: connexion
run:
  stack_info:
    - type: INFO
      message: Skip package info stack info
      link: https://thoth-station.ninja
  log:
    message: Skip package info message
    type: INFO
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SKIP_PACKAGE_SIEVE_SCHEMA(prescription)
        SkipPackageSievePrescription.set_prescription(prescription)

        context.stack_info.clear()

        unit = SkipPackageSievePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            with pytest.raises(SkipPackage):
                unit.run((i for i in (flexmock(),)))

            # Run multiple times to verify stack_info is adjusted just once.
            with pytest.raises(SkipPackage):
                unit.run((i for i in (flexmock(),)))

        assert context.stack_info == [
            {
                "type": "INFO",
                "message": "Skip package info stack info",
                "link": "https://thoth-station.ninja",
            }
        ]
