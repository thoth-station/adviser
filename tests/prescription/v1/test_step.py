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

from flexmock import flexmock
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
match:
  package_version:
    index_url: 'https://thoth-station.ninja/simple'
run:
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
match:
  package_version:
    name: flask
run:
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
match:
  package_version:
    name: flask
    version: "<1.0.0"
run:
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
match:
  package_version:
      name: flask
      version: "~=0.0"
      index_url: "https://pypi.org/simple"
run:
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
match:
  package_version:
    name: pysaml2
    version: '<6.5.0'
    index_url: 'https://pypi.org/simple'
run:
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

            # Run one more time to make sure justification is added only once.
            result = unit.run(state, package_version)
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert result[0] == -0.1
            assert result[1] is None

    def test_run_state(self, context: Context, state: State) -> None:
        """Test running the prescription if state matches."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: '==1.19.1'
    index_url: 'https://pypi.org/simple'
  state:
    resolved_dependencies:
      - name: tensorflow
        version: '~=2.4.0'
run:
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
match:
  package_version:
    name: numpy
    version: '==1.19.1'
    index_url: 'https://pypi.org/simple'
  state:
    resolved_dependencies:
      - name: tensorflow
        version: '~=2.4.0'
run:
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

    def test_should_include_package_name(self) -> None:
        """Test including this pipeline unit."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  - package_version:
      name: numpy
      version: '==1.19.1'
      index_url: 'https://pypi.org/simple'
run:
  multi_package_resolution: true
  score: 0.1
"""
        flexmock(StepPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)

        builder_context = flexmock()
        result = list(StepPrescription.should_include(builder_context))
        assert result == [
            {
                "package_name": "numpy",
                "multi_package_resolution": True,
                "prescription": {
                    "run": False,
                },
                "match": {
                    "package_version": {
                        "name": "numpy",
                        "version": "==1.19.1",
                        "index_url": "https://pypi.org/simple",
                    },
                },
                "run": {
                    "score": 0.1,
                    "multi_package_resolution": True,
                },
            }
        ]

    def test_should_include_no_package_name(self) -> None:
        """Test including this pipeline unit."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    index_url: 'https://thoth-station.ninja'
run:
  score: 0.1
"""
        flexmock(StepPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(StepPrescription.should_include(builder_context)) == [
            {
                "package_name": None,
                "prescription": {
                    "run": False,
                },
                "match": {
                    "package_version": {
                        "index_url": "https://thoth-station.ninja",
                    },
                },
                "multi_package_resolution": False,
                "run": {
                    "score": 0.1,
                },
            }
        ]

    def test_should_include_multi(self) -> None:
        """Test including this pipeline unit multiple times."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  - package_version:
      index_url: 'https://thoth-station.ninja'
  - package_version:
      name: flask
run:
  score: 0.1
"""
        flexmock(StepPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)

        builder_context = flexmock()
        result = list(StepPrescription.should_include(builder_context))
        assert result == [
            {
                "package_name": None,
                "multi_package_resolution": False,
                "prescription": {
                    "run": False,
                },
                "match": {
                    "package_version": {
                        "index_url": "https://thoth-station.ninja",
                    }
                },
                "run": {
                    "score": 0.1,
                },
            },
            {
                "package_name": "flask",
                "multi_package_resolution": False,
                "prescription": {
                    "run": False,
                },
                "match": {
                    "package_version": {
                        "name": "flask",
                    }
                },
                "run": {
                    "score": 0.1,
                },
            },
        ]
        assert result[0]["prescription"] is result[1]["prescription"]

    def test_no_should_include(self) -> None:
        """Test not including this pipeline."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    index_url: 'https://thoth-station.ninja'
run:
  score: 0.1
"""
        flexmock(StepPrescription).should_receive("_should_include_base").replace_with(lambda _: False).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(StepPrescription.should_include(builder_context)) == []

    def test_run_state_not_index_url(self, context: Context, state: State) -> None:
        """Test running the prescription if state matches."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: '==1.19.1'
    index_url:
      not: 'https://pypi.org/simple'
  state:
    resolved_dependencies:
      - name: tensorflow
        version: '~=2.4.0'
        index_url:
          not: 'https://pypi.org/simple'
