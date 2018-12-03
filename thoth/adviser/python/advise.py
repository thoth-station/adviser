#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
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
import operator
import typing

import attr
import random

from thoth.solver.python.base import SolverException
from thoth.python import Project
from thoth.adviser.python import DECISISON_FUNCTIONS
from thoth.adviser.python import DEFAULT_DECISION_FUNCTION
from thoth.adviser.python import DependencyGraph
from thoth.adviser.enums import RecommendationType
from thoth.adviser.python.helpers import fill_package_digests_from_graph

_LOGGER = logging.getLogger(__name__)

class HeapEntry:
    __slots__ = ['score', 'reasoning', 'generated_project']

    def __init__(self, score: float, reasoning: list, generated_project: Project):
        self.score = score
        self.reasoning = reasoning
        self.generated_project = generated_project

    def __gt__(self, other):
        return self.score > other.score

    def get_entries(self) -> tuple:
        return self.reasoning, self.generated_project


@attr.s(slots=True)
class Adviser:
    """Implementation of adviser - the core of recommendation engine in Thoth."""

    recommendation_type = attr.ib(type=RecommendationType, default=RecommendationType.LATEST)
    count = attr.ib(type=int, default=None)
    limit = attr.ib(type=int, default=None)
    _computed_stacks_heap = attr.ib(type=list, default=attr.Factory(list))
    _visited = attr.ib(type=int, default=0)

    def compute(self, project: Project, decision_function: typing.Callable = None, dry_run: bool = False) -> typing.List[Project]:
        """Compute recommendations for the given project."""
        decision_function = decision_function or DEFAULT_DECISION_FUNCTION
        dependency_graph = DependencyGraph.from_project(project)

        try:
            for decision_function_result, generated_project in dependency_graph.walk(decision_function):
                score, reasoning = decision_function_result
                self._visited += 1

                if dry_run:
                    continue

                heap_entry = HeapEntry(score, reasoning, generated_project)
                if self.count is not None and len(self._computed_stacks_heap) >= self.count:
                    heapq.heappushpop(self._computed_stacks_heap, heap_entry)
                else:
                    heapq.heappush(self._computed_stacks_heap, heap_entry)

                if self.limit is not None and self._visited >= self.count:
                    break

            if dry_run:
                return self._visited

            # Sort computed stacks based on score and return them.
            result = (item.get_entries() for item in sorted(self._computed_stacks_heap))
            _LOGGER.info("Filling package digests to software stacks")
            #result = sorted(
            #    [(item[0], fill_package_digests_from_graph(item[1])) for item in result], key=operator.itemgetter(0)
            #)
            result = [(item[0], fill_package_digests_from_graph(item[1])) for item in result]
            return result
        finally:
            self._computed_stacks_heap = []
            self._visited = 0

    @classmethod
    def compute_on_project(cls, project: Project, *,
                           decision_function: typing.Callable = None,
                           recommendation_type: RecommendationType = RecommendationType.LATEST,
                           count: int = None,
                           limit: int = None,
                           dry_run: bool = False) -> list:
        """Compute recommendations for the given project, a syntax sugar for the compute method."""
        instance = cls(recommendation_type=recommendation_type, count=count, limit=limit)
        return instance.compute(project, decision_function, dry_run=dry_run)
