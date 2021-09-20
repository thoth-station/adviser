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

"""Test implementation of add package step."""

import yaml

import pytest

from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.prescription.v1 import AddPackageStepPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages.exceptions import NotFoundError

from .base import AdviserUnitPrescriptionTestCase


class TestAddPackageStepPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to add package step prescription."""

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
        """Test running the add package unit."""
        prescription_str = f"""
name: AddPackageStep
type: step.AddPackage
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
  package_version:
    name: daiquiri
    locked_version: ==2.0.0
    index_url: https://pypi.org/simple
    develop: true
  stack_info:
    - type: INFO
      message: "Hello, Thoth!"
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA(prescription)
        AddPackageStepPrescription.set_prescription(prescription)

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

        assert "dauiqiri" not in state.resolved_dependencies

        state.add_resolved_dependency(package_version_from.to_tuple())
        context.register_package_version(package_version_from)

        if add_resolved:
            state.add_resolved_dependency(package_version_resolved.to_tuple())
            context.register_package_version(package_version_resolved)

        runtime_env = context.project.runtime_environment
        runtime_env.operating_system.name = "rhel"
        runtime_env.operating_system.version = "8"
        runtime_env.python_version = "3.8"

        context.register_package_tuple(
            package_version.to_tuple(),
            dependent_tuple=package_version_from.to_tuple(),
            develop=False,
            extras=None,
            os_name=runtime_env.operating_system.name,
            os_version=runtime_env.operating_system.version,
            python_version=runtime_env.python_version,
        )

        pv_tuple = ("daiquiri", "2.0.0", "https://pypi.org/simple")

        if pipeline_run:
            context.graph.should_receive("python_package_version_exists").with_args(
                *pv_tuple, solver_name="solver-rhel-8-py38"
            ).and_return(True).once()
            context.graph.should_receive("is_python_package_index_enabled").with_args(
                "https://pypi.org/simple"
            ).and_return(True).once()

        unit = AddPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

        if pipeline_run:
            assert "daiquiri" in state.unresolved_dependencies
            assert set(state.unresolved_dependencies.get("daiquiri").values()) == {pv_tuple}
            pv = context.get_package_version(pv_tuple, graceful=True)
            assert pv is not None
            assert pv.to_tuple() == pv_tuple
            assert pv.develop is True
        else:
            assert "daiquiri" not in state.unresolved_dependencies
            assert state.unresolved_dependencies.get("daiquiri") is None

    def test_run_package_version_not_solved(self, context: Context, state: State) -> None:
        """Test running the prescription based on the dependency not solved."""
        prescription_str = f"""
name: AddPackageStep
type: step.AddPackage
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: "~=1.19.0"
  state:
    package_version_from:
    - name: scikit-learn
      version: "<=0.25.0"
      develop: false
      index_url: "https://pypi.org/simple"
    resolved_dependencies:
    - name: click
      version: "==8.0.0"
      develop: false
      index_url: https://pypi.org/simple
run:
  package_version:
    name: daiquiri
    locked_version: ==2.0.0
    index_url: https://pypi.org/simple
    develop: true
  stack_info:
    - type: INFO
      message: "Hello, Thoth!"
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA(prescription)
        AddPackageStepPrescription.set_prescription(prescription)

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

        assert "dauiqiri" not in state.resolved_dependencies

        state.add_resolved_dependency(package_version_from.to_tuple())
        context.register_package_version(package_version_from)

        state.add_resolved_dependency(package_version_resolved.to_tuple())
        context.register_package_version(package_version_resolved)

        runtime_env = context.project.runtime_environment
        runtime_env.operating_system.name = "rhel"
        runtime_env.operating_system.version = "8"
        runtime_env.python_version = "3.8"

        context.register_package_tuple(
            package_version.to_tuple(),
            dependent_tuple=package_version_from.to_tuple(),
            develop=False,
            extras=None,
            os_name=runtime_env.operating_system.name,
            os_version=runtime_env.operating_system.version,
            python_version=runtime_env.python_version,
        )

        pv_tuple = ("daiquiri", "2.0.0", "https://pypi.org/simple")

        context.graph.should_receive("python_package_version_exists").with_args(
            *pv_tuple, solver_name="solver-rhel-8-py38"
        ).and_return(False).once()

        unit = AddPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

        assert "daiquiri" not in state.unresolved_dependencies
        assert state.unresolved_dependencies.get("daiquiri") is None

    def test_run_package_version_index_url_not_enabled(self, context: Context, state: State) -> None:
        """Test running the prescription based on the dependency introduced when index_url is not enabled."""
        prescription_str = f"""
