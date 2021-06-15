#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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

"""Test filtering out software stacks based on version seen."""

import pytest

from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.exceptions import PipelineUnitConfigurationSchemaError
from thoth.adviser.state import State
from thoth.adviser.strides import OneVersionStride
from thoth.adviser.pipeline_builder import PipelineBuilderContext

from ..base import AdviserUnitTestCase


class TestOneVersionStride(AdviserUnitTestCase):
    """Test filtering out software stacks based on version seen."""

    UNIT_TESTED = OneVersionStride

    @pytest.mark.skip(reason="Stride for ensuring one version is never registered.")
    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""

    def test_default_configuration(self) -> None:
        """Test instantiation the pipeline unit fails with the default configuration."""
        unit_instance = self.UNIT_TESTED()
        with pytest.raises(PipelineUnitConfigurationSchemaError):
            unit_instance.update_configuration({})

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test no inclusion of this pipeline unit."""
        assert list(OneVersionStride.should_include(builder_context)) == []

    def test_pre_run_error(self) -> None:
        """Test error produced in pre-run if configuration is wrong."""
        unit = OneVersionStride()
        with pytest.raises(PipelineUnitConfigurationSchemaError):
            unit.update_configuration({})

        unit = OneVersionStride()
        with pytest.raises(PipelineUnitConfigurationSchemaError):
            unit.update_configuration({"package_name": None})

    def test_configuration_default(self) -> None:
        """Test default pipeline unit configuration."""
        unit = OneVersionStride()
        assert unit.configuration == {"package_name": None, "only_once": True}

    def test_run_only_once(self) -> None:
        """Test running this stride with only-once pipeline flag set."""
        unit = OneVersionStride()
        unit.update_configuration({"package_name": "tensorflow", "only_once": True})
        unit.pre_run()

        state1 = State(score=1.0)
        state1.add_resolved_dependency(("tensorflow", "2.0.0", "https://pypi.org/simple"))

        assert unit.run(state1) is None

        state2 = State(score=1.0)
        state2.add_resolved_dependency(("tensorflow", "2.0.0", "https://pypi.org/simple"))
        with pytest.raises(NotAcceptable):
            unit.run(state2)

        state3 = State(score=1.0)
        state3.add_resolved_dependency(("tensorflow", "2.1.0", "https://pypi.org/simple"))
        with pytest.raises(NotAcceptable):
            unit.run(state3)

    def test_run_no_only_once(self) -> None:
        """Test running this stride with only-once pipeline flag set."""
        unit = OneVersionStride()
        unit.update_configuration({"package_name": "tensorflow", "only_once": False})
        unit.pre_run()

        state1 = State(score=1.0)
        state1.add_resolved_dependency(("tensorflow", "2.0.0", "https://pypi.org/simple"))

        assert unit.run(state1) is None

        state2 = State(score=1.0)
        state2.add_resolved_dependency(("tensorflow", "2.0.0", "https://pypi.org/simple"))
        assert unit.run(state2) is None

        state3 = State(score=1.0)
        state3.add_resolved_dependency(("tensorflow", "2.1.0", "https://pypi.org/simple"))
        with pytest.raises(NotAcceptable):
            unit.run(state3)
