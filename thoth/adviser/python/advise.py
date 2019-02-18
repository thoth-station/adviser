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
import heapq
import typing

import attr

from thoth.common import RuntimeEnvironment
from thoth.python import Project
from thoth.adviser.python import DependencyGraph
from thoth.adviser.enums import RecommendationType
from thoth.adviser.python.helpers import fill_package_digests_from_graph
from thoth.storages import GraphDatabase

from .scoring import Scoring


_LOGGER = logging.getLogger(__name__)


class HeapEntry:
    """An advise with score stored on heap."""

    __slots__ = ["score", "reasoning", "generated_project"]

    def __init__(self, score: float, reasoning: list, generated_project: Project):
        """Initialize heap entry item."""
        self.score = score
        self.reasoning = reasoning
        self.generated_project = generated_project

    def __gt__(self, other):
        """Compare heap entries based on score."""
        return self.score > other.score

    def get_entries(self) -> tuple:
        """Get heap entry items."""
        return self.reasoning, self.generated_project


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

    def compute(
        self,
        graph: GraphDatabase,
        project: Project,
        runtime_environment: RuntimeEnvironment,
        scoring_function: typing.Callable,
        dry_run: bool = False,
    ) -> typing.Union[typing.List[Project], int]:
        """Compute recommendations for the given project."""
        dependency_graph = DependencyGraph.from_project(graph, project, runtime_environment, restrict_indexes=False)

        try:
            for decision_function_result, generated_project in dependency_graph.walk(
                scoring_function
            ):
                score, reasoning = decision_function_result
                reasoning.append({'score': score})
                self._visited += 1

                if dry_run:
                    continue

                heap_entry = HeapEntry(score, reasoning, generated_project)
                if (
                    self.count is not None
                    and len(self._computed_stacks_heap) >= self.count
                ):
                    heapq.heappushpop(self._computed_stacks_heap, heap_entry)
                else:
                    heapq.heappush(self._computed_stacks_heap, heap_entry)

                if self.limit is not None and self._visited >= self.limit:
                    _LOGGER.info("Reached graph traversal limit (%s), stopping dependency graph traversal", self.limit)
                    break

            if dry_run:
                return self._visited

            _LOGGER.info("Scored %d stacks in total", self._visited)
            # Sort computed stacks based on score and return them.
            # TODO: heap pop (?)
            result = (
                item.get_entries()
                for item in sorted(self._computed_stacks_heap, reverse=True)
            )
            _LOGGER.info("Filling package digests to software stacks")
            result = [
                (item[0], fill_package_digests_from_graph(item[1], graph)) for item in result
            ]
            return result
        finally:
            self._computed_stacks_heap = []
            self._visited = 0

    @classmethod
    def compute_on_project(
        cls,
        project: Project,
        *,
        runtime_environment: RuntimeEnvironment,
        recommendation_type: RecommendationType,
        count: int = None,
        limit: int = None,
        dry_run: bool = False
    ) -> tuple:
        """Compute recommendations for the given project, a syntax sugar for the compute method."""
        instance = cls(count=count, limit=limit, recommendation_type=recommendation_type)

        graph = GraphDatabase()
        graph.connect()

        scoring = Scoring(
            graph=graph,
            runtime_environment=runtime_environment,
            python_version=project.python_version,
        )
        report = instance.compute(
            graph,
            project,
            runtime_environment,
            scoring.get_scoring_function(recommendation_type),
            dry_run=dry_run
        )
        return scoring.get_stack_info(), report
