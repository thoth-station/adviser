#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

"""File conftest.py for pytest test suite."""

import pytest

from thoth.adviser.pipeline_config import PipelineConfig  # type: ignore
from .units.boots import Boot1
from .units.sieves import Sieve1
from .units.steps import Step1
from .units.strides import Stride1
from .units.wraps import Wrap1

from thoth.storages import GraphDatabase


@pytest.fixture
def pipeline_config() -> PipelineConfig:
    """A fixture for a pipeline configuration with few representatives of each pipeline unit type."""
    return PipelineConfig(
        boots=[Boot1()],
        sieves=[Sieve1()],
        steps=[Step1()],
        strides=[Stride1()],
        wraps=[Wrap1()],
    )


@pytest.fixture
def graph() -> GraphDatabase:
    """A knowledge graph connector fixture."""
    graph = GraphDatabase()
    graph.connect()
    return graph
