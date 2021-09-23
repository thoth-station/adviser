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

from thoth.adviser.exceptions import SkipPackage
from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.prescription.v1 import SkipPackageStepPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_SKIP_PACKAGE_STEP_SCHEMA
from thoth.python import PackageVersion
from thoth.python import Source

from .base import AdviserUnitPrescriptionTestCase


class TestSkipPackageStepPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to skip package step prescription."""

    @pytest.mark.parametrize(
        "package_version_from_version,package_version_from_index,package_version_from_develop,"
        "register_dependency,pipeline_run",
        [
            ("<=0.25.0", "https://pypi.org/simple", "false", True, True),
            (">0.25.0", "https://pypi.org/simple", "false", True, False),  # Version not matching.
            ("<=0.25.0", '{"not": "https://pypi.org/simple"}', "false", True, False),  # Index not matching.
            ("<=0.25.0", "https://pypi.org/simple", "true", True, False),  # Develop flag not matching.
            ("<=0.25.0", "https://pypi.org/simple", "false", False, False),  # Dependency is not registered.
        ],
    )
    def test_run_package_version_from(
        self,
        context: Context,
        state: State,
        package_version_from_version: str,
        package_version_from_index: str,
        package_version_from_develop: str,
        register_dependency: bool,
        pipeline_run: bool,
    ) -> None:
        """Test running the prescription based on the dependency introduced."""
        prescription_str = f"""
name: SkipPackageStep
type: step.SkipPackage
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
  state:
    package_version_from:
    - name: scikit-learn
      version: "{package_version_from_version}"
      develop: {package_version_from_develop}
      index_url: {package_version_from_index}
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SKIP_PACKAGE_STEP_SCHEMA(prescription)
        SkipPackageStepPrescription.set_prescription(prescription)

        pypi = Source("https://pypi.org/simple")
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=pypi,
            develop=False,
        )

        package_version_from = PackageVersion(
            name="scikit-learn",
            version="==0.24.2",
            index=pypi,
            develop=False,
        )

        state.add_resolved_dependency(package_version_from.to_tuple())
        context.register_package_version(package_version_from)

        if register_dependency:
            runtime_env = context.project.runtime_environment
            context.register_package_tuple(
                package_version.to_tuple(),
                dependent_tuple=package_version_from.to_tuple(),
                develop=False,
                extras=None,
                os_name=runtime_env.operating_system.name,
                os_version=runtime_env.operating_system.version,
                python_version=runtime_env.python_version,
            )

        unit = SkipPackageStepPrescription()
        unit.pre_run()

        with unit.assigned_context(context):
            if pipeline_run:
                with pytest.raises(SkipPackage):
                    unit.run(state, package_version)
            else:
                assert unit.run(state, package_version) is None

    @pytest.mark.parametrize(
        "package_version_from_version,package_version_from_index,package_version_from_develop,"
        "resolved_version,resolved_index,resolved_develop,"
        "add_resolved,pipeline_run",
        [
            ("<=0.25.0", "https://pypi.org/simple", "false", "==8.0.0", "https://pypi.org/simple", "false", True, True),
            # Version not matching.
            (">0.25.0", "https://pypi.org/simple", "false", "==8.0.0", "https://pypi.org/simple", "false", True, False),
            # Index not matching.
            (
                "<=0.25.0",
                '{"not": "https://pypi.org/simple"}',
                "false",
                "==8.0.0",
                "https://pypi.org/simple",
                "false",
                True,
                False,
            ),
            # Develop flag not matching.
            ("<=0.25.0", "https://pypi.org/simple", "true", "==8.0.0", "https://pypi.org/simple", "false", True, False),
            # Version not matching.
            (
                "<=0.25.0",
                "https://pypi.org/simple",
                "false",
                "!=8.0.0",
                "https://pypi.org/simple",
                "false",
                True,
                False,
            ),
            # Index not matching.
            (
                "<=0.25.0",
                "https://pypi.org/simple",
                "false",
                "==8.0.0",
                '{"not": "https://pypi.org/simple"}',
                "false",
                True,
                False,
            ),
            # Develop flag not matching.
            ("<=0.25.0", "https://pypi.org/simple", "false", "==8.0.0", "https://pypi.org/simple", "true", True, False),
            # Resolved dependency nit present.
            (
                "<=0.25.0",
                "https://pypi.org/simple",
                "false",
                "==8.0.0",
                "https://pypi.org/simple",
                "false",
                False,
                False,
            ),
        ],
    )
    def test_run_package_version_from_with_resolved(
        self,
        context: Context,
        state: State,
        package_version_from_version: str,
        package_version_from_index: str,
        package_version_from_develop: str,
        resolved_version: str,
        resolved_index: str,
        resolved_develop: str,
        add_resolved: bool,
        pipeline_run: bool,
    ) -> None:
        """Test running the prescription based on the dependency introduced."""
        prescription_str = f"""
name: SkipPackageStep
type: step.SkipPackage
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
  state:
    package_version_from:
    - name: scikit-learn
      version: "{package_version_from_version}"
      develop: {package_version_from_develop}
      index_url: {package_version_from_index}
    resolved_dependencies:
    - name: click
      version: "{resolved_version}"
      develop: {resolved_develop}
      index_url: {resolved_index}
run:
  stack_info:
  - type: WARNING
    message: A warning message
    link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_SKIP_PACKAGE_STEP_SCHEMA(prescription)
        SkipPackageStepPrescription.set_prescription(prescription)

        pypi = Source("https://pypi.org/simple")
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=pypi,
            develop=False,
        )

        package_version_from = PackageVersion(
            name="scikit-learn",
            version="==0.24.2",
            index=pypi,
            develop=False,
        )

        package_version_resolved = PackageVersion(
            name="click",
            version="==8.0.0",
            index=pypi,
            develop=False,
        )

        state.add_resolved_dependency(package_version_from.to_tuple())
        context.register_package_version(package_version_from)

        if add_resolved:
            state.add_resolved_dependency(package_version_resolved.to_tuple())
            context.register_package_version(package_version_resolved)

        runtime_env = context.project.runtime_environment
        context.register_package_tuple(
            package_version.to_tuple(),
            dependent_tuple=package_version_from.to_tuple(),
            develop=False,
            extras=None,
            os_name=runtime_env.operating_system.name,
            os_version=runtime_env.operating_system.version,
            python_version=runtime_env.python_version,
        )

        context.stack_info.clear()

        unit = SkipPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            if pipeline_run:
                with pytest.raises(SkipPackage):
                    unit.run(state, package_version)

                # Run one more time to verify the stack info is added just once.
                with pytest.raises(SkipPackage):
                    unit.run(state, package_version)
            else:
                assert unit.run(state, package_version) is None

        if pipeline_run:
            assert self.verify_justification_schema(context.stack_info)
            assert len(context.stack_info) == 1
            assert context.stack_info == [
                {"type": "WARNING", "link": "https://thoth-station.ninja", "message": "A warning message"}
            ]
        else:
            assert not context.stack_info
