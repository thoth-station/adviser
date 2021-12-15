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

"""Test a wrap that provides a link to Thoth Search UI for packages."""

from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.wraps import ThothSearchPackageWrap

from ..base import AdviserUnitTestCase


class TestThothSearchPackageWrap(AdviserUnitTestCase):
    """Test a wrap that provides a link to Thoth Search UI for packages."""

    UNIT_TESTED = ThothSearchPackageWrap

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.verify_multiple_should_include(builder_context)

    def test_run(self, context: Context, state: State) -> None:
        """Test propagating a link to Thoth Search UI."""
        search_package_url = "https://thoth-station.ninja/some/nice/url/{package_name}/summary/{package_version}/link"

        state.justification.clear()
        state.resolved_dependencies.clear()
        state.add_resolved_dependency(("flask", "2.0.2", "https://pypi.org/simple"))
        state.add_resolved_dependency(("thamos", "1.21.1", "https://thoth-station.ninja/simple"))

        unit = self.UNIT_TESTED(search_package_url=search_package_url)
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert state.justification == [
            {
                "link": "https://thoth-station.ninja/some/nice/url/flask/summary/2.0.2/link",
                "message": "Browse Thoth Search UI for 'flask==2.0.2'",
                "package_name": "flask",
                "type": "INFO",
            },
            {
                "link": "https://thoth-station.ninja/some/nice/url/thamos/summary/1.21.1/link",
                "message": "Browse Thoth Search UI for 'thamos==1.21.1'",
                "package_name": "thamos",
                "type": "INFO",
            },
        ]
