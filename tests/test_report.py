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

"""Test report as product by a resolver."""

import json
import os
import pytest
from itertools import chain

from thoth.adviser.context import Context
from thoth.adviser.pipeline_config import PipelineConfig
from thoth.adviser.product import Product
from thoth.adviser.report import Report
from thoth.common import RuntimeEnvironment

from .base import AdviserTestCase


@pytest.fixture
def pipeline_config() -> PipelineConfig:  # noqa: D401
    """A fixture for a pipeline config."""
    return PipelineConfig(boots={}, pseudonyms={}, sieves={}, steps={}, strides={}, wraps={})


class TestReport(AdviserTestCase):
    """Test report product by a resolver."""

    def test_stack_info(self, pipeline_config: PipelineConfig) -> None:
        """Test setting a global stack information."""
        report = Report(products=[], pipeline=pipeline_config)
        report.set_stack_info([{"foo": "bar"}])

        assert report.to_dict(verbose=True) == {
            "pipeline": {
                "boots": [],
                "pseudonyms": [],
                "sieves": [],
                "steps": [],
                "strides": [],
                "wraps": [],
            },
            "products": [],
            "stack_info": [{"foo": "bar"}],
            "resolver_iterations": 0,
            "accepted_final_states_count": 0,
            "discarded_final_states_count": 0,
        }

    def test_to_dict(self, context: Context, pipeline_config: PipelineConfig) -> None:
        """Test conversion to a dict."""
        # Reuse project from the context for this test case.
        project = context.project
        project_dict = {"aresto momentum": "avada kedavra"}
        project.should_receive("to_dict").with_args(keep_thoth_section=True).and_return(
            project_dict
        ).twice()  # In test and in the report.

        product = Product(
            project=project,
            score=0.666,
            justification=[{"gryffindor": "le gladium leviosa"}],
            advised_runtime_environment=RuntimeEnvironment.from_dict({"python_version": "3.6"}),
            context=context,
        )

        report = Report(products=[product], pipeline=pipeline_config)

        assert report.to_dict(verbose=True) == {
            "pipeline": pipeline_config.to_dict(),
            "products": [product.to_dict()],
            "stack_info": [],
            "resolver_iterations": 0,
            "accepted_final_states_count": 0,
            "discarded_final_states_count": 0,
        }

    def test_to_dict_metadata(self, context: Context, pipeline_config: PipelineConfig) -> None:
        """Test conversion to a dict with passed metadata."""
        # Reuse project from the context for this test case.
        project = context.project
        project_dict = {"aresto momentum": "avada kedavra"}
        project.should_receive("to_dict").with_args(keep_thoth_section=True).and_return(project_dict)

        product = Product(
            project=project,
            score=0.666,
            justification=[{"gryffindor": "le gladium leviosa"}],
            advised_runtime_environment=RuntimeEnvironment.from_dict({"python_version": "3.6"}),
            context=context,
        )

        stack_info = [{"type": "WARNING", "message": "Hello, metadata"}]

        report = Report(
            products=[product],
            pipeline=pipeline_config,
            stack_info=stack_info,
        )

        stack_info_metadata = {
            "thoth.adviser": {
                "stack_info": stack_info,
            }
        }

        assert "THOTH_ADVISER_METADATA" not in os.environ
        os.environ["THOTH_ADVISER_METADATA"] = json.dumps(stack_info_metadata)

        try:
            assert report.to_dict(verbose=True) == {
                "pipeline": pipeline_config.to_dict(),
                "products": [product.to_dict()],
                "stack_info": list(chain(stack_info, report.stack_info)),
                "resolver_iterations": 0,
                "accepted_final_states_count": 0,
                "discarded_final_states_count": 0,
            }
        finally:
            os.environ.pop("THOTH_ADVISER_METADATA")

    def test_no_verbose(self, context: Context, pipeline_config: PipelineConfig) -> None:
        """Test obtaining report with and without verbose flag set."""
        # Reuse project from the context for this test case.
        project = context.project
        project_dict = {"aresto momentum": "avada kedavra"}
        project.should_receive("to_dict").with_args(keep_thoth_section=True).and_return(project_dict)

        product = Product(
            project=project,
            score=0.666,
            justification=[{"gryffindor": "le gladium leviosa"}],
            advised_runtime_environment=RuntimeEnvironment.from_dict({"python_version": "3.6"}),
            context=context,
        )

        report = Report(
            products=[product],
            pipeline=pipeline_config,
            stack_info=[{"foo": "bar"}],
        )

        assert report.to_dict(verbose=False) == {
            "pipeline": None,
            "products": [product.to_dict()],
            "stack_info": report.stack_info,
            "resolver_iterations": 0,
            "accepted_final_states_count": 0,
            "discarded_final_states_count": 0,
        }

        assert report.to_dict(verbose=True) == {
            "pipeline": pipeline_config.to_dict(),
            "products": [product.to_dict()],
            "stack_info": report.stack_info,
            "resolver_iterations": 0,
            "accepted_final_states_count": 0,
            "discarded_final_states_count": 0,
        }