run:
  score: 0.5
  stack_info:
  - type: WARNING
    message: Hello, Thoth!
    link: https://thoth-station.ninja
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=Source("https://thoth-station.ninja/simple"),
            develop=False,
        )

        state.add_resolved_dependency(("tensorflow", "2.4.0", "https://thoth-station.ninja/simple"))

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)
            assert isinstance(result, tuple)
            assert result[0] == 0.5
            assert result[1] is None

            self.verify_justification_schema(context.stack_info)
            assert context.stack_info == [
                {"type": "WARNING", "message": "Hello, Thoth!", "link": "https://thoth-station.ninja"}
            ]

            # Run one more time to make sure stack info is added just once.
            result = unit.run(state, package_version)
            assert isinstance(result, tuple)
            assert result[0] == 0.5
            assert result[1] is None
            assert context.stack_info == [
                {"type": "WARNING", "message": "Hello, Thoth!", "link": "https://thoth-station.ninja"}
            ]

    def test_run_state_not_index_url_not_match(self, context: Context, state: State) -> None:
        """Test running the prescription if state matches."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: '==1.19.1'
    index_url:
      not: 'https://pypi.org/simple'
  state:
    resolved_dependencies:
      - name: tensorflow
        version: '~=2.4.0'
        index_url:
          not: 'https://pypi.org/simple'
run:
  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=Source("https://pypi.org/simple"),  # This does match.
            develop=False,
        )

        state.add_resolved_dependency(("tensorflow", "2.4.0", "https://thoth-station.ninja/simple"))

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

    def test_run_state_not_index_url_not_match_state(self, context: Context, state: State) -> None:
        """Test running the prescription if state matches."""
        prescription_str = """
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    version: '==1.19.1'
    index_url:
      not: 'https://pypi.org/simple'
  state:
    resolved_dependencies:
      - name: tensorflow
        version: '~=2.4.0'
        index_url:
          not: 'https://pypi.org/simple'
run:
  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=Source("https://thoth-station.ninja/simple"),
            develop=False,
        )

        state.add_resolved_dependency(("tensorflow", "2.4.0", "https://pypi.org/simple"))  # This does match.

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

    @pytest.mark.parametrize("develop", [True, False])
    def test_run_develop_match(self, context: Context, state: State, develop: bool) -> None:
        """Test running the prescription if develop flag is set."""
        prescription_str = f"""
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    develop: {'true' if develop else 'false'}
run:
  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=Source("https://thoth-station.ninja/simple"),
            develop=develop,
        )

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)

        assert isinstance(result, tuple)
        assert result[0] == 0.5
        assert result[1] is None

    @pytest.mark.parametrize("develop", [True, False])
    def test_run_develop_not_match(self, context: Context, state: State, develop: bool) -> None:
        """Test not running the prescription if develop flag is set."""
        prescription_str = f"""
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    develop: {'true' if develop else 'false'}
run:
  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=Source("https://thoth-station.ninja/simple"),
            develop=not develop,
        )

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state, package_version) is None

    @pytest.mark.parametrize(
        "develop,state_develop",
        [
            (True, True),
            (False, True),
            (True, False),
            (False, False),
        ],
    )
    def test_run_develop_state_match(self, context: Context, state: State, develop: bool, state_develop: bool) -> None:
        """Test not running the prescription if develop flag is set also on the state match."""
        prescription_str = f"""
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
    develop: {'true' if develop else 'false'}
  state:
    resolved_dependencies:
    - name: pytest
      develop: {'true' if state_develop else 'false'}
run:
  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)
        package_version = PackageVersion(
            name="numpy",
            version="==1.19.1",
            index=Source("https://pypi.org/simple"),
            develop=develop,
        )

        state_package_version = PackageVersion(
            name="pytest",
            version="==6.2.4",
            index=Source("https://pypi.org/simple"),
            develop=state_develop,
        )
        state.add_resolved_dependency(state_package_version.to_tuple())
        context.register_package_version(state_package_version)

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)

        assert isinstance(result, tuple)
        assert result[0] == 0.5
        assert result[1] is None

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
name: StepUnit
type: step
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
run:
  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)

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

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)

        if pipeline_run:
            assert isinstance(result, tuple)
            assert result[0] == 0.5
            assert result[1] is None
        else:
            assert result is None

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
name: StepUnit
type: step
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
  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)

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

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)

        if pipeline_run:
            assert isinstance(result, tuple)
            assert result[0] == 0.5
            assert result[1] is None
        else:
            assert result is None

    @pytest.mark.parametrize("allow_other", [True, False])
    def test_run_package_version_from_with_other(self, context: Context, state: State, allow_other: bool) -> None:
        """Test running the prescription based on the dependency introduced without with considering other packages."""
        prescription_str = f"""
name: StepUnit
type: step
should_include:
  times: 1
  adviser_pipeline: true
match:
  package_version:
    name: numpy
  state:
    package_version_from_allow_other: {'true' if allow_other else 'false'}
    package_version_from:
    - name: scikit-learn
      version: "<1.0.0"
      develop: false
      index_url: https://pypi.org/simple
run:
  score: 0.5
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_STEP_SCHEMA(prescription)
        StepPrescription.set_prescription(prescription)

        pypi = Source("https://pypi.org/simple")

        package_version = PackageVersion(
            name="numpy",
            version="==1.19.4",
            index=pypi,
            develop=False,
        )

        package_version_other = PackageVersion(
            name="tensorflow",
            version="==2.6.0",
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

        state.add_resolved_dependency(package_version_other.to_tuple())
        context.register_package_version(package_version_other)

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

        context.register_package_tuple(
            package_version.to_tuple(),
            dependent_tuple=package_version_other.to_tuple(),
            develop=False,
            extras=None,
            os_name=runtime_env.operating_system.name,
            os_version=runtime_env.operating_system.version,
            python_version=runtime_env.python_version,
        )

        unit = StepPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            result = unit.run(state, package_version)

        if allow_other:
            assert isinstance(result, tuple)
            assert result[0] == 0.5
            assert result[1] is None
        else:
            assert result is None
