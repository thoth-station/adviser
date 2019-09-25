#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019 Fridolin Pokorny
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


"""Recommendation engine based on scoring of a software stack."""

import logging
from typing import List
from typing import Tuple
from typing import Dict

import attr

from thoth.common import RuntimeEnvironment
from thoth.python import Project
from thoth.adviser.enums import RecommendationType
from thoth.storages import GraphDatabase

from .builder import PipelineBuilder
from .builder import PipelineConfig
from .pipeline import Pipeline


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Adviser:
    """Implementation of adviser - the core of recommendation engine in Thoth."""

    count = attr.ib(type=int, default=None)
    limit = attr.ib(type=int, default=None)
    recommendation_type = attr.ib(
        type=RecommendationType, default=RecommendationType.STABLE
    )
    _computed_stacks_heap = attr.ib(type=RuntimeEnvironment, default=attr.Factory(list))
    _visited = attr.ib(type=int, default=0)

    def compute_using_pipeline(self, pipeline: Pipeline) -> Tuple[List[Tuple[Dict, Project, float]], List[Dict]]:
        """Compute recommendations using a custom pipeline configuration."""
        result = []
        for product in pipeline.conduct(count=self.count, limit=self.limit):
            product.finalize()
            result.append((product.justification, product.project, product.score))

        return result, pipeline.get_stack_info()

    def compute(
        self,
        graph: GraphDatabase,
        project: Project,
        limit_latest_versions: int = None,
        library_usage: dict = None,
    ) -> Tuple[Tuple[List[Tuple[Dict, Project, float]], List[Dict]], Dict]:
        """Compute recommendations for the given project."""
        builder = PipelineBuilder(graph, project, library_usage)
        pipeline_config: PipelineConfig = builder.get_adviser_pipeline_config(
            self.recommendation_type, limit_latest_versions=limit_latest_versions
        )
        pipeline = Pipeline(
            sieves=pipeline_config.sieves,
            steps=pipeline_config.steps,
            strides=pipeline_config.strides,
            graph=graph,
            project=project,
            library_usage=library_usage,
        )

        return self.compute_using_pipeline(pipeline), pipeline.get_configuration()

    @classmethod
    def compute_on_project(
        cls,
        project: Project,
        *,
        recommendation_type: RecommendationType,
        library_usage: dict = None,
        count: int = None,
        limit: int = None,
        limit_latest_versions: int = None,
        graph: GraphDatabase = None,
    ) -> tuple:
        """Compute recommendations for the given project, a syntax sugar for the compute method."""
        stack_info = []

        instance = cls(
            count=count, limit=limit, recommendation_type=recommendation_type
        )

        if project.runtime_environment.python_version and not project.python_version:
            stack_info.append(
                {
                    "type": "WARNING",
                    "justification": "Use specific Python version in Pipfile based on Thoth's configuration to "
                    "ensure correct Python version usage on deployment",
                }
            )
            project.set_python_version(project.runtime_environment.python_version)

        if not graph:
            graph = GraphDatabase()
            graph.connect()

        result, pipeline_configuration = instance.compute(
            graph,
            project,
            limit_latest_versions=limit_latest_versions,
            library_usage=library_usage,
        )

        report, stack_info = result
        advised_configuration = None
        configuration_check_report = project.get_configuration_check_report()
        if configuration_check_report:
            advised_configuration, configuration_check_report = (
                configuration_check_report
            )
            stack_info.extend(configuration_check_report)

        return stack_info, advised_configuration, report, pipeline_configuration
