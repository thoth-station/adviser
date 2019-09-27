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

"""Thoth-adviser CLI."""

import os
import json
import sys
import logging
import time
import typing
import traceback
from pathlib import Path
from copy import deepcopy

import click
from thoth.adviser import __title__ as analyzer_name
from thoth.adviser import __version__ as analyzer_version
from thoth.adviser.enums import PythonRecommendationOutput
from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import DecisionType
from thoth.adviser.exceptions import InternalError
from thoth.adviser.exceptions import ThothAdviserException
from thoth.adviser.python.exceptions import UnableLock
from thoth.adviser.python import Adviser
from thoth.adviser.python import GraphDigestsFetcher
from thoth.adviser.python import dependency_monkey as run_dependency_monkey
from thoth.adviser.python.dependency_monkey import dm_amun_inspect_wrapper
from thoth.analyzer import print_command_result
from thoth.common import init_logging
from thoth.common import RuntimeEnvironment
from thoth.python import Pipfile
from thoth.python import PipfileLock
from thoth.python import Project
from thoth.solver.python.base import SolverException
from thoth.solver.python.base import NoReleasesFound

init_logging()

_LOGGER = logging.getLogger(__name__)


def _print_version(ctx, _, value):
    """Print adviser version and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(analyzer_version)
    ctx.exit()


def _instantiate_project(
    requirements: str,
    requirements_locked: typing.Optional[str],
    files: bool,
    runtime_environment: RuntimeEnvironment = None,
):
    """Create Project instance based on arguments passed to CLI."""
    if files:
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
@click.option(
    "--files",
    "-F",
    is_flag=True,
    help="Requirements passed represent paths to files on local filesystem.",
)
def provenance(
    click_ctx,
    requirements,
    requirements_locked=None,
    whitelisted_sources=None,
    output=None,
    files=False,
    no_pretty=False,
):
    """Check provenance of packages based on configuration."""
    start_time = time.monotonic()
    _LOGGER.debug("Passed arguments: %s", locals())

    whitelisted_sources = whitelisted_sources.split(",") if whitelisted_sources else []
    result = {
        "error": None,
        "report": [],
        "parameters": {"whitelisted_indexes": whitelisted_sources},
        "input": None,
    }
    try:
        project = _instantiate_project(requirements, requirements_locked, files)
        result["input"] = project.to_dict()
        report = project.check_provenance(
            whitelisted_sources=whitelisted_sources,
            digests_fetcher=GraphDigestsFetcher(),
        )
    except ThothAdviserException as exc:
        # TODO: we should extend exceptions so they are capable of storing more info.
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        _LOGGER.exception("Error during checking provenance: %s", str(exc))
        result["error"] = True
        result["report"] = [
            {"type": "ERROR", "justification": f"{str(exc)} ({type(exc).__name__})"}
        ]
    else:
        result["error"] = False
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
    return int(result["error"] is True)


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
)
@click.option(
    "--limit",
    type=int,
    envvar="THOTH_ADVISER_LIMIT",
    help="Number of software stacks that should be taken into account (stop after reaching the limit).",
)
@click.option(
    "--limit-latest-versions",
    type=int,
    envvar="THOTH_ADVISER_LIMIT_LATEST_VERSIONS",
    help="Consider only desired number of versions (latest) for a package to limit number of software stacks scored.",
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
    "--files",
    "-F",
    is_flag=True,
    help="Requirements passed represent paths to files on local filesystem.",
)
def advise(
    click_ctx,
    requirements,
    requirements_format=None,
    requirements_locked=None,
    recommendation_type=None,
    runtime_environment=None,
    output=None,
    no_pretty=False,
    files=False,
    count=None,
    limit=None,
    library_usage=None,
    limit_latest_versions=None,
):
    """Advise package and package versions in the given stack or on solely package only."""
    start_time = time.monotonic()
    _LOGGER.debug("Passed arguments: %s", locals())
    limit = int(limit) if limit else None
    count = int(count) if count else None

    # A special value of -1 signalizes no limit/count, this is a workaround for Click's option parser.
    if count == -1:
        count = None
    if limit == -1:
        limit = None
    if limit_latest_versions == -1:
        limit_latest_versions = None

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
    result = {
        "error": None,
        "report": [],
        "stack_info": None,
        "advised_configuration": None,
        "pipeline_configuration": None,
        "parameters": {
            "runtime_environment": runtime_environment.to_dict(),
            "recommendation_type": recommendation_type.name,
            "library_usage": library_usage,
            "requirements_format": requirements_format.name,
            "limit": limit,
            "limit_latest_versions": limit_latest_versions,
            "count": count,
            "no_pretty": no_pretty,
        },
        "input": None,
    }

    try:
        project = _instantiate_project(
            requirements, requirements_locked, files, runtime_environment
        )
        result["input"] = project.to_dict()
        if runtime_environment:
            _LOGGER.info(
                "Runtime environment configuration:\n%s",
                json.dumps(runtime_environment.to_dict(), sort_keys=True, indent=2),
            )
        else:
            _LOGGER.info("No runtime environment configuration supplied")
        if library_usage:
            _LOGGER.info(
                "Library usage:\n%s",
                json.dumps(library_usage, sort_keys=True, indent=2),
            )
        else:
            _LOGGER.info("No library usage supplied")
        stack_info, advised_configuration, report, pipeline_configuration = Adviser.compute_on_project(
            project,
            recommendation_type=recommendation_type,
            library_usage=library_usage,
            count=count,
            limit=limit,
            limit_latest_versions=limit_latest_versions,
        )
    except ThothAdviserException as exc:
        # TODO: we should extend exceptions so they are capable of storing more info.
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        _LOGGER.exception("Error during computing recommendation: %s", str(exc))
        result["error"] = True
        result["report"] = [([{"justification": f"{str(exc)}", "type": "ERROR"}], None)]
    except NoReleasesFound as exc:
        result["error"] = True
        result["report"] = [([{
            "justification": f"{str(exc)}; analysis of the missing package will be "
                             f"automatically scheduled by the system",
            "type": "ERROR"
        }], None)]
    except (SolverException, UnableLock) as exc:
        result["error"] = True
        result["report"] = [([{"justification": str(exc), "type": "ERROR"}], None)]
    else:
        # Convert report to a dict so its serialized.
        result["report"] = [
            (justification, project.to_dict(), overall_score)
            for justification, project, overall_score in report
        ]
        # Report error if we did not find any recommendation to the user, the
        # stack_info carries information on why it hasn't been found.
        result["error"] = len(result["report"]) == 0
        result["stack_info"] = stack_info
        if result["error"]:
            result["stack_info"].append({
                "type": "ERROR",
                "justification": "Recommendation engine did not produce any stacks"
            })
        result["advised_configuration"] = advised_configuration
        result["pipeline_configuration"] = pipeline_configuration
    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=output,
        duration=time.monotonic() - start_time,
        pretty=not no_pretty,
    )
    return int(result["error"] is True)


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
    "--limit-latest-versions",
    type=int,
    envvar="THOTH_ADVISER_LIMIT_LATEST_VERSIONS",
    metavar="INT",
    help="Consider only desired number of versions (latest) for "
    "a package to limit number of software stacks generated.",
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
    "--files",
    "-F",
    is_flag=True,
    help="Requirements passed represent paths to files on local filesystem.",
)
@click.option(
    "--seed",
    envvar="THOTH_DEPENDENCY_MONKEY_SEED",
    help="A seed to be used for generating software stack samples (defaults to time if omitted).",
)
@click.option(
    "--count",
    envvar="THOTH_DEPENDENCY_MONKEY_COUNT",
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
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
def dependency_monkey(
    click_ctx,
    requirements: str,
    stack_output: str,
    report_output: str,
    files: bool,
    seed: int = None,
    decision_type: str = None,
    dry_run: bool = False,
    context: str = None,
    no_pretty: bool = False,
    count: int = None,
    runtime_environment: dict = None,
    limit_latest_versions: int = None,
    library_usage: str = None,
):
    """Generate software stacks based on all valid resolutions that conform version ranges."""
    # We cannot have these as ints in click because they are optional and we
    # cannot pass empty string as an int as env variable.
    start_time = time.monotonic()
    seed = int(seed) if seed else None
    count = int(count) if count else None
    limit_latest_versions = (
        int(limit_latest_versions) if limit_latest_versions else None
    )

    # A special value of -1 signalizes no limit, this is a workaround for Click's option parser.
    if count == -1:
        count = None
    if limit_latest_versions == -1:
        limit_latest_versions = None

    runtime_environment = RuntimeEnvironment.load(runtime_environment)
    decision_type = DecisionType.by_name(decision_type)
    project = _instantiate_project(
        requirements,
        requirements_locked=None,
        files=files,
        runtime_environment=runtime_environment,
    )

    if library_usage:
        if os.path.isfile(library_usage):
            try:
                library_usage = json.loads(Path(library_usage).read_text())
            except Exception as exc:
                _LOGGER.error("Failed to load library usage file %r: %s", library_usage, str(exc))
                raise
        else:
            library_usage = json.loads(library_usage)

    if runtime_environment:
        _LOGGER.info(
            "Runtime environment configuration:\n%s",
            json.dumps(runtime_environment.to_dict(), sort_keys=True, indent=2),
        )
    else:
        _LOGGER.info("No runtime environment configuration supplied")
    if library_usage:
        _LOGGER.info(
            "Library usage:\n%s", json.dumps(library_usage, sort_keys=True, indent=2)
        )
    else:
        _LOGGER.info("No library usage supplied")

    result = {
        "error": None,
        "parameters": {
            "requirements": project.pipfile.to_dict(),
            "runtime_environment": runtime_environment.to_dict(),
            "seed": seed,
            "decision_type": decision_type.name,
            "library_usage": library_usage,
            "context": deepcopy(
                context
            ),  # We reuse context later, perform deepcopy to report the one on input.
            "stack_output": stack_output,
            "report_output": report_output,
            "files": files,
            "dry_run": dry_run,
            "no_pretty": no_pretty,
            "count": count,
        },
        "input": None,
        "output": [],
        "computed": None,
    }

    try:
        report = run_dependency_monkey(
            project,
            stack_output,
            seed=seed,
            decision_type=decision_type,
            dry_run=dry_run,
            context=context,
            count=count,
            limit_latest_versions=limit_latest_versions,
            library_usage=library_usage,
        )
        # Place report into result.
        result.update(report)
    except SolverException:
        _LOGGER.exception("An error occurred during dependency monkey run")
        result["error"] = traceback.format_exc()
    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=report_output,
        duration=time.monotonic() - start_time,
        pretty=not no_pretty,
    )

    return sys.exit(result["error"] is not None)


@cli.command("submit-amun")
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
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    required=True,
    help="Requirements to be advised.",
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
    "--files",
    "-F",
    is_flag=True,
    help="Requirements passed represent paths to files on local filesystem.",
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
def submit_amun(
    requirements: str,
    requirements_locked: str,
    stack_output: str,
    files: bool,
    context: str = None,
):
    """Submit the given project to Amun for inspection - mostly for debug purposes."""
    project = _instantiate_project(
        requirements, requirements_locked=requirements_locked, files=files
    )
    context = json.loads(context) if context else {}
    inspection_id = dm_amun_inspect_wrapper(stack_output, context, project, 0)
    click.echo(inspection_id)


if __name__ == "__main__":
    cli()
