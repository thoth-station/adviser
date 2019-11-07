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
# type: ignore

"""Thoth-adviser CLI."""

import json
import logging
import os
import time
from functools import partial
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

import attr
import click
from thoth.analyzer import print_command_result
from thoth.common import init_logging
from thoth.common import RuntimeEnvironment
from thoth.python import Pipfile
from thoth.python import PipfileLock
from thoth.python import Project

from thoth.adviser.anneal import AdaptiveSimulatedAnnealing
from thoth.adviser.dependency_monkey import DependencyMonkey
from thoth.adviser.digests_fetcher import GraphDigestsFetcher
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import PythonRecommendationOutput
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import AdviserException
from thoth.adviser.exceptions import InternalError
from thoth.adviser import __title__ as analyzer_name
from thoth.adviser import __version__ as analyzer_version
from thoth.adviser.pipeline_builder import PipelineBuilder
from thoth.adviser.run import subprocess_run
from thoth.adviser.temperature import ASATemperatureFunction
from thoth.storages import GraphDatabase

init_logging()

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class _PrintFunc:
    """A print function - a workaround for typing and kwargs arguments."""

    func = attr.ib(type=Callable)

    def __call__(self, duration: float, result: Dict[str, Any]) -> None:
        self.func(duration=duration, result=result)


def _print_version(ctx: click.Context, _, value: str):
    """Print adviser version and exit."""
    if not value or ctx.resilient_parsing:
        return

    click.echo(analyzer_version)
    ctx.exit()


def _instantiate_project(
    requirements: str,
    requirements_locked: Optional[str] = None,
    runtime_environment: RuntimeEnvironment = None,
):
    """Create Project instance based on arguments passed to CLI."""
    if os.path.isfile(requirements):
        with open(requirements, "r") as requirements_file:
            requirements = requirements_file.read()

        if requirements_locked:
            with open(requirements_locked, "r") as requirements_file:
                requirements_locked = requirements_file.read()
            del requirements_file
    else:
        # We we gather values from env vars, un-escape new lines.
        requirements = requirements.replace("\\n", "\n")
        if requirements_locked:
            requirements_locked = requirements_locked.replace("\\n", "\n")

    pipfile = Pipfile.from_string(requirements)
    pipfile_lock = (
        PipfileLock.from_string(requirements_locked, pipfile)
        if requirements_locked
        else None
    )
    project = Project(
        pipfile=pipfile,
        pipfile_lock=pipfile_lock,
        runtime_environment=runtime_environment or RuntimeEnvironment.from_dict({}),
    )

    return project


@click.group()
@click.pass_context
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    envvar="THOTH_ADVISER_DEBUG",
    help="Be verbose about what's going on.",
)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    callback=_print_version,
    expose_value=False,
    help="Print adviser version and exit.",
)
@click.option(
    "--metadata",
    type=str,
    envvar="THOTH_ADVISER_METADATA",
    help="Metadata in a form of a JSON which are used for carrying additional context in Thoth deployment.",
)
def cli(ctx=None, verbose=False, metadata=None):
    """Thoth adviser command line interface."""
    if ctx:
        ctx.auto_envvar_prefix = "THOTH_ADVISER"

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    _LOGGER.debug("Debug mode is on")
    _LOGGER.info("Version: %s", analyzer_version)

    # This value is unused here, but is reported from click context.
    metadata = metadata


