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

from flexmock import flexmock
import pytest
import yaml

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
match:
  package_version:
    name: flask
    version: '>1.0,<=1.1.0'
    index_url: 'https://pypi.org/simple'
run:
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
            package_name="flask",
            package_version="1.2.0",
            index_url="https://pypi.org/simple",
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return([("flask", "1.2.0", "https://pypi.org/simple")]).once()
        self.check_run_stack_info(context, PseudonymPrescription, package_version=package_version)

    def test_run_stack_info_multi_call(self, context: Context) -> None:
        """Make sure the stack info is added just once on multiple calls."""
        prescription_str = """
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '>1.0,<=1.1.0'
    index_url: 'https://pypi.org/simple'
run:
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
            package_name="flask",
            package_version="1.2.0",
            index_url="https://pypi.org/simple",
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return([("flask", "1.2.0", "https://pypi.org/simple")]).twice()

        assert not context.stack_info

        unit = PseudonymPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = list(unit.run(package_version))
            assert result == [("flask", "1.2.0", "https://pypi.org/simple")]
            result = list(unit.run(package_version))
            assert result == [("flask", "1.2.0", "https://pypi.org/simple")]

        assert self.verify_justification_schema(context.stack_info)
        assert len(context.stack_info) == 1, "Only one stack info should be included"
        assert context.stack_info == unit.run_prescription["stack_info"]

    @pytest.mark.parametrize("log_level", ["INFO", "ERROR", "WARNING"])
    def test_run_log(self, caplog, context: Context, log_level: str) -> None:
        """Check logging messages."""
        prescription_str = f"""
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: tensorflow
    version: '~=2.4.0'
    index_url: 'https://pypi.org/simple'
run:
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
            package_name="intel-tensorflow",
            package_version="2.4.0",
            index_url="https://pypi.org/simple",
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
match:
  package_version:
    name: tensorflow-cpu
    index_url: 'https://pypi.org/simple'