name: AddPackageStep
type: step.AddPackage
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: "~=1.19.0"
  state:
    package_version_from:
    - name: scikit-learn
      version: "<=0.25.0"
      develop: false
      index_url: "https://pypi.org/simple"
    resolved_dependencies:
    - name: click
      version: "==8.0.0"
      develop: false
      index_url: https://pypi.org/simple
run:
  package_version:
    name: daiquiri
    locked_version: ==2.0.0
    index_url: https://pypi.org/simple
    develop: true
  stack_info:
    - type: INFO
      message: "Hello, Thoth!"
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA(prescription)
        AddPackageStepPrescription.set_prescription(prescription)

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

        assert "dauiqiri" not in state.resolved_dependencies

        state.add_resolved_dependency(package_version_from.to_tuple())
        context.register_package_version(package_version_from)

        state.add_resolved_dependency(package_version_resolved.to_tuple())
        context.register_package_version(package_version_resolved)

        runtime_env = context.project.runtime_environment
        runtime_env.operating_system.name = "rhel"
        runtime_env.operating_system.version = "8"
        runtime_env.python_version = "3.8"

        context.register_package_tuple(
            package_version.to_tuple(),
            dependent_tuple=package_version_from.to_tuple(),
            develop=False,
            extras=None,
            os_name=runtime_env.operating_system.name,
            os_version=runtime_env.operating_system.version,
            python_version=runtime_env.python_version,
        )

        pv_tuple = ("daiquiri", "2.0.0", "https://pypi.org/simple")

        context.graph.should_receive("python_package_version_exists").with_args(
            *pv_tuple, solver_name="solver-rhel-8-py38"
        ).and_return(True).once()
        context.graph.should_receive("is_python_package_index_enabled").with_args("https://pypi.org/simple").and_return(
            False
        ).once()

        unit = AddPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

        assert "daiquiri" not in state.unresolved_dependencies
        assert state.unresolved_dependencies.get("daiquiri") is None

    def test_run_package_version_index_url_not_known(self, context: Context, state: State) -> None:
        """Test running the prescription based on the dependency introduced when index_url is not known."""
        prescription_str = f"""
name: AddPackageStep
type: step.AddPackage
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: "~=1.19.0"
  state:
    package_version_from:
    - name: scikit-learn
      version: "<=0.25.0"
      develop: false
      index_url: "https://pypi.org/simple"
    resolved_dependencies:
    - name: click
      version: "==8.0.0"
      develop: false
      index_url: https://pypi.org/simple
run:
  package_version:
    name: daiquiri
    locked_version: ==2.0.0
    index_url: https://pypi.org/simple
    develop: true
  stack_info:
    - type: INFO
      message: "Hello, Thoth!"
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA(prescription)
        AddPackageStepPrescription.set_prescription(prescription)

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

        assert "dauiqiri" not in state.resolved_dependencies

        state.add_resolved_dependency(package_version_from.to_tuple())
        context.register_package_version(package_version_from)

        state.add_resolved_dependency(package_version_resolved.to_tuple())
        context.register_package_version(package_version_resolved)

        runtime_env = context.project.runtime_environment
        runtime_env.operating_system.name = "rhel"
        runtime_env.operating_system.version = "8"
        runtime_env.python_version = "3.8"

        context.register_package_tuple(
            package_version.to_tuple(),
            dependent_tuple=package_version_from.to_tuple(),
            develop=False,
            extras=None,
            os_name=runtime_env.operating_system.name,
            os_version=runtime_env.operating_system.version,
            python_version=runtime_env.python_version,
        )

        pv_tuple = ("daiquiri", "2.0.0", "https://pypi.org/simple")

        context.graph.should_receive("python_package_version_exists").with_args(
            *pv_tuple, solver_name="solver-rhel-8-py38"
        ).and_return(True).once()
        context.graph.should_receive("is_python_package_index_enabled").with_args("https://pypi.org/simple").and_raise(
            NotFoundError
        ).once()

        unit = AddPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

        assert "daiquiri" not in state.unresolved_dependencies
        assert state.unresolved_dependencies.get("daiquiri") is None

    def test_run_package_version_already_resolved(self, context: Context, state: State) -> None:
        """Test running the prescription when the given package is already in the resolved state."""
        prescription_str = f"""