@cli.command()
@click.pass_context
@click.option(
    "--requirements",
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    required=True,
    help="Pipfile to be checked for provenance.",
)
@click.option(
    "--requirements-locked",
    "-l",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS_LOCKED",
    required=True,
    help="Pipenv.lock file stating currently locked packages.",
)
@click.option(
    "--output",
    "-o",
    type=str,
    envvar="THOTH_ADVISER_OUTPUT",
    default="-",
    help="Output file or remote API to print results to, in case of URL a POST request is issued.",
)
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
@click.option(
    "--whitelisted-sources",
    "-i",
    type=str,
    required=False,
    envvar="THOTH_WHITELISTED_SOURCES",
    help="A comma separated list of whitelisted simple repositories providing packages - if not "
    "provided, all indexes are whitelisted (example: https://pypi.org/simple/).",
)
def provenance(
    click_ctx: click.Context,
    requirements: str,
    requirements_locked: str,
    output: str,
    whitelisted_sources: Optional[str] = None,
    no_pretty: bool = False,
):
    """Check provenance of packages based on configuration."""
    parameters = locals()
    parameters.pop("click_ctx")
    start_time = time.monotonic()
    _LOGGER.debug("Passed arguments: %s", parameters)

    whitelisted_sources = whitelisted_sources.split(",") if whitelisted_sources else []
    result = {
        "error": None,
        "report": [],
        "parameters": {"whitelisted_indexes": whitelisted_sources},
        "input": None,
    }
    try:
        project = _instantiate_project(requirements, requirements_locked)
        result["input"] = project.to_dict()
        report = project.check_provenance(
            whitelisted_sources=whitelisted_sources,
            digests_fetcher=GraphDigestsFetcher(),
        )
    except AdviserException as exc:
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        _LOGGER.exception("Error during checking provenance: %s", str(exc))
        result["error"] = True
        result["error_msg"] = str(exc)
        result["report"] = [
            {"type": "ERROR", "justification": f"{str(exc)} ({type(exc).__name__})"}
        ]
    else:
        result["error"] = False
        result["error_msg"] = None
        result["report"] = report

    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=output,
        duration=time.monotonic() - start_time,
        pretty=not no_pretty,
    )

    click_ctx.exit(int(result["error"] is True))


@cli.command()
@click.pass_context
@click.option(
    "--requirements",
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    required=True,
    help="Requirements to be advised.",
)
@click.option(
    "--requirements-locked",
    "-l",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS_LOCKED",
    help="Currently locked down requirements used.",
)
@click.option(
    "--requirements-format",
    "-f",
    envvar="THOTH_REQUIREMENTS_FORMAT",
    default="pipenv",
    required=True,
    type=click.Choice(["pipenv", "requirements"]),
    help="The output format of requirements that are computed based on recommendations.",
)
@click.option(
    "--output",
    "-o",
    type=str,
    envvar="THOTH_ADVISER_OUTPUT",
    default="-",
    help="Output file or remote API to print results to, in case of URL a POST request is issued.",
)
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
@click.option(
    "--recommendation-type",
    "-t",
    envvar="THOTH_ADVISER_RECOMMENDATION_TYPE",
    default="STABLE",
    required=True,
    type=click.Choice([e.name for e in RecommendationType]),
    help="Type of recommendation generated based on knowledge base.",
)
@click.option(
    "--count",
    type=int,
    envvar="THOTH_ADVISER_COUNT",
    help="Number of software stacks shown in the output.",
    default=AdaptiveSimulatedAnnealing.DEFAULT_COUNT,
    show_default=True,
)
@click.option(
    "--limit",
    type=int,
    envvar="THOTH_ADVISER_LIMIT",
    help="Number of software stacks that should be taken into account (stop after reaching the limit).",
    default=AdaptiveSimulatedAnnealing.DEFAULT_LIMIT,
    show_default=True,
)
@click.option(
    "--seed",
    type=int,
    envvar="THOTH_ADVISER_SEED",
    help="A seed used for generating random numbers (defaults to time if omitted).",
)
@click.option(
    "--library-usage",
    type=str,
    envvar="THOTH_ADVISER_LIBRARY_USAGE",
    help="Add library usage information to adviser's resolution algorithm.",
)
@click.option(
    "--runtime-environment",
    "-e",
    envvar="THOTH_ADVISER_RUNTIME_ENVIRONMENT",
    type=str,
    help="Runtime environment specification (file or directly JSON) to describe target environment.",
)
@click.option(
    "--plot-history",
    envvar="THOTH_ADVISER_PLOT_HISTORY",
    type=str,
    help="Plot temperature history during annealing.",
)
@click.option(
    "--beam-width",
    "-b",
    envvar="THOTH_ADVISER_BEAM_WIDTH",
    type=int,
    default=AdaptiveSimulatedAnnealing.DEFAULT_BEAM_WIDTH,
    help="Width of the beam used.",
)
@click.option(
    "--limit-latest-versions",
    envvar="THOTH_ADVISER_LIMIT_LATEST_VERSIONS",
    type=int,
    default=AdaptiveSimulatedAnnealing.DEFAULT_LIMIT_LATEST_VERSIONS,
    help="Limit number of latest versions considered for dependency graphs.",
)
def advise(
    click_ctx: click.Context,
    *,
    beam_width: int,
    count: int,
    limit: int,
    output: str,
    recommendation_type: str,
    requirements_format: str,
    requirements: str,
    library_usage: Optional[str] = None,
    limit_latest_versions: Optional[int] = None,
    no_pretty: bool = False,
    plot_history: Optional[str] = None,
    requirements_locked: Optional[str] = None,
    runtime_environment: Optional[str] = None,
    seed: Optional[int] = None,
):
    """Advise package and package versions in the given stack or on solely package only."""
    parameters = locals()
    parameters.pop("click_ctx")

    if library_usage:
        if os.path.isfile(library_usage):
            try:
                library_usage = json.loads(Path(library_usage).read_text())
            except Exception as exc:
                _LOGGER.error("Failed to load library usage file %r", library_usage)
                raise
        else:
            library_usage = json.loads(library_usage)

    runtime_environment = RuntimeEnvironment.load(runtime_environment)
    recommendation_type = RecommendationType.by_name(recommendation_type)
    requirements_format = PythonRecommendationOutput.by_name(requirements_format)
    project = _instantiate_project(
        requirements, requirements_locked, runtime_environment
    )

    parameters["project"] = project.to_dict()
    parameters["runtime_environment"] = parameters["project"]["runtime_environment"]
    asa = partial(
        AdaptiveSimulatedAnnealing.compute_on_project,
        project=project,
        recommendation_type=recommendation_type,
        library_usage=library_usage,
        limit=limit,
        limit_latest_versions=limit_latest_versions,
        count=count,
        temperature_function=ASATemperatureFunction.exp,
        seed=seed,
        beam_width=beam_width,
    )

    print_func = _PrintFunc(
        partial(
            print_command_result,
            click_ctx=click_ctx,
            analyzer=analyzer_name,
            analyzer_version=analyzer_version,
            output=output,
            pretty=not no_pretty,
        )
    )

    exit_code = subprocess_run(
        asa,
        print_func,
        plot_history=plot_history,
        result_dict={"parameters": parameters},
    )

    click_ctx.exit(exit_code)


