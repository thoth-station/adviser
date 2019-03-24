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

"""Configuration of stack generator pipelines."""


from collections import namedtuple

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType

from .pipeline.steps import LimitLatestVersions
from .pipeline.steps import PerformanceAdjustment
from .pipeline.steps import CutPreReleases
from .pipeline.steps import RestrictIndexes
from .pipeline.steps import SemverSort
from .pipeline.steps import CutToolchain
from .pipeline.steps import CutUnreachable
from .pipeline.steps import BuildtimeErrorFiltering
from .pipeline.steps import CvePenalization
from .pipeline.steps import RuntimeErrorFiltering
from .pipeline.strides import PerformanceScoring
from .pipeline.strides import RandomDecision
from .pipeline.strides import ScoreFiltering
from .pipeline.strides import CveScoring

PipelineConfig = namedtuple("PipelineConfig", "steps, strides")


class PipelineConfigAdviser:
    """Configuration of stack generator pipeline for adviser."""

    def __init__(self):
        """Avoid instantiating this class."""
        raise RuntimeError("Cannot instantiate")

    @classmethod
    def by_recommendation_type(
        cls,
        recommendation_type: RecommendationType,
        *,
        limit_latest_versions: int = None,
    ) -> PipelineConfig:
        """Get pipeline configuration based on recommendation type."""
        if recommendation_type == RecommendationType.LATEST:
            pipeline_config = PipelineConfig(
                steps=[
                    (CutPreReleases, None),
                    (CutToolchain, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
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
                steps=[
                    (CutPreReleases, None),
                    (CutToolchain, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
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
                steps=[
                    (CutPreReleases, None),
                    (CutToolchain, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
                    (BuildtimeErrorFiltering, None),
                    (RuntimeErrorFiltering, None),
                    (CvePenalization, None),
                ],
                strides=[
                    (PerformanceScoring, None),
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

            pipeline_config.steps.append((PerformanceAdjustment, None))
        else:
            raise ValueError(
                f"No stack generation pipeline configuration defined for recommendation type {recommendation_type.name}"
            )

        return pipeline_config


class PipelineConfigDependencyMonkey:
    """Configuration of stack generator pipeline for adviser."""

    def __init__(self):
        """Avoid instantiating this class."""
        raise RuntimeError("Cannot instantiate")

    @classmethod
    def by_decision_type(
        cls, decision_type: DecisionType, *, limit_latest_versions: int = None
    ) -> PipelineConfig:
        """Get pipeline configuration based on decision type."""
        if decision_type == DecisionType.ALL:
            pipeline_config = PipelineConfig(
                steps=[
                    (CutPreReleases, None),
                    (RestrictIndexes, None),
                    (CutUnreachable, None),
                    (SemverSort, None),
                ],
                strides=[],
            )
        elif decision_type == DecisionType.RANDOM:
            pipeline_config = PipelineConfig(
                steps=[
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
