#!/usr/bin/env python3
# thoth-adviser
# copyright(c) 2019 fridolin pokorny
#
# this program is free software: you can redistribute it and / or modify
# it under the terms of the gnu general public license as published by
# the free software foundation, either version 3 of the license, or
# (at your option) any later version.
#
# this program is distributed in the hope that it will be useful,
# but without any warranty without even the implied warranty of
# merchantability or fitness for a particular purpose. see the
# gnu general public license for more details.
#
# you should have received a copy of the gnu general public license
# along with this program. if not, see <http://www.gnu.org/licenses/>.

"""Shared code for strides and steps."""

import math
import logging
import itertools

from typing import Tuple
from typing import Set
from typing import List
from typing import Iterable

from thoth.adviser.isis import Isis
from thoth.storages import GraphDatabase
from thoth.python import Project

_LOGGER = logging.getLogger(__name__)

# Keep set of reported warnings per adviser run so each package is reported just once.
_REPORTED_NO_ISIS_RECORD = set()


def get_performance_impact_packages(
    package_tuples: Iterable[Tuple[str, str, str]], threshold: float = 0.0
) -> Set[Tuple[str, str, str]]:
    """Get packages which can affect performance in some way."""
    performance_impact = Isis().get_python_package_performance_impact_all(
        package_tuples
    )

    performance_impact_packages = set()
    for package_tuple in package_tuples:
        performance_score = performance_impact[package_tuple]

        if performance_score is None:
            if package_tuple not in _REPORTED_NO_ISIS_RECORD:
                _LOGGER.warning(
                    "Package %r has no record on Isis, assuming its positive performance impact",
                    package_tuple,
                )
                _REPORTED_NO_ISIS_RECORD.add(package_tuple)
        elif performance_score > threshold:
            performance_impact_packages.add(package_tuple)

    return performance_impact_packages


def get_performance(
    graph: GraphDatabase,
    project: Project,
    package_tuples: Iterable[Tuple[str, str, str]],
    threshold: float = 0.0,
) -> List[Tuple[float, Set[Tuple[str, str, str]]]]:
    """Group packages into a set of packages which can affect performance with their score based on observations."""
    result = []
    performance_impact_packages = get_performance_impact_packages(
        package_tuples, threshold
    )

    # Prepare runtime and hardware information for the graph query - this is a bit not nice, but we need
    # to do it this way based on graph schema.
    runtime_environment = project.runtime_environment.to_dict(without_none=True)
    hardware = runtime_environment.pop("hardware", None)

    if project.runtime_environment.operating_system.name:
        runtime_environment[
            "os_name"
        ] = project.runtime_environment.operating_system.name
        if project.runtime_environment.operating_system.version:
            runtime_environment[
                "os_version"
            ] = project.runtime_environment.operating_system.version

    runtime_environment.pop("operating_system", None)

    package_type_map = {}
    for package_tuple in performance_impact_packages:
        if package_tuple[0] not in package_type_map:
            package_type_map[package_tuple[0]] = []

        package_type_map[package_tuple[0]].append(package_tuple)

    for packages in itertools.product(*package_type_map.values()):
        if not packages:
            # No product was made.
            continue

        score = graph.compute_python_package_version_avg_performance(
            set(packages),
            runtime_environment=runtime_environment,
            hardware_specs=hardware,
        )
        if math.isnan(score) or score is None:
            _LOGGER.debug("No performance records found for packages %r", packages)
            continue
        elif score > threshold:
            _LOGGER.debug(
                "Adding packages %r to performance impact result set with a score of %f",
                packages,
                score,
            )
            result.append((score, set(packages)))
            pass
        else:
            _LOGGER.debug("Discarding packages %r from performance impact result set")

    return result
