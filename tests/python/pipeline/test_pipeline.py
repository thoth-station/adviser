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

"""Test pipeline run."""

import flexmock
import pytest

from thoth.python import Project
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.adviser.python.dependency_graph import DependencyGraphWalker
from thoth.adviser.python.dependency_graph import PrematureStreamEndError
from thoth.adviser.python.pipeline import Pipeline
from thoth.adviser.python.pipeline import PipelineProduct
from thoth.adviser.python.pipeline import StepContext
from thoth.adviser.python.pipeline import StrideContext
from thoth.adviser.python.pipeline.step import Step
from thoth.adviser.python.pipeline.stride import Stride
from thoth.adviser.python.pipeline.exceptions import StrideRemoveStack
from thoth.adviser.python.pipeline.exceptions import NotResolvedError

from base import AdviserTestCase


_PIPFILE_STR = """
[[source]]
name = "pypi"
url = "https://pypi.org/simple"
verify_ssl = true

[dev-packages]

[packages]
flask = "*"

[requires]
python_version = "3.6"
"""


_MOCK_STEP_PARAMETERS = {"foo": "bar"}
_MOCK_STRIDE_PARAMETERS = {"thoth": "rockz"}
_MOCK_STRIDE_JUSTIFICATION = [{"justification": "Just for testing purposes"}]


class _MockStep(Step):
    """A mock used as a step in testing pipeline."""

    def run(self, step_context: StepContext) -> None:
        assert self.parameters == _MOCK_STEP_PARAMETERS
        assert isinstance(step_context, StepContext)


class _MockStride(Stride):
    """A mock used as a stride in testing pipeline."""

    def run(self, stride_context: StrideContext) -> None:
        assert self.parameters == _MOCK_STRIDE_PARAMETERS
        assert isinstance(stride_context, StrideContext)
        stride_context.adjust_score(1.0, _MOCK_STRIDE_JUSTIFICATION)


class _MockStrideRemoveStack(Stride):
    """A mock used as a stride in testing pipeline."""

    def run(self, stride_context: StrideContext) -> None:
        raise StrideRemoveStack("Stack inspected in this stride will be removed")


