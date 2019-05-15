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

"""Test scoring based on performance index."""

import math

import flexmock

from thoth.adviser.python.pipeline import StrideContext
from thoth.adviser.python.pipeline.strides import PerformanceScoring
from thoth.adviser.isis import Isis
from thoth.storages import GraphDatabase
from thoth.common import RuntimeEnvironment

from base import AdviserTestCase


class TestPerformanceScoring(AdviserTestCase):
    """Test scoring based on performance index."""

    _CASE_STACK = [
        ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
        ("numpy", "1.16.2", "https://pypi.org/simple"),
        ("markdown", "3.1", "https://pypi.org/simple"),
    ]

    def test_score_multi(self):
        """Test scoring of performance based on a multiple packages affecting performance present in a stack."""
        stride_context = StrideContext(self._CASE_STACK)
        stride_context.adjust_score(3.0)  # Set some initial score.
        flexmock(GraphDatabase)

        GraphDatabase.should_receive(
            "compute_python_package_version_avg_performance"
        ).with_args(
            {
                ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                ("numpy", "1.16.2", "https://pypi.org/simple"),
            },
            runtime_environment={},
            hardware_specs=None,
        ).and_return(
            30.0
        )

        performance_impact = {
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): 1.0,
            ("numpy", "1.16.2", "https://pypi.org/simple"): 1.0,
            ("markdown", "3.1", "https://pypi.org/simple"): 0.0,
        }

        flexmock(Isis)
        Isis.should_receive("get_python_package_performance_impact_all").with_args(
            self._CASE_STACK
        ).and_return(performance_impact)

        project = flexmock(
            name="project", runtime_environment=RuntimeEnvironment.from_dict({})
        )
        performance_scoring = PerformanceScoring(
            graph=GraphDatabase(),
            project=project,
            library_usage=None,
        )
        self.run_async(performance_scoring.run(stride_context))
        assert (
            len(stride_context.justification) == 1
        ), "No justification adjustments found after scoring"
        assert stride_context.justification[0] == {
            "performance_score": 30.0
        }, "Justification for performance scoring is not propagated correctly"
        # Addition with the initial score.
        assert (
            stride_context.score == 33.0
        ), "Peformance score is not computed correctly"

    def test_score_single(self):
        """Test scoring of performance based on a single package version affecting performance present in a stack."""
        stride_context = StrideContext(self._CASE_STACK)
        flexmock(GraphDatabase)

        GraphDatabase.should_receive(
            "compute_python_package_version_avg_performance"
        ).with_args(
            {("tensorflow", "1.9.0", "https://thoth-station.ninja/simple")},
            runtime_environment={},
            hardware_specs=None,
        ).and_return(
            42.0
        )

        performance_impact = {
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): 1.0,
            ("numpy", "1.16.2", "https://pypi.org/simple"): 0.0,
            ("markdown", "3.1", "https://pypi.org/simple"): 0.0,
        }

        flexmock(Isis)
        Isis.should_receive("get_python_package_performance_impact_all").with_args(
            self._CASE_STACK
        ).and_return(performance_impact)

        project = flexmock(
            name="project", runtime_environment=RuntimeEnvironment.from_dict({})
        )
        performance_scoring = PerformanceScoring(
            graph=GraphDatabase(),
            project=project,
            library_usage=None,
        )
        self.run_async(performance_scoring.run(stride_context))
        assert (
            len(stride_context.justification) == 1
        ), "No changes to justification found"
        assert stride_context.justification[0] == {
            "performance_score": 42.0
        }, "Justification for performance scoring is not correct"
        # No initial score.
        assert stride_context.score == 42.0, "Score is not correctly computed"

    def test_no_score(self):
        """Test no performance information does not affect performance score."""
        stride_context = StrideContext(self._CASE_STACK)
        stride_context.adjust_score(3030.0)  # Set some initial score.
        flexmock(GraphDatabase)

        GraphDatabase.should_receive(
            "compute_python_package_version_avg_performance"
        ).with_args(
            {
                ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                ("numpy", "1.16.2", "https://pypi.org/simple"),
            },
            runtime_environment={},
            hardware_specs=None,
        ).and_return(
            math.nan
        )

        performance_impact = {
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): 1.0,
            ("numpy", "1.16.2", "https://pypi.org/simple"): 1.0,
            ("markdown", "3.1", "https://pypi.org/simple"): 0.0,
        }
        flexmock(Isis)
        Isis.should_receive("get_python_package_performance_impact_all").with_args(
            self._CASE_STACK
        ).and_return(performance_impact)

        project = flexmock(
            name="project", runtime_environment=RuntimeEnvironment.from_dict({})
        )
        performance_scoring = PerformanceScoring(
            graph=GraphDatabase(),
            project=project,
            library_usage=None,
        )
        self.run_async(performance_scoring.run(stride_context))
        assert (
            len(stride_context.justification) == 0
        ), "No justification expected if no changes were made"
        assert stride_context.score == 3030.0, "Score is not kept untouched"
