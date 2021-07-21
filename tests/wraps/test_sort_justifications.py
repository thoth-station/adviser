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

"""Test wrap that sorts justifications for better UX."""

from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import SortJustificationsWrap

from ..base import AdviserUnitTestCase


class TestSortPackageNameWrap(AdviserUnitTestCase):
    """Test wrap that sorts justifications for better UX."""

    UNIT_TESTED = SortJustificationsWrap

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.verify_multiple_should_include(builder_context)

    def test_run_add_justification(self) -> None:
        """Test sorting justifications.."""
        state = State()
        state.add_justification(
            [
                {
                    "type": "INFO",
                    "message": "Info about 'b'",
                    "link": "https://foo/bar",
                    "package_name": "b",
                },
                {
                    "type": "INFO",
                    "message": "Package 'a' in version '1.0.0'",
                    "link": "https://foo/bar",
                    "package_name": "a",
                },
                {
                    "type": "WARNING",
                    "message": "Some warning message printed not specific to any package",
                    "link": "https://foo/bar",
                },
                {
                    "type": "WARNING",
                    "message": "Warning about 'a'",
                    "link": "https://foo/bar",
                    "package_name": "a",
                },
            ]
        )

        unit = self.UNIT_TESTED()
        unit.run(state)

        assert state.justification == [
            {
                "link": "https://foo/bar",
                "message": "Some warning message printed not specific to any package",
                "type": "WARNING",
            },
            {
                "link": "https://foo/bar",
                "message": "Package 'a' in version '1.0.0'",
                "package_name": "a",
                "type": "INFO",
            },
            {"link": "https://foo/bar", "message": "Warning about 'a'", "package_name": "a", "type": "WARNING"},
            {"link": "https://foo/bar", "message": "Info about 'b'", "package_name": "b", "type": "INFO"},
        ]
        self.verify_justification_schema(state.justification)
