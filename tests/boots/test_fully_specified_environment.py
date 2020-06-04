#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""Test fully specified software environment boot."""

import pytest

from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.boots import FullySpecifiedEnvironment
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from ..base import AdviserTestCase


class TestFullySpecifiedEnvironment(AdviserTestCase):
    """Test fully specified software environment boot."""

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit for adviser runs."""
        builder_context.should_receive("is_adviser_pipeline").and_return(True)

        assert FullySpecifiedEnvironment.should_include(builder_context) == {}

        builder_context.add_unit(FullySpecifiedEnvironment())

        assert FullySpecifiedEnvironment.should_include(builder_context) is None

    def test_should_include_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test not registering the pipeline unit."""
        builder_context.should_receive("is_adviser_pipeline").and_return(False)
        assert FullySpecifiedEnvironment.should_include(builder_context) is None

    def test_run(self, context: Context) -> None:
        """Test if the given software environment is fully specified."""
        context.project.runtime_environment.should_receive("is_fully_specified").and_return(True)

        unit = FullySpecifiedEnvironment()
        with unit.assigned_context(context):
            assert unit.run() is None

    def test_run_error(self, context: Context) -> None:
        """Test raising no exception raised if the given software environment is not fully specified."""
        context.project.runtime_environment.should_receive("is_fully_specified").and_return(False)

        unit = FullySpecifiedEnvironment()
        with pytest.raises(NotAcceptable):
            with unit.assigned_context(context):
                unit.run()
