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

"""Test implementation of stride prescription v1."""

import flexmock
import pytest
import yaml

from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.prescription.v1 import StridePrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_STRIDE_SCHEMA
from thoth.python import PackageVersion
from thoth.python import Source

from .base import AdviserUnitPrescriptionTestCase


class TestStridePrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to stride prescription v1."""

    def test_run_stack_info(self, context: Context, state: State) -> None:
        """Check assigning stack info."""
        prescription_str = """
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
 state:
    resolved_dependencies:
      - name: werkzeug
        version: "<=1.0.0"
        index_url: 'https://pypi.org/simple'
run:
  stack_info:
    - type: WARNING
      message: Some message
      link: https://pypi.org/project/werkzeug
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)
        state.add_resolved_dependency(("werkzeug", "0.5.0", "https://pypi.org/simple"))
        self.check_run_stack_info(context, StridePrescription, state=state)

    @pytest.mark.parametrize("log_level", ["INFO", "ERROR", "WARNING"])
    def test_run_log(self, caplog, context: Context, state: State, log_level: str) -> None:
        """Check logging messages."""
        prescription_str = f"""
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
 state:
    resolved_dependencies:
      - name: flask
run:
  log:
    message: Seen flask in one of the resolved stacks
    type: {log_level}
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12", "https://pypi.org/simple"))
        self.check_run_log(caplog, context, log_level, StridePrescription, state=state)

    def test_run_eager_stop_pipeline(self, context: Context, state: State) -> None:
        """Check eager stop pipeline configuration."""
        prescription_str = """
name: StrideUnit
type: stride
should_include:
  times: 1
  dependency_monkey_pipeline: true
match:
 state:
   resolved_dependencies:
    - name: flask
      version: ==0.12
    - name: werkzeug
      version: ==1.0.1
    - name: itsdangerous
      version: <1.0
run:
  eager_stop_pipeline: These three cannot occur together
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12.0", "https://pypi.org/simple"))
        state.add_resolved_dependency(("werkzeug", "1.0.1", "https://pypi.org/simple"))
        state.add_resolved_dependency(("itsdangerous", "0.5.1", "https://pypi.org/simple"))
        self.check_run_eager_stop_pipeline(context, StridePrescription, state=state)

    def test_run_not_acceptable(self, context: Context, state: State) -> None:
        """Check raising not acceptable."""
        prescription_str = """
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
      - name: connexion
        version: "==2.7.0"
        index_url: "https://pypi.org/simple"
run:
  not_acceptable: This is exception message reported
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12", "https://pypi.org/simple"))
        state.add_resolved_dependency(("connexion", "2.7.0", "https://pypi.org/simple"))
        self.check_run_not_acceptable(context, StridePrescription, state=state)

    def test_run_no_match(self, context: Context, state: State) -> None:
        """Test running this pipeline unit without match."""
        prescription_str = """
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
      - name: connexion
        version: "==2.7.0"
        index_url: "https://pypi.org/simple"
run:
  stack_info:
    - type: ERROR
      message: This message will not be shown
      link: https://pypi.org/project/connexion
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12", "https://pypi.org/simple"))
        state.add_resolved_dependency(("connexion", "2.0.0", "https://pypi.org/simple"))

        assert not context.stack_info

        unit = StridePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert not context.stack_info

    def test_should_include(self) -> None:
        """Test including this pipeline unit."""
        prescription_str = """
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
run:
  stack_info:
    - type: ERROR
      message: This message will not be shown
      link: https://pypi.org/project/connexion
"""
        flexmock(StridePrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(StridePrescription.should_include(builder_context)) == [
            {
                "package_name": "flask",
                "match": {
                    "state": {
                        "resolved_dependencies": [
                            {
                                "name": "flask",
                                "version": "<=1.0.0,>=0.12",
                                "index_url": "https://pypi.org/simple",
                            }
                        ]
                    },
                },
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {
                            "type": "ERROR",
                            "message": "This message will not be shown",
                            "link": "https://pypi.org/project/connexion",
                        }
                    ]
                },
            }
        ]

    def test_should_include_multi(self) -> None:
        """Test including this pipeline unit multiple times."""
        prescription_str = """
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
  - state:
      resolved_dependencies:
        - name: flask
  - state:
      resolved_dependencies:
        - name: werkzeug
run:
  stack_info:
    - type: INFO
      message: This message will be shown probably multiple times
      link: https://pypi.org/project/flask
"""
        flexmock(StridePrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(StridePrescription.should_include(builder_context)) == [
            {
                "package_name": "flask",
                "match": {
                    "state": {
                        "resolved_dependencies": [
                            {
                                "name": "flask",
                            }
                        ]
                    },
                },
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {
                            "type": "INFO",
                            "message": "This message will be shown probably multiple times",
                            "link": "https://pypi.org/project/flask",
                        }
                    ]
                },
            },
            {
                "package_name": "werkzeug",
                "match": {
                    "state": {
                        "resolved_dependencies": [
                            {
                                "name": "werkzeug",
                            }
                        ]
                    },
                },
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {
                            "type": "INFO",
                            "message": "This message will be shown probably multiple times",
                            "link": "https://pypi.org/project/flask",
                        }
                    ]
                },
            },
        ]

    def test_no_should_include(self) -> None:
        """Test not including this pipeline unit."""
        prescription_str = """
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
run:
  stack_info:
    - type: ERROR
      message: This message will not be shown
      link: https://pypi.org/project/connexion
"""
        flexmock(StridePrescription).should_receive("_should_include_base").replace_with(lambda _: False).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(StridePrescription.should_include(builder_context)) == []

    @pytest.mark.parametrize("develop", [True, False])
    def test_run_match_develop(self, context: Context, state: State, develop: bool) -> None:
        """Test running this pipeline unit based on develop matching."""
        prescription_str = f"""
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        develop: {'true' if develop else 'false'}
run:
  stack_info:
    - type: INFO
      message: This message will be shown
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==2.0.1",
            index=Source("https://pypi.org/simple"),
            develop=develop,
        )
        state.add_resolved_dependency(package_version.to_tuple())
        context.register_package_version(package_version)

        assert not context.stack_info

        unit = StridePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

            # Run one more time to verify the stack info is added just once.
            assert unit.run(state) is None

        assert context.stack_info == [
            {"type": "INFO", "message": "This message will be shown", "link": "https://thoth-station.ninja"}
        ]

    @pytest.mark.parametrize("develop", [True, False])
    def test_run_not_match_develop(self, context: Context, state: State, develop: bool) -> None:
        """Test running this pipeline unit when develop is not matching."""
        prescription_str = f"""
name: StrideUnit
type: stride
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        develop: {'true' if develop else 'false'}
run:
  stack_info:
    - type: INFO
      message: This message will NOT be shown
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STRIDE_SCHEMA(prescription)
        StridePrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="flask",
            version="==2.0.1",
            index=Source("https://pypi.org/simple"),
            develop=not develop,
        )
        state.add_resolved_dependency(package_version.to_tuple())
        context.register_package_version(package_version)

        assert not context.stack_info

        unit = StridePrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert not context.stack_info