name: AddPackageStep
type: step.AddPackage
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: "~=1.19.0"
  state:
    package_version_from:
    - name: scikit-learn
      version: "<=0.25.0"
      develop: false
      index_url: "https://pypi.org/simple"
    resolved_dependencies:
    - name: click
      version: "==8.0.0"
      develop: false
      index_url: https://pypi.org/simple
run:
  package_version:
    name: daiquiri
    locked_version: ==2.0.0
    index_url: https://pypi.org/simple
    develop: true
  stack_info:
    - type: INFO
      message: "Hello, Thoth!"
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA(prescription)
        AddPackageStepPrescription.set_prescription(prescription)

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

        pv_daiquiri = PackageVersion(
            name="daiquiri",
            version="==2.0.0",
            index=pypi,
            develop=False,
        )

        pv_tuple = ("daiquiri", "2.0.0", "https://pypi.org/simple")

        state.add_resolved_dependency(pv_tuple)
        context.register_package_version(pv_daiquiri)

        state.add_resolved_dependency(package_version_from.to_tuple())
        context.register_package_version(package_version_from)

        state.add_resolved_dependency(package_version_resolved.to_tuple())
        context.register_package_version(package_version_resolved)

        runtime_env = context.project.runtime_environment
        runtime_env.operating_system.name = "rhel"
        runtime_env.operating_system.version = "8"
        runtime_env.python_version = "3.8"

        context.register_package_tuple(
            package_version.to_tuple(),
            dependent_tuple=package_version_from.to_tuple(),
            develop=False,
            extras=None,
            os_name=runtime_env.operating_system.name,
            os_version=runtime_env.operating_system.version,
            python_version=runtime_env.python_version,
        )

        unit = AddPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

        assert "daiquiri" not in state.unresolved_dependencies
        assert "daiquiri" in state.resolved_dependencies

    def test_run_package_version_already_resolved_same_name(self, context: Context, state: State) -> None:
        """Test running the prescription when the given package is already in the resolved state (same name)."""
        prescription_str = f"""
name: AddPackageStep
type: step.AddPackage
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: "~=1.19.0"
  state:
    package_version_from:
    - name: scikit-learn
      version: "<=0.25.0"
      develop: false
      index_url: "https://pypi.org/simple"
    resolved_dependencies:
    - name: click
      version: "==8.0.0"
      develop: false
      index_url: https://pypi.org/simple
run:
  package_version:
    name: daiquiri
    locked_version: ==2.0.0
    index_url: https://pypi.org/simple
    develop: true
  stack_info:
    - type: INFO
      message: "Hello, Thoth!"
      link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA(prescription)
        AddPackageStepPrescription.set_prescription(prescription)

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

        pv_daiquiri = PackageVersion(
            name="daiquiri",
            version="==2.5.0",
            index=pypi,
            develop=False,
        )

        pv_tuple = ("daiquiri", "2.5.0", "https://pypi.org/simple")

        state.add_resolved_dependency(pv_tuple)
        context.register_package_version(pv_daiquiri)

        state.add_resolved_dependency(package_version_from.to_tuple())
        context.register_package_version(package_version_from)

        state.add_resolved_dependency(package_version_resolved.to_tuple())
        context.register_package_version(package_version_resolved)

        runtime_env = context.project.runtime_environment
        runtime_env.operating_system.name = "rhel"
        runtime_env.operating_system.version = "8"
        runtime_env.python_version = "3.8"

        context.register_package_tuple(
            package_version.to_tuple(),
            dependent_tuple=package_version_from.to_tuple(),
            develop=False,
            extras=None,
            os_name=runtime_env.operating_system.name,
            os_version=runtime_env.operating_system.version,
            python_version=runtime_env.python_version,
        )

        unit = AddPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

        assert "daiquiri" not in state.unresolved_dependencies
        assert "daiquiri" in state.resolved_dependencies
        assert set(state.resolved_dependencies["daiquiri"]) == set(pv_tuple)

    def test_run_package_version_add_package_multi(self, context: Context, state: State) -> None:
        """Test running the unit multiple times with stack info and justification reported once."""
        prescription_str = f"""
