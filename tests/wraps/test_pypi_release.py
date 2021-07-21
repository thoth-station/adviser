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

"""Test wrap adding information about Python package releases."""

from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import PyPIReleaseWrap

from ..base import AdviserUnitTestCase


class TestPyPIReleaseWrap(AdviserUnitTestCase):
    """Test adding PyPI release information."""

    UNIT_TESTED = PyPIReleaseWrap

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.verify_multiple_should_include(builder_context)

    def test_run_add_justification(self) -> None:
        """Test adding link to PyPI about the given package released."""
        state = State()
        state.add_resolved_dependency(("tensorflow", "2.5.0", "https://pypi.org/simple"))

        unit = self.UNIT_TESTED()
        unit.run(state)

        assert state.justification == [
            {
                "type": "INFO",
                "message": "Package 'tensorflow' in version '2.5.0' is released on PyPI",
                "package_name": "tensorflow",
                "link": "https://pypi.org/project/tensorflow/2.5.0/",
            }
        ]
        self.verify_justification_schema(state.justification)

    def test_run_no_justification(self) -> None:
        """Test NOT adding information if the given Python package is not a PyPI release."""
        state = State()
        state.add_resolved_dependency(("tensorflow", "2.5.0", "https://thoth-station.ninja"))

        unit = self.UNIT_TESTED()
        unit.run(state)

        assert not state.justification
