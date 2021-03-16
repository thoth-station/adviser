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

"""Test implementation of step prescription v1."""

import pytest
import yaml

from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.prescription.v1 import StepPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_STEP_SCHEMA
from thoth.python import PackageVersion
from thoth.python import Source

from .base import AdviserUnitPrescriptionTestCase


class TestStepPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to step prescription v1."""

    def test_run_stack_info(self, context: Context, state: State) -> None:
        """Check assigning stack info."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
run:
  match:
    package_version:
      index_url: 'https://thoth-station.ninja/simple'

  stack_info:
    - type: WARNING
      message: Some message
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==1.1.0",
            index=Source("https://thoth-station.ninja/simple"),
            develop=False,
        )

        self.check_run_stack_info(context, StepPrescription, state=state, package_version=package_version)

    @pytest.mark.parametrize("log_level", ["INFO", "ERROR", "WARNING"])
    def test_run_log(self, caplog, context: Context, state: State, log_level: str) -> None:
        """Check logging messages."""
        prescription_str = f"""
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
run:
  match:
    package_version:
      name: flask

  log:
    message: Seen flask during resolution
    type: {log_level}
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==1.1.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        self.check_run_log(caplog, context, log_level, StepPrescription, state=state, package_version=package_version)

    def test_run_eager_stop_pipeline(self, context: Context, state: State) -> None:
        """Check eager stop pipeline configuration."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  dependency_monkey_pipeline: true
run:
  match:
    package_version:
      name: flask
      version: "<1.0.0"

  eager_stop_pipeline: This is exception message reported
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==0.12",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        self.check_run_eager_stop_pipeline(context, StepPrescription, state=state, package_version=package_version)

    def test_run_not_acceptable(self, context: Context, state: State) -> None:
        """Check raising not acceptable."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
  dependency_monkey_pipeline: true
run:
  match:
    package_version:
        name: flask
        version: "~=0.0"
        index_url: "https://pypi.org/simple"

  not_acceptable: This is exception message reported
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==0.12",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        self.check_run_not_acceptable(context, StepPrescription, state=state, package_version=package_version)

    def test_run(self, context: Context, state: State) -> None:
        """Check running the step with score and justification."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
run:
  match:
    package_version:
      name: pysaml2
      version: '<6.5.0'
      index_url: 'https://pypi.org/simple'

  score: -0.1
  justification:
    - type: WARNING
      message: CVE found for pysaml2
      link: cve_pysaml2
    - type: INFO
      message: Package pysaml2 was removed from software stack resolution
      link: https://example.com
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="pysaml2",
            version="==6.4.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == -0.1
        assert result[1] == unit.run_prescription["justification"]

    def test_run_state(self, context: Context, state: State) -> None:
        """Test running the prescription if state matches."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
run:
  match:
    package_version:
      name: numpy
      version: '==1.19.1'
      index_url: 'https://pypi.org/simple'
    state:
      resolved_dependencies:
        - name: tensorflow
          version: '~=2.4.0'

  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        state.add_resolved_dependency(("tensorflow", "2.4.0", "https://pypi.org/simple"))

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)

        assert isinstance(result, tuple)
        assert result[0] == 0.5
        assert result[1] is None

    def test_run_state_no_match(self, context: Context, state: State) -> None:
        """Test running the prescription if state matches."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
run:
  match:
    package_version:
      name: numpy
      version: '==1.19.1'
      index_url: 'https://pypi.org/simple'
    state:
      resolved_dependencies:
        - name: tensorflow
          version: '~=2.4.0'

  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        state.add_resolved_dependency(("tensorflow", "2.2.0", "https://pypi.org/simple"))

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)

        assert result is None

    @pytest.mark.parametrize("multi_package_resolution", [True, False])
    def test_run_multi_package_resolution(self, context: Context, state: State, multi_package_resolution: bool) -> None:
        """Check multi package resolution configuration application."""
        # TODO: implement
