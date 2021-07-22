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

"""Test wrap adding information about Red Hat's Pulp instance."""

from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import PulpReleaseWrap

from ..base import AdviserUnitTestCase


class TestPyPIReleaseWrap(AdviserUnitTestCase):
    """Test wrap adding information about Red Hat's Pulp instance."""

    UNIT_TESTED = PulpReleaseWrap

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.verify_multiple_should_include(builder_context)

    def test_run_add_justification(self) -> None:
        """Test adding a link to Pulp instance for the given package released."""
        state = State()
        package_version_tuple = ("tensorflow", "2.5.0", f"{self.UNIT_TESTED._PULP_URL}pypi/test/simple")
        state.add_resolved_dependency(package_version_tuple)

        unit = self.UNIT_TESTED()
        unit.run(state)

        assert state.justification == [
            {
                "type": "INFO",
                "message": f"Package {package_version_tuple[0]!r} is released on Operate First Pulp instance",
                "package_name": package_version_tuple[0],
                "link": package_version_tuple[2],
            }
        ]
        self.verify_justification_schema(state.justification)

    def test_run_no_justification(self) -> None:
        """Test NOT adding a link to Pulp instance for the given package released."""
        index_url = "https://pypi.org/simple"
        assert not self.UNIT_TESTED._PULP_URL.startswith(index_url)

        state = State()
        state.add_resolved_dependency(("tensorflow", "2.5.0", index_url))

        unit = self.UNIT_TESTED()
        unit.run(state)

        assert not state.justification