class TestPipeline(AdviserTestCase):
    """Test pipeline run and manipulation."""

    def test_step_simple_run(self):
        """Test running a single step inside pipeline."""
        project = Project.from_strings(_PIPFILE_STR)

        direct_dependency = PackageVersion(
            name="flask",
            version="==1.0.2",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        step_context = StepContext.from_paths(
            {direct_dependency.to_tuple(): direct_dependency},
            {direct_dependency.to_tuple(): []},
        )

        pipeline = Pipeline(
            graph=None,  # We avoid low-level testing down to thoth-storages.
            project=project,
            sieves=[],
            steps=[
                (_MockStep, _MOCK_STEP_PARAMETERS)
            ],
            strides=[],
        )

        flexmock(
            pipeline,
            _prepare_direct_dependencies=lambda with_devel: [direct_dependency],
            _resolve_transitive_dependencies=lambda _: step_context,
        )

        # We raise an exception on first walk call, no stacks should be produced.
        pipeline_products = list(pipeline.conduct(limit=None, count=None))
        assert len(pipeline_products) == 1
        assert pipeline.get_stack_info() == []

        pipeline_product = pipeline_products[0]
        assert isinstance(pipeline_product, PipelineProduct)
        # No stride was run.
        assert pipeline_product.justification == []
        assert pipeline_product.score == 0.0
        assert pipeline_product.project

    def test_stride_simple_run(self):
        """Test running a single stride inside pipeline."""
        project = Project.from_strings(_PIPFILE_STR)

        direct_dependency = PackageVersion(
            name="flask",
            version="==1.0.2",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        step_context = StepContext.from_paths(
            {direct_dependency.to_tuple(): direct_dependency},
            {direct_dependency.to_tuple(): []}
        )

        pipeline = Pipeline(
            graph=None,  # We avoid low-level testing down to thoth-storages.
            project=project,
            sieves=[],
            steps=[
                (_MockStep, _MOCK_STEP_PARAMETERS)
            ],
            strides=[
                (_MockStride, _MOCK_STRIDE_PARAMETERS)
            ],
        )

        flexmock(
            pipeline,
            _prepare_direct_dependencies=lambda with_devel: [direct_dependency],
            _resolve_transitive_dependencies=lambda _: step_context,
        )

        # We raise an exception on first walk call, no stacks should be produced.
        pipeline_products = list(pipeline.conduct(limit=None, count=None))
        assert len(pipeline_products) == 1
        assert pipeline.get_stack_info() == []

        pipeline_product = pipeline_products[0]
        assert isinstance(pipeline_product, PipelineProduct)
        assert pipeline_product.justification == _MOCK_STRIDE_JUSTIFICATION
        assert pipeline_product.score == 1.0
        assert pipeline_product.project

    def test_stride_remove_stack(self):
        project = Project.from_strings(_PIPFILE_STR)

        direct_dependency = PackageVersion(
            name="flask",
            version="==1.0.2",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        step_context = StepContext.from_paths(
            {direct_dependency.to_tuple(): direct_dependency},
            {direct_dependency.to_tuple(): []},
        )

        pipeline = Pipeline(
            graph=None,  # We avoid low-level testing down to thoth-storages.
            project=project,
            sieves=[],
            steps=[],
            strides=[
                (_MockStrideRemoveStack, None)
            ],
        )

        flexmock(
            pipeline,
            _prepare_direct_dependencies=lambda with_devel: [direct_dependency],
            _resolve_transitive_dependencies=lambda _: step_context,
        )

        # We raise an exception on first walk call, no stacks should be produced.
        pipeline_products = list(pipeline.conduct(limit=None, count=None))
        assert len(pipeline_products) == 0

    def test_step_and_stride_simple_run(self):
        """Test running step and stride at the same time."""
        project = Project.from_strings(_PIPFILE_STR)

        direct_dependency = PackageVersion(
            name="flask",
            version="==1.0.2",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        step_context = StepContext.from_paths(
            {direct_dependency.to_tuple(): direct_dependency},
            {direct_dependency.to_tuple(): []},
        )

        pipeline = Pipeline(
            graph=None,  # We avoid low-level testing down to thoth-storages.
            project=project,
            sieves=[],
            steps=[],
            strides=[
                (_MockStride, _MOCK_STRIDE_PARAMETERS)
            ],
        )

        flexmock(
            pipeline,
            _prepare_direct_dependencies=lambda with_devel: [direct_dependency],
            _resolve_transitive_dependencies=lambda _: step_context,
        )

        # We raise an exception on first walk call, no stacks should be produced.
        pipeline_products = list(pipeline.conduct(limit=None, count=None))
        assert len(pipeline_products) == 1
        assert pipeline.get_stack_info() == []

        pipeline_product = pipeline_products[0]
        assert isinstance(pipeline_product, PipelineProduct)
        assert pipeline_product.justification == _MOCK_STRIDE_JUSTIFICATION
        assert pipeline_product.score == 1.0
        assert pipeline_product.project

    def test_conduct_premature_stream_end(self):
        """Test pipeline reports premature stream error if libdependency_graph.so died."""
        def raise_premature_stream_error():
            raise PrematureStreamEndError("Premature stream exception")

        project = Project.from_strings(_PIPFILE_STR)
        pipeline = Pipeline(
            graph=None,  # We avoid low-level testing down to thoth-storages.
            project=project,
            sieves=[],
            steps=[],
            strides=[],
        )

        flexmock(
            DependencyGraphWalker,
            walk=raise_premature_stream_error,
        )

        direct_dependency = PackageVersion(
            name="flask",
            version="==1.0.2",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        step_context = StepContext.from_paths(
            {direct_dependency.to_tuple(): direct_dependency},
            {direct_dependency.to_tuple(): []},
        )

        flexmock(
            pipeline,
            _prepare_direct_dependencies=lambda with_devel: [direct_dependency],
            _resolve_transitive_dependencies=lambda _: step_context,
        )

        # We raise an exception on first walk call, no stacks should be produced.
        assert len(list(pipeline.conduct(limit=None, count=None))) == 0

        # Get stack info after conduct.
        stack_info = pipeline.get_stack_info()
        assert len(stack_info) == 1
        stack_info_entry = stack_info[0]
        assert "type" in stack_info_entry
        assert stack_info_entry["type"] == "WARNING"
        assert "justification" in stack_info_entry

    def test_not_fully_resolved_error(self):
        """Test trying to running pipeline with unresolved package produces an error."""
        project = Project.from_strings(_PIPFILE_STR)
        pipeline = Pipeline(
            graph=None,  # We avoid low-level testing down to thoth-storages.
            project=project,
            sieves=[],
            steps=[],
            strides=[],
        )

        direct_dependency = PackageVersion(
            name="flask",
            version="==1.0.2",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        step_context = StepContext.from_paths(
            {direct_dependency.to_tuple(): direct_dependency},
            {direct_dependency.to_tuple(): [
                (("flask", "1.0.2", "https://pypi.org/simple"), ("werkzeug", None, None))
            ]},
        )

        flexmock(
            pipeline,
            _prepare_direct_dependencies=lambda with_devel: [direct_dependency],
            _resolve_transitive_dependencies=lambda _: step_context,
        )

        with pytest.raises(NotResolvedError):
            pipeline.conduct(limit=None, count=None)

        # Try again, now with first item in the tuple list - same error should be produced.
        step_context = StepContext.from_paths(
            {direct_dependency.to_tuple(): direct_dependency},
            {direct_dependency.to_tuple(): [
                (("flask", None, None), ("werkzeug", "0.15.6", "https://pypi.org/simple"))
            ]},
        )

        flexmock(
            pipeline,
            _prepare_direct_dependencies=lambda with_devel: [direct_dependency],
            _resolve_transitive_dependencies=lambda _: step_context,
        )

        with pytest.raises(NotResolvedError):
            pipeline.conduct(limit=None, count=None)