@cli.command("dependency-monkey")
@click.pass_context
@click.option(
    "--requirements",
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    metavar="REQUIREMENTS_FILE",
    required=True,
    help="Requirements to be advised.",
)
@click.option(
    "--requirements-format",
    "-f",
    envvar="THOTH_REQUIREMENTS_FORMAT",
    default="pipenv",
    required=True,
    type=click.Choice(["pipenv", "requirements"]),
    help="The output format of requirements that are computed based on recommendations.",
)
@click.option(
    "--stack-output",
    "-o",
    type=str,
    envvar="THOTH_DEPENDENCY_MONKEY_STACK_OUTPUT",
    metavar="OUTPUT",
    required=True,
    help="Output directory or remote API to print results to, in case of URL a POST request "
    "is issued to the Amun REST API.",
)
@click.option(
    "--library-usage",
    type=str,
    envvar="THOTH_ADVISER_LIBRARY_USAGE",
    help="Add library usage information to dependency-monkey resolution algorithm.",
)
@click.option(
    "--report-output",
    "-R",
    type=str,
    envvar="THOTH_DEPENDENCY_MONKEY_REPORT_OUTPUT",
    metavar="REPORT_OUTPUT",
    required=False,
    default="-",
    help="Output directory or remote API where reports of dependency monkey run should be posted..",
)
@click.option(
    "--seed",
    envvar="THOTH_DEPENDENCY_MONKEY_SEED",
    help="A seed to be used for generating software stack samples (defaults to time if omitted).",
)
@click.option(
    "--count",
    type=int,
    envvar="THOTH_DEPENDENCY_MONKEY_COUNT",
    default=AdaptiveSimulatedAnnealing.DEFAULT_COUNT,
    help="Number of software stacks that should be computed.",
)
@click.option(
    "--decision-type",
    required=False,
    envvar="THOTH_DEPENDENCY_MONKEY_DECISION_TYPE",
    default="ALL",
    type=click.Choice([e.name for e in DecisionType]),
    help="A decision type that should be used for generating software stack samples; "
    "if omitted, all software stacks will be created.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    envvar="THOTH_DEPENDENCY_MONKEY_DRY_RUN",
    help="Do not generate software stacks, just report how many software stacks will be "
    "generated given the provided configuration.",
)
@click.option(
    "--context",
    type=str,
    envvar="THOTH_AMUN_CONTEXT",
    metavar="AMUN_JSON",
    help="The context into which computed stacks should be placed; if omitteed, "
    "raw software stacks will be created. This option cannot be set when generating "
    "software stacks onto filesystem.",
)
@click.option(
    "--runtime-environment",
    "-e",
    envvar="THOTH_ADVISER_RUNTIME_ENVIRONMENT",
    metavar="ENV_JSON",
    type=str,
    help="Runtime environment specification (file or directly JSON) to describe target environment.",
)
@click.option(
    "--plot-history",
    envvar="THOTH_ADVISER_PLOT_HISTORY",
    type=str,
    help="Plot temperature history during annealing.",
)
@click.option(
    "--beam-width",
    "-b",
    envvar="THOTH_ADVISER_BEAM_WIDTH",
    type=int,
    default=AdaptiveSimulatedAnnealing.DEFAULT_BEAM_WIDTH,
    help="Width of the beam used.",
)
@click.option(
    "--limit-latest-versions",
    envvar="THOTH_ADVISER_LIMIT_LATEST_VERSIONS",
    type=int,
    default=AdaptiveSimulatedAnnealing.DEFAULT_LIMIT_LATEST_VERSIONS,
    help="Limit number of latest versions considered for dependency graphs.",
)
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
def dependency_monkey(
    click_ctx: click.Context,
    *,
    beam_width: int,
    count: int,
    decision_type: str,
    report_output: str,
    requirements: str,
    requirements_format: str,
    stack_output: str,
    context: Optional[str] = None,
    dry_run: bool = False,
    library_usage: Optional[str] = None,
    limit_latest_versions: Optional[int] = None,
    no_pretty: bool = False,
    plot_history: Optional[str] = None,
    runtime_environment: str = None,
    seed: Optional[int] = None,
):
    """Generate software stacks based on all valid resolutions that conform version ranges."""
    parameters = locals()
    parameters.pop("click_ctx")

    if library_usage:
        if os.path.isfile(library_usage):
            try:
                library_usage = json.loads(Path(library_usage).read_text())
            except Exception as exc:
                _LOGGER.error("Failed to load library usage file %r", library_usage)
                raise
        else:
            library_usage = json.loads(library_usage)

    runtime_environment = RuntimeEnvironment.load(runtime_environment)
    requirements_format = PythonRecommendationOutput.by_name(requirements_format)
    project = _instantiate_project(
        requirements, runtime_environment=runtime_environment
    )

    parameters["project"] = project.to_dict()

    graph = GraphDatabase()
    graph.connect()

    pipeline = PipelineBuilder.get_dependency_monkey_config(
        decision_type=decision_type,
        graph=graph,
        project=project,
        library_usage=library_usage,
    )

    asa = AdaptiveSimulatedAnnealing(
        pipeline=pipeline,
        project=project,
        library_usage=library_usage,
        limit_latest_versions=limit_latest_versions,
        count=count,
        temperature_function=ASATemperatureFunction.exp,
        seed=seed,
        beam_width=beam_width,
    )

    dependency_monkey_runner = DependencyMonkey(
        asa=asa,
        stack_output=stack_output,
        context=context,
        dry_run=dry_run,
        decision_type=decision_type,
    )

    print_func = _PrintFunc(
        partial(
            print_command_result,
            click_ctx=click_ctx,
            analyzer=analyzer_name,
            analyzer_version=analyzer_version,
            output=report_output,
            pretty=not no_pretty,
        )
    )

    exit_code = subprocess_run(
        partial(dependency_monkey_runner.anneal, with_devel=True),
        print_func,
        result_dict={"parameters": parameters},
        plot_history=plot_history,
    )

    click_ctx.exit(exit_code)


__name__ == "__main__" and cli()
