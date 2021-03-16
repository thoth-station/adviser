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

"""Test implementation of pseudonym prescription v1."""

from typing import Optional

import yaml
import pytest

from thoth.adviser.context import Context
from thoth.adviser.prescription.v1 import PseudonymPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_PSEUDONYM_SCHEMA
from thoth.python import PackageVersion
from thoth.python import Source

from .base import AdviserUnitPrescriptionTestCase


class TestPseudonymPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to pseudonym prescription v1."""

    def test_run_stack_info(self, context: Context) -> None:
        """Check assigning stack info."""
        prescription_str = """
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
run:
  match:
    package_version:
      name: flask
      version: '>1.0,<=1.1.0'
      index_url: 'https://pypi.org/simple'

  yield:
    package_version:
      name: flask
      locked_version: ==1.2.0
      index_url: 'https://pypi.org/simple'

  stack_info:
    - type: WARNING
      message: Some stack warning message
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_PSEUDONYM_SCHEMA(prescription)
        PseudonymPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==1.1.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        context.graph.should_receive("get_solved_python_package_versions_all").with_args(
            package_name=prescription["run"]["yield"].get("package_version", {}).get("name"),
            package_version=prescription["run"]["yield"].get("package_version", {}).get("locked_version"),
            index_url=prescription["run"]["yield"].get("package_version", {}).get("index_url"),
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return([("flask", "1.2.0", "https://pypi.org/simple")]).once()
        self.check_run_stack_info(context, PseudonymPrescription, package_version=package_version)

    @pytest.mark.parametrize("log_level", ["INFO", "ERROR", "WARNING"])
    def test_run_log(self, caplog, context: Context, log_level: str) -> None:
        """Check logging messages."""
        prescription_str = f"""
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
run:
  match:
    package_version:
      name: tensorflow
      version: '~=2.4.0'
      index_url: 'https://pypi.org/simple'

  yield:
    package_version:
      name: intel-tensorflow
      locked_version: ==2.4.0
      index_url: 'https://pypi.org/simple'

  log:
    message: Yet some message logged
    type: {log_level}
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_PSEUDONYM_SCHEMA(prescription)
        PseudonymPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.4.1dev0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        context.graph.should_receive("get_solved_python_package_versions_all").with_args(
            package_name=prescription["run"]["yield"].get("package_version", {}).get("name"),
            package_version=prescription["run"]["yield"].get("package_version", {}).get("locked_version"),
            index_url=prescription["run"]["yield"].get("package_version", {}).get("index_url"),
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return([("intel-tensorflow", "2.4.0", "https://pypi.org/simple")]).once()

        self.check_run_log(caplog, context, log_level, PseudonymPrescription, package_version=package_version)

    @pytest.mark.parametrize("package_name", [None, "flask"])
    def test_run_match(self, package_name: Optional[str], context: Context) -> None:
        """Test proper initialization based on yielded package_name."""
        prescription_str = """
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
run:
  match:
    package_version:
      name: tensorflow-cpu
      index_url: 'https://pypi.org/simple'

  yield:
    package_version:
      name: intel-tensorflow
      locked_version: null
      index_url: 'https://pypi.org/simple'
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_PSEUDONYM_SCHEMA(prescription)
        PseudonymPrescription.set_prescription(prescription)

        package_version = PackageVersion(
            name="tensorflow-cpu",
            version="==2.4.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        expected_result = [
            ("intel-tensorflow", "2.4.0", "https://pypi.org/simple"),
            ("intel-tensorflow", "2.4.1", "https://pypi.org/simple"),
        ]

        context.graph.should_receive("get_solved_python_package_versions_all").with_args(
            package_name=prescription["run"]["yield"].get("package_version", {}).get("name"),
            package_version=prescription["run"]["yield"].get("package_version", {}).get("locked_version"),
            index_url=prescription["run"]["yield"].get("package_version", {}).get("index_url"),
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return(expected_result).once()

        unit = PseudonymPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = list(unit.run(package_version=package_version))

        assert result == expected_result
