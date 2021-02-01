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

"""Tests related to check if GPU specific recommendations should be done."""

from thoth.adviser.boots import GPUBoot
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext

from ..base import AdviserUnitTestCase


class TestGPUBoot(AdviserUnitTestCase):
    """Test a boot that checks if GPU specific recommendations should be done."""

    UNIT_TESTED = GPUBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.project.runtime_environment.hardware.gpu_model = 0x42
        builder_context.project.runtime_environment.cuda_version = None
        self.verify_multiple_should_include(builder_context)

    def test_include_no_cuda(self, builder_context: PipelineBuilderContext) -> None:
        """Verify including when no CUDA is supplied."""
        builder_context.project.runtime_environment.hardware.gpu_model = 0x42
        builder_context.project.runtime_environment.cuda_version = None
        self.verify_multiple_should_include(builder_context)

    def test_include_no_gpu(self, builder_context: PipelineBuilderContext) -> None:
        """Verify including when no GPU is supplied."""
        builder_context.project.runtime_environment.hardware.gpu_model = None
        builder_context.project.runtime_environment.cuda_version = "10.0"
        self.verify_multiple_should_include(builder_context)

    def test_no_cuda(self, context: Context) -> None:
        """Test when no CUDA is supplied, but GPU is available."""
        context.project.runtime_environment.hardware.gpu_model = 0x42
        context.project.runtime_environment.cuda_version = None

        boot = self.UNIT_TESTED()
        with boot.assigned_context(context):
            boot.run()

        assert context.stack_info, "No stack info provided"
        assert context.project.runtime_environment.hardware.gpu_model is None
        assert context.project.runtime_environment.cuda_version is None
        assert self.verify_justification_schema(context.stack_info) is True

    def test_no_gpu(self, context: Context) -> None:
        """Test when no GPU is available, but CUDA is available."""
        context.project.runtime_environment.hardware.gpu_model = None
        context.project.runtime_environment.cuda_version = "9.0"

        boot = self.UNIT_TESTED()
        with boot.assigned_context(context):
            boot.run()

        assert context.stack_info, "No stack info provided"
        assert context.project.runtime_environment.hardware.gpu_model is None
        assert context.project.runtime_environment.cuda_version is None
        assert self.verify_justification_schema(context.stack_info) is True
