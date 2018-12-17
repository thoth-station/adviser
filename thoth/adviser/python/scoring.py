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

"""Scoring functions used when computing advises."""

import math
import typing
import logging

import attr

from thoth.adviser import RecommendationType
from thoth.adviser.exceptions import InternalError
from thoth.adviser import RuntimeEnvironment
from thoth.storages import GraphDatabase
from thoth.python import PackageVersion

from .decision import DEFAULT_DECISION_FUNCTION

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Scoring:
    """Scoring functions used for computing advises."""

    graph = attr.ib(type=GraphDatabase)
    runtime_environment = attr.ib(type=RuntimeEnvironment)

    @classmethod
    def get_scoring_function(cls, graph: GraphDatabase, recommendation_type: RecommendationType, runtime_environment: RuntimeEnvironment) -> typing.Callable:
        """Retrieve a bound method to an instance keeping connected adapter to a graph database with runtime information."""
        instance = cls(graph=graph, runtime_environment=runtime_environment)

        if recommendation_type == RecommendationType.STABLE:
            _LOGGER.info("Using scoring function obtaining stable software stacks")
            return instance.stable_scoring_function

        if recommendation_type == RecommendationType.TESTING:
            _LOGGER.info("Using scoring function with experimental testing stacks")
            return instance.testing_scoring_function

        raise InternalError(f"No scoring function defined for recommendation type {recommendation_type}")

    def _performance_scoring(self, packages: typing.List[tuple]) -> typing.Tuple[float, list]:
        """Score the given stack based on performance."""
        # TODO: filter out packages that do not have impact on performance
        _LOGGER.info("Obtaining performance index for stack")
        performance_index = self.graph.compute_python_package_version_avg_performance(
            packages,
            hardware_specs=self.runtime_environment.to_dict()
        )

        _LOGGER.info("Perfomance index for stack: %f", performance_index)
        if math.isnan(performance_index):
            return None, []

        return performance_index, [{'Performance index': performance_index}]

    def stable_scoring_function(self, packages: typing.Sequence[PackageVersion]) -> typing.Tuple[float, list]:
        """Scoring function used for scoring stacks based on stability."""
        packages = [package.to_tuple_locked() for package in packages]
        return self._performance_scoring(packages)

    def testing_scoring_function(self, packages: typing.Sequence[PackageVersion]) -> typing.Tuple[float, list]:
        """Expecimental software stacks scoring."""
        raise NotImplementedError