name: AddPackageStep
type: step.AddPackage
should_include:
  adviser_pipeline: true
match:
  package_version:
    name: numpy
run:
  package_version:
    name: daiquiri
    locked_version: ==2.0.0
    index_url: https://pypi.org/simple
    develop: true
  stack_info:
  - type: INFO
    message: "Hello, Thoth!"
    link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA(prescription)
        AddPackageStepPrescription.set_prescription(prescription)

        pypi = Source("https://pypi.org/simple")
        package_version_np = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=pypi,
            develop=False,
        )

        context.stack_info.clear()

        context.graph.should_receive("python_package_version_exists").with_args(
            "daiquiri", "2.0.0", "https://pypi.org/simple", solver_name="solver-rhel-8-py38"
        ).and_return(True).once()
        context.graph.should_receive("is_python_package_index_enabled").with_args("https://pypi.org/simple").and_return(
            True
        ).once()

        state.resolved_dependencies.clear()

        runtime_env = context.project.runtime_environment
        runtime_env.operating_system.name = "rhel"
        runtime_env.operating_system.version = "8"
        runtime_env.python_version = "3.8"

        unit = AddPackageStepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version_np) is None

        assert "daiquiri" in state.unresolved_dependencies
        assert set(state.unresolved_dependencies["daiquiri"].values()) == {
            ("daiquiri", "2.0.0", "https://pypi.org/simple")
        }

        assert context.stack_info == [
            {"type": "INFO", "message": "Hello, Thoth!", "link": "https://thoth-station.ninja"}
        ]

        package_version_np2 = PackageVersion(
            name="numpy",
            version="==2.0.0",
            index=pypi,
            develop=False,
        )

        context.graph.should_receive("python_package_version_exists").with_args(
            "daiquiri", "2.0.0", "https://pypi.org/simple", solver_name="solver-rhel-8-py38"
        ).and_return(True).once()
        context.graph.should_receive("is_python_package_index_enabled").with_args("https://pypi.org/simple").and_return(
            True
        ).once()

        state.resolved_dependencies.clear()

        runtime_env = context.project.runtime_environment
        runtime_env.operating_system.name = "rhel"
        runtime_env.operating_system.version = "8"
        runtime_env.python_version = "3.8"

        with unit.assigned_context(context):
            assert unit.run(state, package_version_np2) is None

        assert set(state.unresolved_dependencies["daiquiri"].values()) == {
            ("daiquiri", "2.0.0", "https://pypi.org/simple")
        }
        assert context.stack_info == [
            {"type": "INFO", "message": "Hello, Thoth!", "link": "https://thoth-station.ninja"}
        ]
