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


"""Dependency Monkey traverses dependency graph and generates stacks."""

import random
import os
from functools import partial
import typing
import logging
import sys
import json

from amun import inspect as amun_inspect

from thoth.python import Project
from thoth.adviser.python import DependencyGraph
from thoth.adviser.python.helpers import fill_package_digests_from_graph
from thoth.common import RuntimeEnvironment
from thoth.storages import GraphDatabase

from .decision import DecisionFunction

_LOGGER = logging.getLogger(__name__)


def dm_amun_inspect_wrapper(
    output: str, context: dict, generated_project: Project, count: int
) -> typing.Optional[str]:
    """A wrapper around Amun inspection call."""
    context["python"] = generated_project.to_dict()
    try:
        response = amun_inspect(output, **context)
        _LOGGER.info(
            "Submitted Amun inspection #%d: %r", count, response["inspection_id"]
        )
        _LOGGER.debug("Full Amun response: %s", response)
        return response["inspection_id"]
    except Exception as exc:
        _LOGGER.exception("Failed to submit stack to Amun analysis: %s", str(exc))

    return None


def _dm_amun_directory_output(output: str, generated_project: Project, count: int):
    """A wrapper for placing generated software stacks onto filesystem."""
    _LOGGER.debug("Writing stack %d", count)

    path = os.path.join(output, f"{count:d}")
    os.makedirs(path, exist_ok=True)

    _LOGGER.info("Writing project into output directory %r", path)
    generated_project.to_files(
        os.path.join(path, "Pipfile"), os.path.join(path, "Pipfile.lock")
    )

    return path


def _dm_stdout_output(generated_project: Project, count: int):
    """A function called if the project should be printed to stdout as a dict."""
    json.dump(generated_project.to_dict(), fp=sys.stdout, sort_keys=True, indent=2)
    return None


def _do_dependency_monkey(
    project: Project,
    graph: GraphDatabase,
    runtime_environment: RuntimeEnvironment,
    *,
    output_function: typing.Callable,
    decision_function: typing.Callable,
    count: int = None,
    dry_run: bool = False,
) -> dict:
    """Run dependency monkey."""
    dependency_graph = DependencyGraph.from_project(graph, project, runtime_environment, restrict_indexes=True)

    computed = 0
    result = {"output": [], "computed": 0}
    for _, generated_project in dependency_graph.walk(decision_function):
        computed += 1
        generated_project = fill_package_digests_from_graph(generated_project, graph)

        if not dry_run:
            entry = output_function(generated_project, count=computed)
            if entry:
                result["output"].append(entry)

        if count is not None and computed >= count:
            break

    result["computed"] = computed
    return result


def dependency_monkey(
    project: Project,
    output: str = None,
    *,
    seed: int = None,
    decision_function_name: str = None,
    dry_run: bool = False,
    context: str = None,
    count: int = None,
    runtime_environment: RuntimeEnvironment = None,
) -> dict:
    """Run Dependency Monkey on the given stack.

    @param project: a Python project to be used for generating software stacks (lockfile is not needed)
    @param output: output (Amun API, directory or '-' for stdout) where stacks should be written to
    @param seed: a seed to be used in case of random stack generation
    @param decision_function_name: decision function to be used
    @param dry_run: do not perform actual writing to output, just run the dependency monkey report back computed stacks
    @param context: context to be sent to Amun, if output is set to be Amun
    @param runtime_environment: targeted runtime environment used in dependency monkey runs
    @param count: generate upto N stacks
    """
    output = output or "-"  # Default to stdout if no output was provided.

    graph = GraphDatabase()
    graph.connect()

    decision_function = DecisionFunction.get_decision_function(
        graph, decision_function_name, runtime_environment
    )
    random.seed(seed)

    if count is not None and (count <= 0):
        _LOGGER.error("Number of stacks has to be a positive integer")
        return 3

    if output.startswith(("https://", "http://")):
        # Submitting to Amun
        _LOGGER.info("Stacks will be submitted to Amun at %r", output)
        if context:
            _LOGGER.debug("Loading Amun context")
            try:
                context = json.loads(context)
            except Exception as exc:
                _LOGGER.error(
                    "Failed to load Amun context that should be passed with generated stacks: %s",
                    str(exc),
                )
                return 1
        else:
            context = {}
            _LOGGER.warning("Context to Amun API is empty")

        output_function = partial(dm_amun_inspect_wrapper, output, context)
    elif output == "-":
        _LOGGER.debug("Stacks will be printed to stdout")
        output_function = _dm_stdout_output
    else:
        _LOGGER.info("Stacks will be written to %r", output)
        if context:
            _LOGGER.error(
                "Unable to use context when writing generated projects onto filesystem"
            )
            return 2

        if not os.path.isdir(output):
            os.makedirs(output, exist_ok=True)

        output_function = partial(_dm_amun_directory_output, output)

    return _do_dependency_monkey(
        project,
        graph=graph,
        runtime_environment=runtime_environment,
        dry_run=dry_run,
        decision_function=decision_function,
        count=count,
        output_function=output_function,
    )
