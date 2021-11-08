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

"""Test implementation of boot prescription v1."""

from typing import Optional

from flexmock import flexmock
import pytest
import yaml

from thoth.adviser.context import Context
from thoth.adviser.prescription.v1 import BootPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_BOOT_SCHEMA

from .base import AdviserUnitPrescriptionTestCase


class TestBootPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to boot prescription v1."""

    def test_run_stack_info(self, context: Context) -> None:
        """Check assigning stack info."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_name: flask
run:
  stack_info:
    - type: ERROR
      message: "Unable to perform this operation"
      link: https://thoth-station.ninja
    - type: INFO
      message: "Hello, Thoth!"
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)
        self.check_run_stack_info(context, BootPrescription)

    def test_run_eager_stop_pipeline(self, context: Context) -> None:
        """Check eager stop pipeline configuration."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  dependency_monkey_pipeline: true
run:
  eager_stop_pipeline: This is exception message reported
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)
        self.check_run_eager_stop_pipeline(context, BootPrescription)

    def test_run_not_acceptable(self, context: Context) -> None:
        """Check raising not acceptable."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
  dependency_monkey_pipeline: true
run:
  not_acceptable: This is exception message reported
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)
        self.check_run_not_acceptable(context, BootPrescription)

    @pytest.mark.parametrize("log_level", ["INFO", "ERROR", "WARNING"])
    def test_run_log(self, caplog, context: Context, log_level: str) -> None:
        """Check reporting to log."""
        prescription_str = f"""
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
  dependency_monkey_pipeline: true
run:
  log:
    message: Some message logged
    type: {log_level}
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)
        self.check_run_log(caplog, context, log_level, BootPrescription)

    @pytest.mark.parametrize("package_name", [None, "flask"])
    def test_run_match(self, package_name: Optional[str]) -> None:
        """Test proper initialization based on yielded package_name."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_name: flask
run:
  stack_info:
    - type: ERROR
      message: "Unable to perform this operation"
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)
        unit = BootPrescription()
        unit.update_configuration({"package_name": package_name})
        assert unit.configuration["package_name"] == package_name

    def test_should_include_package_name(self) -> None:
        """Test including this pipeline unit."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_name: flask
run:
  stack_info:
    - type: ERROR
      message: "Unable to perform this operation"
      link: https://thoth-station.ninja
"""
        flexmock(BootPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(BootPrescription.should_include(builder_context)) == [
            {
                "package_name": "flask",
                "match": {
                    "package_name": "flask",
                },
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {
                            "type": "ERROR",
                            "message": "Unable to perform this operation",
                            "link": "https://thoth-station.ninja",
                        }
                    ]
                },
            }
        ]

    def test_should_include_multi(self) -> None:
        """Test including this pipeline unit multiple times."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
match:
  - package_name: flask
  - package_name: pandas
run:
  stack_info:
    - type: ERROR
      message: "Unable to perform this operation"
      link: https://thoth-station.ninja
"""
        flexmock(BootPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)

        builder_context = flexmock()
        result = list(BootPrescription.should_include(builder_context))
        assert len(result) == 2
        assert result == [
            {
                "package_name": "flask",
                "match": {
                    "package_name": "flask",
                },
                "prescription": {
                    "run": False,
                },
                "run": {
                    "stack_info": [
                        {
                            "type": "ERROR",
                            "message": "Unable to perform this operation",
                            "link": "https://thoth-station.ninja",
                        }
                    ]
                },
            },
            {
                "package_name": "pandas",
                "match": {
                    "package_name": "pandas",
                },
                "prescription": {
                    "run": False,
                },
                "run": {
                    "stack_info": [
                        {
                            "type": "ERROR",
                            "message": "Unable to perform this operation",
                            "link": "https://thoth-station.ninja",
                        }
                    ]
                },
            },
        ]
        assert result[0]["prescription"] is result[1]["prescription"]

    def test_should_include_no_package_name(self) -> None:
        """Test including this pipeline unit without package name."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
run:
  stack_info:
    - type: INFO
      message: Yet another text printed.
      link: https://thoth-station.ninja
"""
        flexmock(BootPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(BootPrescription.should_include(builder_context)) == [
            {
                "match": {},
                "package_name": None,
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {
                            "type": "INFO",
                            "message": "Yet another text printed.",
                            "link": "https://thoth-station.ninja",
                        }
                    ]
                },
            }
        ]

    def test_no_should_include(self) -> None:
        """Test including this pipeline unit without package name."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
run:
  stack_info:
    - type: INFO
      message: Yet another text printed.
      link: https://thoth-station.ninja
"""
        flexmock(BootPrescription).should_receive("_should_include_base").replace_with(lambda _: False).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(BootPrescription.should_include(builder_context)) == []

    def test_should_include_multi_run(self, context: Context) -> None:
        """Test including this pipeline unit multiple times."""
        prescription_str = """
name: BootUnit
type: boot
should_include:
  times: 1
  adviser_pipeline: true
match:
- package_name: flask
- package_name: pandas
run:
  stack_info:
  - type: INFO
    message: "Hello, Thoth!"
    link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_BOOT_SCHEMA(prescription)
        BootPrescription.set_prescription(prescription)
        unit = BootPrescription()

        assert "flask" in (pv.name for pv in context.project.iter_dependencies())

        unit.pre_run()
        with unit.assigned_context(context):
            # Run twice.
            unit.run()
            unit.run()

        assert context.stack_info == [
            {"type": "INFO", "message": "Hello, Thoth!", "link": "https://thoth-station.ninja"}
        ]
