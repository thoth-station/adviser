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

"""Test implementation of GitHub release notes wrap."""

from typing import Generator

import flexmock
import pytest
import yaml

from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.prescription.v1 import GHReleaseNotesWrapPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_GH_RELEASE_NOTES_WRAP_SCHEMA
from thoth.python import PackageVersion
from thoth.python import Source

from .base import AdviserUnitPrescriptionTestCase


class TestGHReleaseNotesWrapPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to wrap prescription v1."""

    @staticmethod
    def _instantiate_gh_release_notes_wrap(
        prescription_str: str,
    ) -> Generator[GHReleaseNotesWrapPrescription, None, None]:
        """Instantiate GitHub release notes wrap to match desired configuration for testing purposes."""
        prescription = yaml.safe_load(prescription_str)

        PRESCRIPTION_GH_RELEASE_NOTES_WRAP_SCHEMA(prescription)
        GHReleaseNotesWrapPrescription.set_prescription(prescription)

        conf_generator = GHReleaseNotesWrapPrescription.should_include(
            builder_context=flexmock(is_included=lambda _: False)
        )
        for configuration in conf_generator:
            unit = GHReleaseNotesWrapPrescription()
            unit.update_configuration(configuration)
            yield unit

    def test_run_no_resolved(self, context: Context, state: State) -> None:
        """Test running this pipeline unit not matching any resolved dependency."""
        prescription_str = """
name: GHReleaseNotes
type: wrap.GHReleaseNotes
should_include:
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: numpy
run:
  release_notes:
    organization: thoth-station
    repository: adviser
    tag_version_prefix: v
"""
        units = list(self._instantiate_gh_release_notes_wrap(prescription_str))
        assert len(units) == 1, "Multiple units created, expected only one based on prescription"
        unit = units[0]

        state.resolved_dependencies.clear()
        state.add_resolved_dependency(("flask", "1.0.0", "https://pypi.org/simple"))
        state.justification.clear()

        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert state.justification == []

    def test_run_add_justification(self, context: Context, state: State) -> None:
        """Test running this pipeline unit resulting in a justification addition."""
        prescription_str = """
name: GHReleaseNotes
type: wrap.GHReleaseNotes
should_include:
  adviser_pipeline: true
match:
  - state:
     resolved_dependencies:
       - name: thoth-adviser
run:
  release_notes:
    organization: thoth-station
    repository: adviser
    tag_version_prefix: v
"""
        units = list(self._instantiate_gh_release_notes_wrap(prescription_str))
        assert len(units) == 1, "Multiple units created, expected only one based on prescription"
        unit = units[0]

        state.resolved_dependencies.clear()
        state.add_resolved_dependency(("flask", "1.0.0", "https://pypi.org/simple"))
        state.add_resolved_dependency(("thoth-adviser", "1.0.0", "https://pypi.org/simple"))
        state.justification.clear()

        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        self.verify_justification_schema(state.justification)
        assert set(tuple(i.items()) for i in state.justification) == {
            (
                ("type", "INFO"),
                ("message", "Release notes for package 'thoth-adviser'"),
                ("link", "https://github.com/thoth-station/adviser/releases/tag/v1.0.0"),
                ("package_name", "thoth-adviser"),
            ),
        }

    def test_run_not_index_url(self, context: Context, state: State) -> None:
        """Test running this pipeline unit resulting in a justification addition when "not" index url is used."""
        prescription_str = """
name: GHReleaseNotes
type: wrap.GHReleaseNotes
should_include:
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: thoth-solver
        index_url:
          not: https://thoth-station.ninja/simple
run:
  release_notes:
    organization: thoth-station
    repository: solver
"""
        units = list(self._instantiate_gh_release_notes_wrap(prescription_str))
        assert len(units) == 1, "Multiple units created, expected only one based on prescription"
        unit = units[0]

        state.resolved_dependencies.clear()
        state.justification.clear()

        state.add_resolved_dependency(("thoth-solver", "0.5.0", "https://pypi.org/simple"))

        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        self.verify_justification_schema(state.justification)
        assert set(tuple(i.items()) for i in state.justification) == {
            (
                ("type", "INFO"),
                ("message", "Release notes for package 'thoth-solver'"),
                ("link", "https://github.com/thoth-station/solver/releases/tag/0.5.0"),
                ("package_name", "thoth-solver"),
            ),
        }

    @pytest.mark.parametrize("develop", [True, False])
    def test_run_develop(self, context: Context, state: State, develop: bool) -> None:
        """Test running this pipeline unit resulting in a justification addition when "not" index url is used."""
        prescription_str = f"""
