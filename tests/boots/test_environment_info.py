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

"""Test providing environment information used in the stack information."""

import pytest

from typing import Any
from typing import Dict
from typing import List

from thoth.common import RuntimeEnvironment
from thoth.python.constraints import Constraints
from thoth.adviser.boots import EnvironmentInfoBoot
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.enums import RecommendationType
from thoth.common import get_justification_link as jl
from ..base import AdviserUnitTestCase


class TestEnvironmentInfoBoot(AdviserUnitTestCase):
    """Test providing environment information used in the stack information."""

    UNIT_TESTED = EnvironmentInfoBoot

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)
        self.verify_multiple_should_include(builder_context)

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit for adviser runs."""
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

        builder_context.add_unit(self.UNIT_TESTED())

        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    @pytest.mark.parametrize(
        "runtime_environment_dict,expected,use_constraints,use_library_usage",
        [
            (
                {
                    "base_image": "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0",
                    "cuda_version": "11.1",
                    "cudnn_version": "7.6.5",
                    "hardware": {"cpu_family": 1, "cpu_model": 2, "gpu_model": "Some GPU model"},
                    "mkl_version": "2021.1",
                    "name": "rhel-9",
                    "openblas_version": "0.3.0",
                    "openmpi_version": "4.0.5",
                    "operating_system": {"name": "rhel", "version": "9"},
                    "platform": "linux-x86_64",
                    "python_version": "3.10",
                    "recommendation_type": "latest",
                },
                [
                    {
                        "link": jl("env"),
                        "message": "Resolving for runtime environment named 'rhel-9'",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "Resolving for operating system 'rhel' in version '9'",
                    },
                    {
                        "link": jl("env"),
                        "message": "Resolving for Python version '3.6'",
                        "type": "INFO",
                    },
                    {
                        "link": "https://thoth-station.ninja/recommendation-types/",
                        "message": "Using recommendation type 'latest'",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "Using platform 'linux-x86_64'",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "Using constraints provided",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "Using supplied static source code analysis",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "Using containerized environment "
                        "'quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0'",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "Using CPU family 1 model 2",
                        "type": "INFO",
                    },
                    {"link": jl("env"), "message": "Using CUDA '11.1'", "type": "INFO"},
                    {"link": jl("env"), "message": "Using cuDNN '7.6.5'", "type": "INFO"},
                    {"link": jl("env"), "message": "Using OpenBLAS '0.3.0'", "type": "INFO"},
                    {"link": jl("env"), "message": "Using OpenMPI '4.0.5'", "type": "INFO"},
                    {"link": jl("env"), "message": "Using MKL '2021.1'", "type": "INFO"},
                ],
                True,
                True,
            ),
            (
                {},
                [
                    {
                        "link": jl("env"),
                        "message": "Resolving for runtime environment named 'UNKNOWN'",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "Resolving for operating system None in version None",
                    },
                    {
                        "link": jl("env"),
                        "message": "Resolving for Python version '3.6'",
                        "type": "INFO",
                    },
                    {
                        "link": "https://thoth-station.ninja/recommendation-types/",
                        "message": "Using recommendation type 'latest'",
                        "type": "INFO",
                    },
                    {"link": jl("env"), "message": "Using platform 'UNKNOWN'", "type": "INFO"},
                    {
                        "link": jl("env"),
                        "message": "No constraints supplied to the resolution process",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "No static source code analysis supplied",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "No containerized environment used",
                        "type": "INFO",
                    },
                    {
                        "link": jl("env"),
                        "message": "Using CPU family 'UNKNWON' model 'UNKNOWN'",
                        "type": "INFO",
                    },
                    {"link": jl("env"), "message": "No CUDA used", "type": "INFO"},
                    {"link": jl("env"), "message": "No cuDNN used", "type": "INFO"},
                    {"link": jl("env"), "message": "No OpenBLAS used", "type": "INFO"},
                    {"link": jl("env"), "message": "No OpenMPI used", "type": "INFO"},
                    {"link": jl("env"), "message": "No MKL used", "type": "INFO"},
                ],
                False,
                False,
            ),
        ],
    )
    def test_run(
        self,
        context: Context,
        runtime_environment_dict: Dict[str, Any],
        expected: List[Dict[str, str]],
        use_constraints: bool,
        use_library_usage: bool,
    ) -> None:
        """Test providing information about the runtime environment."""
        if use_constraints:
            context.project.constraints = Constraints.from_string("flask>=1.3.0")

        if use_library_usage:
            context.library_usage = {"flask": ["flask.App"]}

        context.project.runtime_environment = RuntimeEnvironment.from_dict(runtime_environment_dict)
        assert not context.stack_info

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            assert unit.run() is None

        assert context.stack_info == expected
        assert self.verify_justification_schema(context.stack_info)
