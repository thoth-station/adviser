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
from thoth.adviser.isis import Isis
from thoth.adviser.exceptions import InternalError
from thoth.common import RuntimeEnvironment
from thoth.storages import GraphDatabase

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Scoring:
    """Scoring functions used for computing advises."""

    graph = attr.ib(type=GraphDatabase)
    runtime_environment = attr.ib(type=RuntimeEnvironment)
    python_version = attr.ib(type=str)
    _counter = attr.ib(type=int, default=0)
    _stack_info = attr.ib(type=set, default=attr.Factory(set))
    _isis = attr.ib(type=Isis, default=attr.Factory(Isis))
    _reported_no_isis_record = attr.ib(type=set, default=attr.Factory(set))

    _CVE_PENALIZATION = -0.1
    _PERFORMANCE_PENALIZATION = 0.2
    _PERFORMANCE_IMPACT_THRESHOLD = 0.0

    def get_scoring_function(
        self, recommendation_type: RecommendationType
    ) -> typing.Callable:
        """Get a bound method keeping connected adapter to a graph database with runtime information."""
        if recommendation_type == RecommendationType.STABLE:
            _LOGGER.info("Using scoring function obtaining stable software stacks")
            return self.stable_scoring_function

        if recommendation_type == RecommendationType.TESTING:
            _LOGGER.info("Using scoring function with experimental testing stacks")
            return self.testing_scoring_function

        if recommendation_type == RecommendationType.LATEST:
            _LOGGER.info("Using scoring function that will generate latest stacks")
            return self.latest_scoring_function

        raise InternalError(
            f"No scoring function defined for recommendation type {recommendation_type}"
        )

    def get_stack_info(self) -> typing.Optional[list]:
        """Get a generic report which is generic for the application stack."""
        return (
            list(dict(item) for item in self._stack_info) if self._stack_info else None
        )

    def _get_performance_substack(
        self, packages: typing.List[tuple]
    ) -> typing.List[tuple]:
        """Filter out packages from stack (packages lists) that do not have performance impact.

        The filtering is done based on queries to Amun API (project2vec API service).
        """
        result = []
        packages_performance_impact = self._isis.get_python_package_performance_impact_all(
            packages
        )
        for (
            package_tuple,
            performance_impact_score,
        ) in packages_performance_impact.items():
            if performance_impact_score is None:
                if package_tuple not in self._reported_no_isis_record:
                    _LOGGER.warning(
                        "Package %r has no record on Isis, assuming its positive performance impact",
                        package_tuple,
                    )
                    self._reported_no_isis_record.add(package_tuple)
                result.append(package_tuple)
            elif performance_impact_score > self._PERFORMANCE_IMPACT_THRESHOLD:
                _LOGGER.debug(
                    "Package %r included in sub-stack for performance scoring (score: %f, threshold: %f)",
                    package_tuple,
                    performance_impact_score,
                    self._PERFORMANCE_IMPACT_THRESHOLD,
                )
                result.append(package_tuple)
            else:
                _LOGGER.debug(
                    "Excluding package %r from sub-stack used in performance scoring (score: %f, threshold: %f)",
                    package_tuple,
                    performance_impact_score,
                    self._PERFORMANCE_IMPACT_THRESHOLD,
                )

        return result

    def _performance_scoring(
        self, packages: typing.List[tuple]
    ) -> typing.Tuple[float, list]:
        """Score the given stack based on performance."""
        _LOGGER.debug("Obtaining performance index for stack")
        hardware = self.runtime_environment.hardware.to_dict(without_none=True)
        packages = self._get_performance_substack(packages)
        # TODO: add operating system and cuda/python version to the query
        performance_index = self.graph.compute_python_package_version_avg_performance(
            packages, hardware_specs=hardware
        )

        if math.isnan(performance_index):
            return 0.0, []
        else:
            _LOGGER.info("Performance index for stack: %f", performance_index)

        score = (100 - performance_index) * self._PERFORMANCE_PENALIZATION
        return score, [{"performance": performance_index}]

    def _cve_scoring(self, packages: typing.List[tuple]) -> typing.Tuple[float, list]:
        """Scoring against CVE database."""
        report = []
        for package in packages:
            cves = self.graph.get_python_cve_records(package[0], package[1])
            for cve_record in cves:
                cve_record.update(
                    {
                        "type": "WARNING",
                        "package": package[0],
                        "version": package[1],
                        "version_range": cve_record["version_range"],
                        "justification": "Found a CVE for the package",
                    }
                )
                report.append(cve_record)
                # Add for the complete listing for user information.
                cve_record = dict(cve_record)
                cve_record.pop("version")
                cve_record[
                    "justification"
                ] = f"Resolution of package {package[0]!r} can lead to a version with CVE"
                self._stack_info.add(tuple(cve_record.items()))

        cve_count = len(report)
        if cve_count > 0:
            _LOGGER.warning(
                "Found %d CVE%s in the application stack",
                cve_count,
                "s" if cve_count != 1 else "",
            )

        score = 0.0 if not report else self._CVE_PENALIZATION * cve_count

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

        scoring, scoring_reasoning = self._cve_scoring(packages)
        score += scoring
        reasoning.extend(scoring_reasoning)

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