name: GHReleaseNotes
type: wrap.GHReleaseNotes
should_include:
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      name: thoth-solver
      develop: {'true' if develop else 'false'}
run:
  release_notes:
    organization: thoth-station
    repository: solver
    tag_version_prefix: v
"""
        units = list(self._instantiate_gh_release_notes_wrap(prescription_str))
        assert len(units) == 1, "Multiple units created, expected only one based on prescription"
        unit = units[0]

        state.resolved_dependencies.clear()
        state.justification.clear()

        package_version = PackageVersion(
            name="thoth-solver",
            version="==0.5.0",
            index=Source("https://pypi.org/simple"),
            develop=develop,
        )
        state.add_resolved_dependency(package_version.to_tuple())
        context.register_package_version(package_version)

        unit.pre_run()
        with unit.assigned_context(context):
            # Run twice to verify the justification is added just once.
            assert unit.run(state) is None
            assert unit.run(state) is None

        self.verify_justification_schema(state.justification)
        assert set(tuple(i.items()) for i in state.justification) == {
            (
                ("type", "INFO"),
                ("message", "Release notes for package 'thoth-solver'"),
                ("link", "https://github.com/thoth-station/solver/releases/tag/v0.5.0"),
                ("package_name", "thoth-solver"),
            ),
        }

    @pytest.mark.parametrize("develop", [True, False])
    def test_run_develop_no_match(self, context: Context, state: State, develop: bool) -> None:
        """Test running this pipeline unit resulting in a justification addition when "not" index url is used."""
        prescription_str = f"""
name: GHReleaseNotes
type: wrap.GHReleaseNotes
should_include:
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      name: thoth-solver
      develop: {'true' if develop else 'false'}
run:
  release_notes:
    organization: thoth-station
    repository: solver
    tag_version_prefix: v
"""
        units = list(self._instantiate_gh_release_notes_wrap(prescription_str))
        assert len(units) == 1, "Multiple units created, expected only one based on prescription"
        unit = units[0]

        state.resolved_dependencies.clear()
        state.justification.clear()

        package_version = PackageVersion(
            name="thoth-solver",
            version="==0.5.0",
            index=Source("https://pypi.org/simple"),
            develop=not develop,
        )
        state.add_resolved_dependency(package_version.to_tuple())
        context.register_package_version(package_version)

        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert not state.justification

    @pytest.mark.parametrize(
        "version_expected,version_provided,include",
        [
            ("~=2.26.0", "2.26.1", True),
            ("~=1.0.0", "2.26.1", False),
        ],
    )
    def test_run_version(
        self, context: Context, state: State, version_expected: str, version_provided: str, include: bool
    ) -> None:
        """Test running this pipeline unit resulting in a justification addition when "not" index url is used."""
        prescription_str = f"""
name: GHReleaseNotes
type: wrap.GHReleaseNotes
should_include:
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      name: requests
      version: '{version_expected}'
run:
  release_notes:
    organization: psf
    repository: requests
"""
        units = list(self._instantiate_gh_release_notes_wrap(prescription_str))
        assert len(units) == 1, "Multiple units created, expected only one based on prescription"
        unit = units[0]

        state.resolved_dependencies.clear()
        state.justification.clear()

        package_version = PackageVersion(
            name="requests",
            version=f"=={version_provided}",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )
        state.add_resolved_dependency(package_version.to_tuple())
        context.register_package_version(package_version)

        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert len(state.justification) == int(include)

    def test_instantiate_multiple(self) -> None:
        """Test instantiating multiple GitHub release notes wraps from a single prescription."""
        prescription_str = f"""
name: GHReleaseNotes
type: wrap.GHReleaseNotes
should_include:
  adviser_pipeline: true
match:
  - state:
      resolved_dependencies:
        name: requests-fork
        index_url: https://pypi.org/simple
  - state:
      resolved_dependencies:
        name: requests
run:
  release_notes:
    organization: psf
    repository: requests
"""
        units = list(self._instantiate_gh_release_notes_wrap(prescription_str))
        assert len(units) == 2
        assert units[0].configuration["prescription"] is units[1].configuration["prescription"]

        assert units[0].configuration == {
            "package_name": "requests-fork",
            "package_version": {"index_url": "https://pypi.org/simple", "name": "requests-fork"},
            "release_notes": {"organization": "psf", "repository": "requests"},
            "prescription": {"run": False},
        }
        assert units[1].configuration == {
            "package_name": "requests",
            "package_version": {"name": "requests"},
            "release_notes": {"organization": "psf", "repository": "requests"},
            "prescription": {"run": False},
        }
