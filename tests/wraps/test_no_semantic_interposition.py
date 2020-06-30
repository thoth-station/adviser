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

"""Test wrap recommending Python3.8 on RHEL/UBI 8.2."""

import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import NoSemanticInterpositionWrap

from ..base import AdviserTestCase


class TestNoSemanticInterpositionWrap(AdviserTestCase):
    """Test recommending Python3.8 on RHEL/UBI 8.2."""

    @pytest.mark.parametrize("os_name,os_version,python_version", [("rhel", "8.2", "3.6"), ("ubi", "8.2", "3.7"),])
    def test_include(
        self, builder_context: PipelineBuilderContext, os_name: str, os_version: str, python_version: str
    ) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = RecommendationType.STABLE
        builder_context.project.runtime_environment.operating_system.name = os_name
        builder_context.project.runtime_environment.operating_system.version = os_version
        builder_context.project.runtime_environment.python_version = python_version
        assert builder_context.is_adviser_pipeline()
        assert NoSemanticInterpositionWrap.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "decision_type,recommendation_type,os_name,os_version,python_version",
        [
            (None, RecommendationType.LATEST, "rhel", "8.0", "3.8"),
            (None, RecommendationType.STABLE, "ubi", "8.0", "3.8"),
            (None, RecommendationType.LATEST, "rhel", "8.2", "3.8"),
            (None, RecommendationType.STABLE, "fedora", "32", "3.8"),
            (DecisionType.RANDOM, None, "rhel", "8.2", "3.6"),
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        decision_type: DecisionType,
        recommendation_type: RecommendationType,
        os_name: str,
        os_version: str,
        python_version: str,
    ) -> None:
        """Test not including this pipeline unit."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.operating_system.name = os_name
        builder_context.project.runtime_environment.operating_system.version = os_version
        builder_context.project.runtime_environment.python_version = python_version
        assert builder_context.is_adviser_pipeline() or builder_context.is_dependency_monkey_pipeline()
        assert NoSemanticInterpositionWrap.should_include(builder_context) is None

    def test_run(self, state: State) -> None:
        """Test running this wrap."""
        state = State()
        assert not state.justification

        unit = NoSemanticInterpositionWrap()
        unit.run(state)

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message"}
        assert state.justification[0]["type"] == "INFO"
        assert (
            state.justification[0]["message"]
            == "Consider using UBI or RHEL 8.2 with Python 3.8 that has optimized Python interpreter "
            "with performance gain up to 30%"
        )
