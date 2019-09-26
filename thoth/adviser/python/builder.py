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

"""Dynamic constructor of stack generation pipeline."""

import attr

from collections import namedtuple

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType

from thoth.storages import GraphDatabase
from thoth.python import Project

from .pipeline.sieves import OperatingSystemSieve
from .pipeline.sieves import PackageIndexSieve
from .pipeline.sieves import SolvedSieve
from .pipeline.steps import BuildtimeErrorFiltering
from .pipeline.steps import CutPreReleases
from .pipeline.steps import CutToolchain
from .pipeline.steps import CutUnsolved
from .pipeline.steps import CutUnreachable
from .pipeline.steps import CvePenalization
from .pipeline.steps import LimitLatestVersions
from .pipeline.steps import ObservationReduction
from .pipeline.steps import RestrictIndexes
from .pipeline.steps import RuntimeErrorFiltering
from .pipeline.steps import SemverSort
from .pipeline.strides import CveScoring
from .pipeline.strides import RandomDecision
from .pipeline.strides import ScoreFiltering


PipelineConfig = namedtuple("PipelineConfig", "sieves, steps, strides")


@attr.s(slots=True)
class PipelineBuilder:
    """Dynamic constructor of stack generation pipeline."""

    graph = attr.ib(type=GraphDatabase)
    project = attr.ib(type=Project)
    library_usage = attr.ib(type=dict, default=None)

    @staticmethod
    def get_adviser_pipeline_config(
        recommendation_type: RecommendationType, *, limit_latest_versions: int = None
    ) -> PipelineConfig:
        """Get pipeline configuration for an adviser run."""
        if recommendation_type == RecommendationType.LATEST:
            pipeline_config = PipelineConfig(
                sieves=[
                    (OperatingSystemSieve, None),
                    (PackageIndexSieve, None),
                    (SolvedSieve, {"without_error": True}),
                ],
                steps=[
                    (CutUnsolved, None),
                    (CutPreReleases, None),
                    (CutToolchain, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
                    (ObservationReduction, None),
                ],
                strides=[],
            )
            if limit_latest_versions:
                pipeline_config.steps.append(
                    (
                        LimitLatestVersions,
                        {"limit_latest_versions": limit_latest_versions},
                    )
                )
        elif recommendation_type == RecommendationType.TESTING:
            pipeline_config = PipelineConfig(
                sieves=[
                    (OperatingSystemSieve, None),
                    (PackageIndexSieve, None),
                    (SolvedSieve, {"without_error": True}),
                ],
                steps=[
                    (CutUnsolved, None),
                    (BuildtimeErrorFiltering, None),
                    (CutPreReleases, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
                    (CutToolchain, None),
                    (RuntimeErrorFiltering, None),
                    (ObservationReduction, None),
                ],
                strides=[],
            )

            if limit_latest_versions:
                pipeline_config.steps.append(
                    (
                        LimitLatestVersions,
                        {"limit_latest_versions": limit_latest_versions},
                    )
                )
        elif recommendation_type == RecommendationType.STABLE:
            pipeline_config = PipelineConfig(
                sieves=[
                    (OperatingSystemSieve, None),
                    (PackageIndexSieve, None),
                    (SolvedSieve, {"without_error": True}),
                ],
                steps=[
                    (CutUnsolved, None),
                    (BuildtimeErrorFiltering, None),
                    (CutPreReleases, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
                    (CutToolchain, None),
                    (RuntimeErrorFiltering, None),
                    (CvePenalization, None),
                    (ObservationReduction, None),
                ],
                strides=[
                    (CveScoring, None),
                    (ScoreFiltering, None),
                ],
            )

            if limit_latest_versions:
                pipeline_config.steps.append(
                    (
                        LimitLatestVersions,
                        {"limit_latest_versions": limit_latest_versions},
                    )
                )
        else:
            raise ValueError(
                f"No stack generation pipeline configuration defined for recommendation type {recommendation_type.name}"
            )

        return pipeline_config

    @staticmethod
    def get_dependency_monkey_pipeline_config(
        decision_type: DecisionType, *, limit_latest_versions: int = None
    ) -> PipelineConfig:
        """Get pipeline configuration for a dependency monkey run."""
        if decision_type == DecisionType.ALL:
            pipeline_config = PipelineConfig(
                sieves=[
                    (OperatingSystemSieve, None),
                    (PackageIndexSieve, None),
                    (SolvedSieve, {"without_error": True}),
                ],
                steps=[
                    (CutUnsolved, None),
                    (CutPreReleases, None),
                    (RestrictIndexes, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
                ],
                strides=[],
            )
        elif decision_type == DecisionType.RANDOM:
            pipeline_config = PipelineConfig(
                sieves=[
                    (OperatingSystemSieve, None),
                    (PackageIndexSieve, None),
                    (SolvedSieve, {"without_error": True}),
                ],
                steps=[
                    (CutUnsolved, None),
                    (CutPreReleases, None),
                    (RestrictIndexes, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
                ],
                strides=[(RandomDecision, None)],
            )
        else:
            raise ValueError(
                f"No stack generation pipeline configuration defined for decision type {decision_type.name}"
            )

        if limit_latest_versions:
            pipeline_config.steps.append(
                (LimitLatestVersions, {"limit_latest_versions": limit_latest_versions})
            )

        return pipeline_config
