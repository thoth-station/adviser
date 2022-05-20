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

"""Test implementation of group step."""

import yaml

from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.prescription.v1 import GroupStepPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_GROUP_STEP_SCHEMA

from .base import AdviserUnitPrescriptionTestCase


class TestGroupStepPrescription(AdviserUnitPrescriptionTestCase):
    """Test implementation of group step.

    As the run implementation is shared with raw step, only computation done in should_include is tested here.
    """

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test calculating configuration for the given prescription unit."""
        prescription_str = """\
name: GroupStep
type: step.Group
should_include:
  adviser_pipeline: true
match:
  group:
  - package_version:
      name: numpy
      version: '!=1.21.4'
      index_url:
        not: 'https://pypi.org/simple'
  - package_version:
      name: tensorflow
      version: '~=2.7.0'
  - package_version:
      name: pandas
      index_url: 'https://thoth-station.ninja'
      develop: true
  - package_version:
      name: werkzeug
      version: '==1.0.0'
      index_url: 'https://pypi.org/simple'
      develop: false
run:
  stack_info:
  - type: INFO
    message: Running the unit.
    link: 'https://thoth-station.ninja'
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_GROUP_STEP_SCHEMA(prescription)
        GroupStepPrescription.set_prescription(prescription)

        configurations = list(GroupStepPrescription.should_include(builder_context))

        assert configurations == [
            {
                "match": {
                    "package_version": {
                        "index_url": {"not": "https://pypi.org/simple"},
                        "name": "numpy",
                        "version": "!=1.21.4",
                    },
                    "state": {
                        "resolved_dependencies": [
                            {"name": "tensorflow", "version": "~=2.7.0"},
                            {"develop": True, "index_url": "https://thoth-station.ninja", "name": "pandas"},
                            {
                                "develop": False,
                                "index_url": "https://pypi.org/simple",
                                "name": "werkzeug",
                                "version": "==1.0.0",
                            },
                        ]
                    },
                },
                "multi_package_resolution": True,
                "package_name": "numpy",
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {"link": "https://thoth-station.ninja", "message": "Running the unit.", "type": "INFO"}
                    ]
                },
            },
            {
                "match": {
                    "package_version": {"name": "tensorflow", "version": "~=2.7.0"},
                    "state": {
                        "resolved_dependencies": [
                            {"index_url": {"not": "https://pypi.org/simple"}, "name": "numpy", "version": "!=1.21.4"},
                            {"develop": True, "index_url": "https://thoth-station.ninja", "name": "pandas"},
                            {
                                "develop": False,
                                "index_url": "https://pypi.org/simple",
                                "name": "werkzeug",
                                "version": "==1.0.0",
                            },
                        ]
                    },
                },
                "multi_package_resolution": True,
                "package_name": "tensorflow",
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {"link": "https://thoth-station.ninja", "message": "Running the unit.", "type": "INFO"}
                    ]
                },
            },
            {
                "match": {
                    "package_version": {"develop": True, "index_url": "https://thoth-station.ninja", "name": "pandas"},
                    "state": {
                        "resolved_dependencies": [
                            {"index_url": {"not": "https://pypi.org/simple"}, "name": "numpy", "version": "!=1.21.4"},
                            {"name": "tensorflow", "version": "~=2.7.0"},
                            {
                                "develop": False,
                                "index_url": "https://pypi.org/simple",
                                "name": "werkzeug",
                                "version": "==1.0.0",
                            },
                        ]
                    },
                },
                "multi_package_resolution": True,
                "package_name": "pandas",
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {"link": "https://thoth-station.ninja", "message": "Running the unit.", "type": "INFO"}
                    ]
                },
            },
            {
                "match": {
                    "package_version": {
                        "develop": False,
                        "index_url": "https://pypi.org/simple",
                        "name": "werkzeug",
                        "version": "==1.0.0",
                    },
                    "state": {
                        "resolved_dependencies": [
                            {"index_url": {"not": "https://pypi.org/simple"}, "name": "numpy", "version": "!=1.21.4"},
                            {"name": "tensorflow", "version": "~=2.7.0"},
                            {"develop": True, "index_url": "https://thoth-station.ninja", "name": "pandas"},
                        ]
                    },
                },
                "multi_package_resolution": True,
                "package_name": "werkzeug",
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {"link": "https://thoth-station.ninja", "message": "Running the unit.", "type": "INFO"}
                    ]
                },
            },
        ]

        for conf in configurations:
            GroupStepPrescription.CONFIGURATION_SCHEMA(conf)

    def test_should_include_groups(self, builder_context: PipelineBuilderContext) -> None:
        """Test calculating configuration for the given prescription unit, multiple groups."""
        prescription_str = """\
name: GroupStep
type: step.Group
should_include:
  adviser_pipeline: true
match:
- group:
  - package_version:
      name: numpy
      version: '!=1.21.4'
      index_url:
        not: 'https://pypi.org/simple'
  - package_version:
      name: tensorflow
      version: '~=2.7.0'
- group:
  - package_version:
      name: pandas
      index_url: 'https://thoth-station.ninja'
      develop: true
  - package_version:
      name: werkzeug
      version: '==1.0.0'
      index_url: 'https://pypi.org/simple'
      develop: false
run:
  stack_info:
  - type: INFO
    message: Running the unit.
    link: 'https://thoth-station.ninja'
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_GROUP_STEP_SCHEMA(prescription)
        GroupStepPrescription.set_prescription(prescription)

        configurations = list(GroupStepPrescription.should_include(builder_context))

        assert configurations == [
            {
                "match": {
                    "package_version": {
                        "index_url": {"not": "https://pypi.org/simple"},
                        "name": "numpy",
                        "version": "!=1.21.4",
                    },
                    "state": {"resolved_dependencies": [{"name": "tensorflow", "version": "~=2.7.0"}]},
                },
                "multi_package_resolution": True,
                "package_name": "numpy",
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {"link": "https://thoth-station.ninja", "message": "Running the unit.", "type": "INFO"}
                    ]
                },
            },
            {
                "match": {
                    "package_version": {"name": "tensorflow", "version": "~=2.7.0"},
                    "state": {
                        "resolved_dependencies": [
                            {"index_url": {"not": "https://pypi.org/simple"}, "name": "numpy", "version": "!=1.21.4"}
                        ]
                    },
                },
                "multi_package_resolution": True,
                "package_name": "tensorflow",
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {"link": "https://thoth-station.ninja", "message": "Running the unit.", "type": "INFO"}
                    ]
                },
            },
            {
                "match": {
                    "package_version": {"develop": True, "index_url": "https://thoth-station.ninja", "name": "pandas"},
                    "state": {
                        "resolved_dependencies": [
                            {
                                "develop": False,
                                "index_url": "https://pypi.org/simple",
                                "name": "werkzeug",
                                "version": "==1.0.0",
                            }
                        ]
                    },
                },
                "multi_package_resolution": True,
                "package_name": "pandas",
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {"link": "https://thoth-station.ninja", "message": "Running the unit.", "type": "INFO"}
                    ]
                },
            },
            {
                "match": {
                    "package_version": {
                        "develop": False,
                        "index_url": "https://pypi.org/simple",
                        "name": "werkzeug",
                        "version": "==1.0.0",
                    },
                    "state": {
                        "resolved_dependencies": [
                            {"develop": True, "index_url": "https://thoth-station.ninja", "name": "pandas"}
                        ]
                    },
                },
                "multi_package_resolution": True,
                "package_name": "werkzeug",
                "prescription": {"run": False},
                "run": {
                    "stack_info": [
                        {"link": "https://thoth-station.ninja", "message": "Running the unit.", "type": "INFO"}
                    ]
                },
            },
        ]

        for conf in configurations:
            GroupStepPrescription.CONFIGURATION_SCHEMA(conf)
