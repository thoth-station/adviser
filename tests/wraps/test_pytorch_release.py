#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2022 Fridolin Pokorny
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

"""Test wrap adding a link to the PyTorch index."""

from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import PyTorchReleaseWrap

from ..base import AdviserUnitTestCase


class TestPyTorchReleaseWrap(AdviserUnitTestCase):
    """Test wrap adding a link to the PyTorch index."""

    UNIT_TESTED = PyTorchReleaseWrap

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.verify_multiple_should_include(builder_context)

    def test_run_add_justification(self) -> None:
        """Test adding a link to the PyTorch index."""
        state = State()
        package_version_tuple = ("torch", "1.10.2", f"{self.UNIT_TESTED._TORCH_INDEX_PREFIX}cpu")
        state.add_resolved_dependency(package_version_tuple)

        unit = self.UNIT_TESTED()
        unit.run(state)

        assert state.justification == [
            {
                "link": "https://download.pytorch.org/whl/cpu",
                "message": "Package 'torch' in version '1.10.2' is released on the PyTorch index",
                "package_name": "torch",
                "type": "INFO",
            },
        ]
        self.verify_justification_schema(state.justification)

    def test_run_no_justification(self) -> None:
        """Test NOT adding a link to the PyTorch index."""
        state = State()
        state.add_resolved_dependency(("torch", "1.10.2", "https://pypi.org/simple"))

        unit = self.UNIT_TESTED()
        unit.run(state)

        assert not state.justification
