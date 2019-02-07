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

"""Scoring functions used when computing advises."""

import typing
import logging
import math

import attr

from thoth.adviser import RecommendationType
from thoth.adviser.exceptions import InternalError
from thoth.adviser import RuntimeEnvironment
from thoth.storages import GraphDatabase
from thoth.python import PackageVersion

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Scoring:
    """Scoring functions used for computing advises."""

    graph = attr.ib(type=GraphDatabase)
    runtime_environment = attr.ib(type=RuntimeEnvironment)
    python_version = attr.ib(type=str)
    _counter = attr.ib(type=int, default=0)

    _CVE_PENALIZATION = 0.1
    _PERFORMANCE_PENALIZATION = 0.2

    @classmethod
    def get_scoring_function(
        cls,
        graph: GraphDatabase,
        recommendation_type: RecommendationType,
        runtime_environment: RuntimeEnvironment,
        python_version: str,
    ) -> typing.Callable:
        """Get a bound method keeping connected adapter to a graph database with runtime information."""
        instance = cls(
            graph=graph,
            runtime_environment=runtime_environment,
            python_version=python_version,
        )

        if recommendation_type == RecommendationType.STABLE:
            _LOGGER.info("Using scoring function obtaining stable software stacks")
            return instance.stable_scoring_function

        if recommendation_type == RecommendationType.TESTING:
            _LOGGER.info("Using scoring function with experimental testing stacks")
            return instance.testing_scoring_function

        if recommendation_type == RecommendationType.LATEST:
            _LOGGER.info("Using scoring function that will generate latest stacks")
            return instance.latest_scoring_function

        raise InternalError(
            f"No scoring function defined for recommendation type {recommendation_type}"
        )

    def _performance_scoring(
        self, packages: typing.List[tuple]
    ) -> typing.Tuple[float, list]:
        """Score the given stack based on performance."""
        # TODO: filter out packages that do not have impact on performance
        _LOGGER.info("Obtaining performance index for stack")
        performance_index = self.graph.compute_python_package_version_avg_performance(
            packages, hardware_specs=self.runtime_environment.to_dict()
        )

        _LOGGER.info("Performance index for stack: %f", performance_index)

        if math.isnan(performance_index):
            return 0.0, []

        score = (1.0 - performance_index) * self._PERFORMANCE_PENALIZATION
        return score, [{"performance": performance_index}]

    def _cve_scoring(self, packages: typing.List[tuple]) -> typing.Tuple[float, list]:
        """Scoring against CVE database."""
        report = []
        for package in packages:
            cves = self.graph.get_python_cve_records(package[0], packages[1])
            if cves:
                report.append(cves)

        score = 0.0 if not report else self._CVE_PENALIZATION * len(report)
        return score, report

    def stable_scoring_function(
        self, packages: typing.List[tuple]
    ) -> typing.Tuple[float, list]:
        """Scoring function used for scoring stacks based on stability."""
        reasoning = []
        score = 0.0

        scoring, scoring_reasoning = self._performance_scoring(packages)
        score += scoring
        reasoning.extend(scoring_reasoning)

        """
        _LOGGER.info("Scoring...")
        scoring, scoring_reasoning = self._cve_scoring(package_tuples)
        score += scoring
        reasoning.extend(scoring_reasoning)
        _LOGGER.info("Finished scoring...")
        """

        return score, reasoning

    def testing_scoring_function(
        self, packages: typing.List[tuple]
    ) -> typing.Tuple[typing.Optional[float], list]:
        """Experimental software stacks scoring."""
        raise NotImplementedError

    def latest_scoring_function(
        self, _: typing.List[tuple]
    ) -> typing.Tuple[typing.Optional[float], list]:
        """Get latest software stacks."""
        # As we preserve order in which software stacks are generated, we just return a positive score. As software
        # stacks get generated, we just append them to the resulting list in the adviser report.
        self._counter += 1
        return 1.0, [{"Latest stack": self._counter}]
