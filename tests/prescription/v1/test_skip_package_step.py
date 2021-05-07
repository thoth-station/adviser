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

"""Test implementation of skip package step."""

import yaml

import pytest

from thoth.python import PackageVersion
from thoth.python import Source
from thoth.adviser.exceptions import SkipPackage
from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.prescription.v1 import SkipPackageStepPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_SKIP_PACKAGE_STEP_SCHEMA

from .base import AdviserUnitPrescriptionTestCase


class TestSkipPackageStepPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to skip package prescription."""

    def test_run(self, context: Context, state: State) -> None:
        """Test running this pipeline unit."""
        prescription_str = """
name: SkipPackageStep
type: step.SkipPackage
should_include:
  adviser_pipeline: true
match:
  package_name: scipy
  state:
    resolved_dependencies:
      - name: tensorflow
        version: ">=2.1,<=2.3"
        index_url: "https://pypi.org/simple"
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
        PRESCRIPTION_SKIP_PACKAGE_STEP_SCHEMA(prescription)
        SkipPackageStepPrescription.set_prescription(prescription)

        context.stack_info.clear()

        package_version = PackageVersion(
            name="scipy",
            version="==1.6.3",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        state.add_resolved_dependency(("tensorflow", "2.1.1", "https://pypi.org/simple"))

        unit = SkipPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            with pytest.raises(SkipPackage):
                unit.run(state, package_version)

        assert context.stack_info == [
            {
                "type": "INFO",
                "message": "Skip package info stack info",
                "link": "https://thoth-station.ninja",
            }
        ]
