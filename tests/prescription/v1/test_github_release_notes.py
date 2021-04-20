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

import yaml

from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.prescription.v1 import GitHubReleaseNotesWrapPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_SCHEMA

from .base import AdviserUnitPrescriptionTestCase


class TestGitHubReleaseNotesWrapPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to wrap prescription v1."""

    def test_run_no_resolved(self, context: Context, state: State) -> None:
        """Test running this pipeline unit not matching any resolved dependency."""
        prescription_str = """
name: GitHubReleaseNotes
type: wrap.GitHubReleaseNotes
should_include:
  adviser_pipeline: true
run:
  release_notes:
    - organization: thoth-station
      repository: adviser
      tag_version_prefix: v
      package_version:
        name: adviser
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_SCHEMA(prescription)
        GitHubReleaseNotesWrapPrescription.set_prescription(prescription)

        state.resolved_dependencies.clear()
        state.add_resolved_dependency(("flask", "1.0.0", "https://pypi.org/simple"))
        state.justification.clear()

        unit = GitHubReleaseNotesWrapPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert state.justification == []

    def test_run_add_justification(self, context: Context, state: State) -> None:
        """Test running this pipeline unit resulting in a justification addition."""
        prescription_str = """
name: GitHubReleaseNotes
type: wrap.GitHubReleaseNotes
should_include:
  adviser_pipeline: true
run:
  release_notes:
    - organization: thoth-station
      repository: adviser
      tag_version_prefix: v
      package_version:
        name: thoth-adviser
    - organization: thoth-station
      repository: common
      tag_version_prefix: v
      package_version:
        name: thoth-common
        version: '>=1.0.0'
    - organization: thoth-station
      repository: solver
      tag_version_prefix: v
      package_version:
        name: thoth-solver
        index_url: https://thoth-station.ninja
    - organization: thoth-station
      repository: analyzer
      package_version:
        name: thoth-analyzer
        version: '~=1.0.0'
        index_url: https://pypi.org/simple
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_SCHEMA(prescription)
        GitHubReleaseNotesWrapPrescription.set_prescription(prescription)

        state.resolved_dependencies.clear()
        # Will NOT occur in the justification:
        state.add_resolved_dependency(("flask", "1.0.0", "https://pypi.org/simple"))  # Not listed.
        state.add_resolved_dependency(("thoth-common", "0.5.0", "https://pypi.org/simple"))  # No version match.
        state.add_resolved_dependency(("thoth-solver", "0.5.0", "https://pypi.org/simple"))  # No index match.
        # Will occur in the justification:
        state.add_resolved_dependency(("thoth-adviser", "1.0.0", "https://pypi.org/simple"))  # With v prefix.
        state.add_resolved_dependency(("thoth-analyzer", "1.0.1", "https://pypi.org/simple"))  # Without v prefix.
        state.justification.clear()

        unit = GitHubReleaseNotesWrapPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        self.verify_justification_schema(state.justification)
        assert set(tuple(i.items()) for i in state.justification) == {
            (
                ("type", "INFO"),
                ("message", "Release notes for package 'thoth-adviser'"),
                ("link", "https://github.com/thoth-station/adviser/releases/tag/v1.0.0"),
            ),
            (
                ("type", "INFO"),
                ("message", "Release notes for package 'thoth-analyzer'"),
                ("link", "https://github.com/thoth-station/analyzer/releases/tag/1.0.1"),
            ),
        }
