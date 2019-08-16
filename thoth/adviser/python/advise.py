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
from .adviser_report import AdviserReport


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Adviser:
    """Implementation of adviser - the core of recommendation engine in Thoth."""

    count = attr.ib(type=int, default=None)
    limit = attr.ib(type=int, default=None)
    recommendation_type = attr.ib(type=RecommendationType, default=RecommendationType.STABLE)

    def compute_using_pipeline(self, pipeline: Pipeline) -> AdviserReport:
        """Perform actual computing using the given pipeline and return report."""
        result = []
        for product in pipeline.conduct(count=self.count, limit=self.limit):
            product.finalize(pipeline.graph)
            result.append(product.to_dict())

        configuration_check_report = pipeline.project.get_configuration_check_report()
        advised_configuration = None
        if configuration_check_report:
            advised_configuration, configuration_check_report = configuration_check_report

        report = AdviserReport(
            products=result,
            pipeline_configuration=pipeline.get_configuration(),
            advised_configuration=advised_configuration,
            library_usage=pipeline.library_usage,
            stack_info=pipeline.get_stack_info() + (configuration_check_report or []),
            was_oom_killed=pipeline.was_oom_killed,
            was_cpu_time_exhausted_killed=pipeline.was_cpu_time_exhausted_killed,
        )

        if pipeline.project.runtime_environment.python_version and not pipeline.project.python_version:
            report.stack_info.append(
                {
                    "type": "WARNING",
                    "justification": "Use specific Python version in Pipfile based on Thoth's configuration to "
                    "ensure correct Python version usage on deployment",
                }
            )
            pipeline.project.set_python_version(pipeline.project.runtime_environment.python_version)

        return report

    def compute(
        self,
        *,
        project: Project,
        graph: GraphDatabase = None,
        limit_latest_versions: int = None,
        library_usage: dict = None,
    ) -> AdviserReport:
        """Compute recommendations for the given project."""
        if not graph:
            graph = GraphDatabase()
            graph.connect()

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

        return self.compute_using_pipeline(pipeline)
