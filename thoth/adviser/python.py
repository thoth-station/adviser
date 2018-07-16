#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""Compute advises on PyPI ecosystem."""

import typing
from collections import deque
from itertools import chain
import logging

from pip._vendor.packaging.requirements import Requirement

from thoth.solver import pip_compile
from thoth.solver.exceptions import ThothPipCompileError

from .enums import RecommendationType
from .enums import Ecosystem
from .scoring import score_package_version


_LOGGER = logging.getLogger(__name__)


def _parse_requirements(requiremnets: typing.List[str]) -> typing.List[Requirement]:
    """Parse the given requirements into pip's internal Requirement object."""
    return [Requirement(req) for req in requiremnets if req and not req.strip().startswith('#')]


def _get_from_dependencies(comment: str):
    """Get dependent packages from pip-compile output."""
    result = []

    comment = comment[len('via '):]
    for dep in comment.split(','):
        result.append(dep.strip())

    return result


def _execute_pip_compile(*requirements: Requirement) -> typing.List[Requirement]:
    """Execute pip-compile on parser requirements, also get flattened dependency tree as a dict (reverse mapping)."""
    result = []
    graph = {}

    output = pip_compile(*[str(req) for req in requirements])
    for line in output.splitlines():
        if line.startswith('#'):
            # Skip leading pip-compile comments.
            continue
        line = line.split('#', maxsplit=1)

        if len(line) == 2:
            requirement, comment = line
            requirement = Requirement(requirement)
            result.append(requirement)

            from_dependencies = _get_from_dependencies(comment)
            graph[requirement.name] = from_dependencies
        else:
            requirement = Requirement(line[0])
            result.append(requirement)
            # This is root node.
            graph[requirement.name] = []

    return result, graph


def _find_transitive(graph, package_name):
    """Get all packages that introduced the given package either transitively or directly based on dependency graph."""
    assert package_name in graph,\
        f"The requested package {package_name} does not occur in the dependency graph {graph}"

    result = deque()
    queue = deque([(package_name, [], set())])
    while queue:
        package_name, traversed, seen = queue.pop()
        ancestors = graph.get(package_name)

        if not ancestors:
            if traversed:
                result.append(traversed)
            continue

        for ancestor in ancestors:
            if ancestor not in seen:
                new_seen = seen | set(ancestor)
                queue.append((ancestor, traversed + [ancestor], new_seen))

    return list(result)


def _get_version(package_name, pinned_requirements):
    """Get version of a package from pinned requirements."""
    for requirement in pinned_requirements:
        if requirement.name == package_name:
            return str(requirement).split('==', maxsplit=1)[1]

    raise RuntimeError("Unreachable code - package name not found in the pinned stack")


def exclude_requirement(requirement: Requirement,
                        requirements: typing.List[Requirement],
                        pinned_requirements: typing.List[Requirement],
                        dependency_graph: dict) -> typing.List[typing.List[Requirement]]:
    """Exclude the given package version from requirements.

    This function excludes the given requirement by putting putting restriction into the original requirements.
    As the given package version can be introduced by transitively, we need to take into account also all its
    transitive ancestors.
    """
    candidates = []

    requirement_version = str(requirement).split('==', maxsplit=1)[1]
    new_requirements = list(requirements)
    new_requirements.append(Requirement(f"{requirement.name}!={requirement_version}"))
    candidates.append(new_requirements)

    # Also all transitive requirements.
    packages = _find_transitive(dependency_graph, requirement.name)
    for package in set(chain(*packages)):
        package_version = _get_version(package, pinned_requirements)
        new_requirements = list(requirements)
        new_requirements.append(Requirement(f"{package}!={package_version}"))
        candidates.append(new_requirements)

    return candidates


def advise_python(raw_requirements: typing.List[str],
                  recommendation_type: RecommendationType,
                  runtime_environment: str=None) -> dict:
    """Give recommendation on Python package requirements."""
    info = {}
    requirements = _parse_requirements(raw_requirements)

    if recommendation_type == RecommendationType.LATEST:
        # Early stop for LATEST
        return {'stacks': [requirements], 'info': "Warning: observations were not considered when LATEST is used"}

    stacks = []
    queue = deque([requirements])
    while queue:
        requirements = queue.pop()

        _LOGGER.info(f"New resolution run for requirements: {[str(req) for req in requirements]}")

        try:
            pinned_requirements, dependency_graph = _execute_pip_compile(*requirements)
        except ThothPipCompileError as exc:
            _LOGGER.warning(f"Requirement specification was invalid: {[str(req) for req in requirements]}: {str(exc)}")
            continue

        for requirement in pinned_requirements:
            package_name, package_version = requirement.name, str(requirement.specifier)[len('=='):]
            is_ok = score_package_version(package_name, package_version,
                                          ecosystem=Ecosystem.PYTHON, runtime_environment=runtime_environment)

            if is_ok is None and recommendation_type == RecommendationType.TESTING.name:
                # TODO: append this to list instead of having a key from package name
                info[str(requirement)] = "Warning: No observations found"
            elif (is_ok is None and recommendation_type == RecommendationType.STABLE.name) or is_ok is False:
                justification = "Package excluded - negative observations found in the knowledge database" \
                    if is_ok is False else "Package excluded - no observations found in the knowledge database"

                # TODO: append this to list instead of having a key from package name
                info[str(requirement)] = justification
                candidates = exclude_requirement(
                    requirement,
                    requirements,
                    pinned_requirements,
                    dependency_graph,
                )
                queue.extend(candidates)
                break
        else:
            stacks.append(pinned_requirements)

    return {
        'stacks': list(map(lambda s: [str(req) for req in s], stacks)),
        'info': info,
        'type': recommendation_type.name,
        'runtime_environment': runtime_environment,
        'requirements': raw_requirements
    }
