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

from thoth.adviser.enums import DecisionType
from thoth.python import Project
from thoth.storages import GraphDatabase

from .builder import PipelineBuilder
from .pipeline import Pipeline

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
    *,
    output_function: typing.Callable,
    decision_type: DecisionType,
    count: int = None,
    dry_run: bool = False,
    limit_latest_versions: int = None,
    library_usage: dict = None,
) -> dict:
    """Run dependency monkey."""
    builder = PipelineBuilder(graph, project, library_usage)
    pipeline_config = builder.get_dependency_monkey_pipeline_config(
        decision_type, limit_latest_versions=limit_latest_versions
    )
    pipeline = Pipeline(
        steps=pipeline_config.steps,
        strides=pipeline_config.strides,
        graph=graph,
        project=project,
    )

    computed = 0
    result = {"output": [], "computed": 0}
    # The limit and count arguments propagated down to pipeline are set
    # to the same number as in case of dependency monkey we do not care how
    # many stacks are discarded - we want all which went through the pipeline.
    for pipeline_product in pipeline.conduct(count=count, limit=count):
        computed += 1
        pipeline_product.finalize()

        if not dry_run:
            entry = output_function(pipeline_product.project, count=computed)
            if entry:
                result["output"].append(entry)

        if count is not None and computed >= count:
            break

    result["computed"] = computed
    result["stack_info"] = pipeline.get_stack_info()
    return result


def dependency_monkey(
    project: Project,
    output: str = None,
    *,
    seed: int = None,
    decision_type: DecisionType = DecisionType.ALL,
    dry_run: bool = False,
    context: str = None,
    count: int = None,
    limit_latest_versions: int = None,
    library_usage: dict = None,
) -> dict:
    """Run Dependency Monkey on the given stack.

    @param project: a Python project to be used for generating software stacks (lockfile is not needed)
    @param output: output (Amun API, directory or '-' for stdout) where stacks should be written to
    @param seed: a seed to be used in case of random stack generation
    @param decision_type: decision to be used when filtering out undesired stacks
    @param dry_run: do not perform actual writing to output, just run the dependency monkey report back computed stacks
    @param context: context to be sent to Amun, if output is set to be Amun
    @param count: generate upto N stacks
    @param limit_latest_versions: number of latest versions considered for each package when generation is done
    @library_usage: library usage to supply additional configuration in stack generation pipeline
    """
    output = output or "-"  # Default to stdout if no output was provided.

    graph = GraphDatabase()
    graph.connect()

    random.seed(seed)

    if count is not None and (count <= 0):
        raise ValueError("Number of stacks has to be a positive integer")

    if output.startswith(("https://", "http://")):
        # Submitting to Amun
        _LOGGER.info("Stacks will be submitted to Amun at %r", output)
        if context:
            _LOGGER.debug("Loading Amun context")
            try:
                context = json.loads(context)
            except Exception as exc:
                raise ValueError(
                    "Failed to load Amun context that should be passed with generated stacks: %s",
                    str(exc),
                )
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
            raise ValueError(
                "Unable to use context when writing generated projects onto filesystem"
            )

        if not os.path.isdir(output):
            os.makedirs(output, exist_ok=True)

        output_function = partial(_dm_amun_directory_output, output)

    return _do_dependency_monkey(
        project,
        graph=graph,
        dry_run=dry_run,
        decision_type=decision_type,
        count=count,
        output_function=output_function,
        limit_latest_versions=limit_latest_versions,
        library_usage=library_usage,
    )
