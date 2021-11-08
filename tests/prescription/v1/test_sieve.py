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

"""Test implementation of sieve prescription v1."""

from flexmock import flexmock
import pytest
import yaml

from thoth.adviser.context import Context
from thoth.adviser.prescription.v1 import SievePrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_SIEVE_SCHEMA
from thoth.python import PackageVersion
from thoth.python import Source

from .base import AdviserUnitPrescriptionTestCase


class TestSievePrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to sieve prescription v1."""

    def test_run_stack_info(self, context: Context) -> None:
        """Check assigning stack info."""
        prescription_str = """
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '>1.0,<=1.1.0'
    index_url: 'https://pypi.org/simple'
run:
  stack_info:
    - type: WARNING
      message: Some stack warning message printed by a sieve
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==1.1.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        self.check_run_stack_info(context, SievePrescription, package_versions=(pv for pv in [package_version]))

    def test_run_stack_info_run_multi(self, context: Context) -> None:
        """Check assigning stack info only once on multiple calls."""
        prescription_str = """
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '>1.0,<=1.1.0'
    index_url: 'https://pypi.org/simple'
run:
  stack_info:
    - type: WARNING
      message: Some stack warning message printed by a sieve
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==1.1.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        assert not context.stack_info

        unit = SievePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = list(unit.run((pv for pv in (package_version,))))
            assert not result
            result = list(unit.run((pv for pv in (package_version,))))
            assert not result

        assert self.verify_justification_schema(context.stack_info)
        assert len(context.stack_info) == 1, "Stack information should be added only once"
        assert context.stack_info == unit.run_prescription["stack_info"]

    @pytest.mark.parametrize("log_level", ["INFO", "ERROR", "WARNING"])
    def test_run_log(self, caplog, context: Context, log_level: str) -> None:
        """Check logging messages."""
        prescription_str = f"""
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '>1.0,<=1.1.0'
    index_url: 'https://pypi.org/simple'
run:
  log:
    message: Some stack warning message printed by a sieve
    type: {log_level}
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==1.1.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        self.check_run_log(
            caplog, context, log_level, SievePrescription, package_versions=(pv for pv in [package_version])
        )

    def test_sieve(self, context: Context) -> None:
        """Test sieving packages."""
        prescription_str = """
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '<=1.1.0'
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)
        package_versions = [
            PackageVersion(
                name="flask",
                version="==1.1.0",
                index=Source("https://thoth-station.ninja"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==1.1.2",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==1.0.2",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]

        unit = SievePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = list(unit.run((pv for pv in package_versions)))

        assert len(result) == 1
        assert result[0] == package_versions[1]  # ==1.1.2 stays in the result

    def test_should_include_package_name(self) -> None:
        """Test including this pipeline unit."""
        prescription_str = """
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '<=1.1.0'
"""
        flexmock(SievePrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(SievePrescription.should_include(builder_context)) == [
            {
                "package_name": "flask",
                "match": {
                    "package_version": {
                        "name": "flask",
                        "version": "<=1.1.0",
                    },
                },
                "run": {},
                "prescription": {"run": False},
            },
        ]

    def test_should_include_multi(self) -> None:
        """Test including this pipeline unit multiple times."""
        prescription_str = """
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  - package_version:
      name: flask
      version: '<=1.1.0'
  - package_version:
      name: numpy
"""
        flexmock(SievePrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)

        builder_context = flexmock()
        result = list(SievePrescription.should_include(builder_context))
        assert len(result) == 2

        assert result == [
            {
                "package_name": "flask",
                "match": {
                    "package_version": {
                        "name": "flask",
                        "version": "<=1.1.0",
                    },
                },
                "run": {},
                "prescription": {"run": False},
            },
            {
                "package_name": "numpy",
                "match": {
                    "package_version": {
                        "name": "numpy",
                    },
                },
                "prescription": {"run": False},
                "run": {},
            },
        ]

    def test_should_include_no_package_name(self) -> None:
        """Test including this pipeline unit."""
        prescription_str = """
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    index_url: https://pypi.org/simple
"""
        flexmock(SievePrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(SievePrescription.should_include(builder_context)) == [
            {
                "package_name": None,
                "match": {
                    "package_version": {
                        "index_url": "https://pypi.org/simple",
                    }
                },
                "prescription": {"run": False},
                "run": {},
            }
        ]

    def test_no_should_include(self) -> None:
        """Test not including this pipeline."""
        prescription_str = """
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '<=1.1.0'
"""
        flexmock(SievePrescription).should_receive("_should_include_base").replace_with(lambda _: False).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(SievePrescription.should_include(builder_context)) == []

    def test_sieve_not_index_url(self, context: Context) -> None:
        """Test sieving packages based on "not" index_url."""
        prescription_str = """
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    index_url:
      not: https://pypi.org/simple
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)
        package_versions = [
            PackageVersion(
                name="flask",
                version="==1.1.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==1.1.2",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==1.0.2",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]

        unit = SievePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = list(unit.run((pv for pv in package_versions)))

        assert len(result) == 2
        assert result == [package_versions[1], package_versions[2]]

    @pytest.mark.parametrize("develop", [True, False])
    def test_sieve_develop_true(self, context: Context, develop: bool) -> None:
        """Test sieving packages based on develop flag set to true."""
        prescription_str = f"""
name: SieveUnit
type: sieve
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    develop: {'true' if develop else 'false'}
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SIEVE_SCHEMA(prescription)
        SievePrescription.set_prescription(prescription)
        package_versions = [
            PackageVersion(
                name="flask",
                version="==1.1.2",
                index=Source("https://pypi.org/simple"),
                develop=develop,
            ),
            PackageVersion(
                name="flask",
                version="==1.0.2",
                index=Source("https://pypi.org/simple"),
                develop=not develop,
            ),
        ]

        unit = SievePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = list(unit.run((pv for pv in package_versions)))

        assert len(result) == 1
        assert [result[0]] == [pv for pv in package_versions if pv.develop != develop]
