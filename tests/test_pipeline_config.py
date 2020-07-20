#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Test pipeline configuration and its manipulation."""

import flexmock

from thoth.adviser.pipeline_config import PipelineConfig
from thoth.adviser.report import Report

from .base import AdviserTestCase


class TestPipelineConfig(AdviserTestCase):
    """Test adviser pipeline configuration."""

    def test_to_dict(self, pipeline_config: PipelineConfig) -> None:
        """Test serialization of pipeline configuration."""
        assert pipeline_config.to_dict() == {
            "boots": [{"name": "Boot1", "configuration": {"some_parameter": -0.2}}],
            "sieves": [{"name": "Sieve1", "configuration": {"flying_circus": 1969}}],
            "steps": [{"name": "Step1", "configuration": {"guido_retirement": 2019}}],
            "strides": [
                {
                    "name": "Stride1",
                    "configuration": {"linus": {"residence": "oregon", "children": 3, "parents": ["nils", "anna"],}},
                }
            ],
            "wraps": [
                {
                    "name": "Wrap1",
                    "configuration": {"thoth": [2018, 2019], "cities": ["Brno", "Bonn", "Boston", "Milan"],},
                }
            ],
        }

    def test_iter_units(self, pipeline_config: PipelineConfig) -> None:
        """Test iteration over all units present in the pipeline configuration."""
        visited = dict.fromkeys(("Boot1", "Sieve1", "Step1", "Stride1", "Wrap1"), 0)
        for unit in pipeline_config.iter_units():
            assert unit.__class__.__name__ in visited, f"Unknown unit {unit.__class__.__name__!r}"
            visited[unit.__class__.__name__] += 1

        assert len(visited) == 5
        assert list(visited.values()) == [1] * 5

    def test_call_pre_run(self, pipeline_config: PipelineConfig) -> None:
        """Test calling pre-run method on units."""
        for unit in pipeline_config.iter_units():
            flexmock(unit).should_receive("pre_run").with_args().and_return(None).once()

        pipeline_config.call_pre_run()

    def test_call_post_run(self, pipeline_config: PipelineConfig) -> None:
        """Test calling post-run method on units."""
        for unit in pipeline_config.iter_units():
            flexmock(unit).should_receive("post_run").with_args().and_return(None).once()

        pipeline_config.call_post_run()

    def test_call_post_run_report(self, pipeline_config: PipelineConfig) -> None:
        """Test calling post-run method with report."""
        report = Report(count=2, pipeline=pipeline_config)

        for unit in pipeline_config.iter_units():
            flexmock(unit).should_receive("post_run_report").with_args(report=report).and_return(None).once()

        pipeline_config.call_post_run_report(report)