run:
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
            package_name="intel-tensorflow",
            package_version=None,
            index_url="https://pypi.org/simple",
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

    def test_should_include_package_name(self) -> None:
        """Test including this pipeline unit."""
        prescription_str = """
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: tensorflow-cpu
    index_url: 'https://pypi.org/simple'
run:
  yield:
    package_version:
      name: intel-tensorflow
      locked_version: null
      index_url: 'https://pypi.org/simple'
"""
        flexmock(PseudonymPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_PSEUDONYM_SCHEMA(prescription)
        PseudonymPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(PseudonymPrescription.should_include(builder_context)) == [
            {
                "package_name": "tensorflow-cpu",
                "match": {
                    "package_version": {
                        "name": "tensorflow-cpu",
                        "index_url": "https://pypi.org/simple",
                    },
                },
                "prescription": {"run": False},
                "run": {
                    "yield": {
                        "package_version": {
                            "name": "intel-tensorflow",
                            "locked_version": None,
                            "index_url": "https://pypi.org/simple",
                        }
                    }
                },
            }
        ]

    def test_should_include_multi(self) -> None:
        """Test including this pipeline unit multiple times."""
        prescription_str = """
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
match:
  - package_version:
      name: tensorflow-cpu
  - package_version:
      name: tensorflow-gpu
  - package_version:
      name: intel-tensorflow
  - package_version:
      name: tensorflow
run:
  yield:
    package_version:
      name: intel-tensorflow
      locked_version: null
      index_url: 'https://pypi.org/simple'
"""
        flexmock(PseudonymPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_PSEUDONYM_SCHEMA(prescription)
        PseudonymPrescription.set_prescription(prescription)

        builder_context = flexmock()
        result = list(PseudonymPrescription.should_include(builder_context))
        assert len(result) == 4

        prescription_conf = result[0]["prescription"]
        assert prescription_conf == {"run": False}
        for item in result:
            assert item["prescription"] is prescription_conf

        assert result == [
            {
                "package_name": "tensorflow-cpu",
                "match": {
                    "package_version": {
                        "name": "tensorflow-cpu",
                    }
                },
                "prescription": {"run": False},
                "run": {
                    "yield": {
                        "package_version": {
                            "name": "intel-tensorflow",
                            "locked_version": None,
                            "index_url": "https://pypi.org/simple",
                        },
                    },
                },
            },
            {
                "package_name": "tensorflow-gpu",
                "match": {
                    "package_version": {
                        "name": "tensorflow-gpu",
                    }
                },
                "prescription": {"run": False},
                "run": {
                    "yield": {
                        "package_version": {
                            "name": "intel-tensorflow",
                            "locked_version": None,
                            "index_url": "https://pypi.org/simple",
                        },
                    },
                },
            },
            {
                "package_name": "intel-tensorflow",
                "match": {
                    "package_version": {
                        "name": "intel-tensorflow",
                    }
                },
                "prescription": {"run": False},
                "run": {
                    "yield": {
                        "package_version": {
                            "name": "intel-tensorflow",
                            "locked_version": None,
                            "index_url": "https://pypi.org/simple",
                        },
                    },
                },
            },
            {
                "package_name": "tensorflow",
                "match": {
                    "package_version": {
                        "name": "tensorflow",
                    }
                },
                "prescription": {"run": False},
                "run": {
                    "yield": {
                        "package_version": {
                            "name": "intel-tensorflow",
                            "locked_version": None,
                            "index_url": "https://pypi.org/simple",
                        },
                    },
                },
            },
        ]

    def test_no_should_include(self) -> None:
        """Test including this pipeline unit without package name."""
        prescription_str = """
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: tensorflow-cpu
    index_url: 'https://pypi.org/simple'
run:
  yield:
    package_version:
      name: intel-tensorflow
      locked_version: null
      index_url: 'https://pypi.org/simple'
"""
        flexmock(PseudonymPrescription).should_receive("_should_include_base").replace_with(lambda _: False).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_PSEUDONYM_SCHEMA(prescription)
        PseudonymPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(PseudonymPrescription.should_include(builder_context)) == []

    def test_run_yield_matched_version(self, context: Context) -> None:
        """Check yielding correct version when yield_matched_version is supplied."""
        prescription_str = """
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '>1.0,<=1.1.0'
    index_url: 'https://pypi.org/simple'
run:
  yield:
    yield_matched_version: true
    package_version:
      name: flask
      index_url: 'https://pypi.org/simple'
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
            package_version="1.1.0",
            index_url=prescription["run"]["yield"].get("package_version", {}).get("index_url"),
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return([("flask", "1.1.0", "https://pypi.org/simple")]).once()

        unit = PseudonymPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = list(unit.run(package_version))

        assert result == [("flask", "1.1.0", "https://pypi.org/simple")]

    def test_run_yield_matched_version_not_index_url(self, context: Context) -> None:
        """Check yielding correct version when "not" index_url is supplied."""
        prescription_str = """
name: PseudonymUnit
type: pseudonym
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: flask
    version: '>1.0,<=1.1.0'
    index_url:
      not: 'https://pypi.org/simple'
run:
  yield:
    yield_matched_version: true
    package_version:
      name: flask
      index_url: 'https://pypi.org/simple'
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_PSEUDONYM_SCHEMA(prescription)
        PseudonymPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==1.1.0",
            index=Source("https://thoth-station.ninja/simple"),
            develop=False,
        )

        context.graph.should_receive("get_solved_python_package_versions_all").with_args(
            package_name=prescription["run"]["yield"].get("package_version", {}).get("name"),
            package_version="1.1.0",
            index_url=prescription["run"]["yield"].get("package_version", {}).get("index_url"),
            count=None,
            os_name=context.project.runtime_environment.operating_system.name,
            os_version=context.project.runtime_environment.operating_system.version,
            python_version=context.project.runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        ).and_return([("flask", "1.1.0", "https://pypi.org/simple")]).once()

        unit = PseudonymPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = list(unit.run(package_version))

        assert result == [("flask", "1.1.0", "https://pypi.org/simple")]
