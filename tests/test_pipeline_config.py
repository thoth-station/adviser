#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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
        pipeline_dict = pipeline_config.to_dict()
        assert pipeline_dict == {
            "boots": [
                {"configuration": {"package_name": "flask", "some_parameter": -0.2}, "name": "Boot1", "unit_run": False}
            ],
            "pseudonyms": [
                {
                    "configuration": {"another_parameter": 0.33, "package_name": "tensorflow"},
                    "name": "Pseudonym1",
                    "unit_run": False,
                }
            ],
            "sieves": [
                {
                    "configuration": {"flying_circus": 1969, "package_name": "tensorflow"},
                    "name": "Sieve1",
                    "unit_run": False,
                }
            ],
            "steps": [
                {
                    "configuration": {
                        "guido_retirement": 2019,
                        "package_name": "tensorflow",
                        "multi_package_resolution": False,
                    },
                    "name": "Step1",
                    "unit_run": False,
                }
            ],
            "strides": [
                {
                    "configuration": {
                        "linus": {"children": 3, "parents": ["nils", "anna"], "residence": "oregon"},
                        "package_name": None,
                    },
                    "name": "Stride1",
                    "unit_run": False,
                }
            ],
            "wraps": [
                {
                    "configuration": {
                        "cities": ["Brno", "Bonn", "Boston", "Milan"],
                        "thoth": [2018, 2019],
                        "package_name": None,
                    },
                    "name": "Wrap1",
                    "unit_run": False,
                }
            ],
        }

    def test_iter_units(self, pipeline_config: PipelineConfig) -> None:
        """Test iteration over all units present in the pipeline configuration."""
        visited = dict.fromkeys(("Boot1", "Pseudonym1", "Sieve1", "Step1", "Stride1", "Wrap1"), 0)
        for unit in pipeline_config.iter_units():
            assert unit.__class__.__name__ in visited, f"Unknown unit {unit.__class__.__name__!r}"
            visited[unit.__class__.__name__] += 1

        assert len(visited) == 6
        assert list(visited.values()) == [1] * 6

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
        report = Report(products=[flexmock()], pipeline=pipeline_config)

        for unit in pipeline_config.iter_units():
            flexmock(unit).should_receive("post_run_report").with_args(report=report).and_return(None).once()

        pipeline_config.call_post_run_report(report)
