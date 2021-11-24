#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 - 2021 Fridolin Pokorny
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
import pickle
import random
import sys
import time
from functools import partial
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple

import attr
import click
import yaml
import termial_random
from thoth.analyzer import print_command_result
from thoth.common import init_logging
from thoth.common import RuntimeEnvironment
from thoth.python import Constraints
from thoth.python import Pipfile
from thoth.python import PipfileLock
from thoth.python import Project
from thoth.python.exceptions import UnsupportedConfigurationError
from prometheus_client import CollectorRegistry
from prometheus_client import Gauge
from prometheus_client import push_to_gateway

from thoth.adviser.dependency_monkey import DependencyMonkey
from thoth.adviser.digests_fetcher import GraphDigestsFetcher
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import PythonRecommendationOutput
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import AdviserException
from thoth.adviser.exceptions import InternalError
from thoth.adviser.pipeline_builder import PipelineBuilder
from thoth.adviser.prescription import Prescription
from thoth.adviser import Resolver
from thoth.adviser import __title__ as analyzer_name
from thoth.adviser import __version__ as analyzer_version
from thoth.adviser.run import subprocess_run
import thoth.adviser.predictors as predictors

init_logging()

_LOGGER = logging.getLogger("thoth.adviser")


prometheus_registry = CollectorRegistry()

_THOTH_DEPLOYMENT_NAME = os.getenv("THOTH_DEPLOYMENT_NAME")
_THOTH_METRICS_PUSHGATEWAY_URL = os.getenv("PROMETHEUS_PUSHGATEWAY_URL")
_DEFAULT_PLATFORM = "linux-x86_64"


_METRIC_INFO = Gauge(
    "thoth_adviser_info",
    "Thoth adviser information",
    ["env", "version"],
    registry=prometheus_registry,
)


_METRIC_DATABASE_SCHEMA_SCRIPT = Gauge(
    "thoth_database_schema_revision_script",
    "Thoth database schema revision from script",
    ["component", "revision", "env"],
    registry=prometheus_registry,
)


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
    *,
    runtime_environment: RuntimeEnvironment = None,
    constraints: Optional[str] = None,
):
    """Create Project instance based on arguments passed to CLI."""
    try:
        with open(requirements, "r") as requirements_file:
            requirements = requirements_file.read()
    except (OSError, FileNotFoundError):
        # We we gather values from env vars, un-escape new lines.
        requirements = requirements.replace("\\n", "\n")

    if requirements_locked:
        try:
            with open(requirements_locked, "r") as requirements_file:
                requirements_locked = requirements_file.read()
        except (OSError, FileNotFoundError):
            # We we gather values from env vars, un-escape new lines.
            requirements_locked = requirements_locked.replace("\\n", "\n")

    pipfile = Pipfile.from_string(requirements)
    pipfile_lock = None
    if requirements_locked and requirements_locked != "null":
        pipfile_lock = PipfileLock.from_string(requirements_locked, pipfile)

    constraints_instance = None
    if constraints:
        try:
            with open(constraints, "r") as constraints_file:
                constraints_content = constraints_file.read()
        except (OSError, FileNotFoundError):
            # We we gather values from env vars, un-escape new lines.
            constraints_content = constraints.replace("\\n", "\n")

        try:
            constraints_instance = Constraints.from_dict(json.loads(constraints_content))
        except json.decoder.JSONDecodeError:
            constraints_instance = Constraints.from_string(constraints_content)

    runtime_environment = runtime_environment or RuntimeEnvironment.from_dict({})
    if not runtime_environment.platform:
        runtime_environment.platform = _DEFAULT_PLATFORM

    project = Project(
        pipfile=pipfile,
        pipfile_lock=pipfile_lock,
        runtime_environment=runtime_environment,
        constraints=constraints_instance or Constraints(),
    )

    return project


def _get_adviser_predictor(predictor: str, recommendation_type: RecommendationType) -> Tuple[type, Dict[str, Any]]:
    """Get adviser predictor based on command line option."""
    if predictor != "AUTO":
        return getattr(predictors, predictor), {}

    if recommendation_type == RecommendationType.LATEST:
        return predictors.ApproximatingLatest, {}
    elif (
        recommendation_type == RecommendationType.STABLE
        or recommendation_type == RecommendationType.TESTING
        or recommendation_type == RecommendationType.PERFORMANCE
        or recommendation_type == RecommendationType.SECURITY
    ):
        return (
            predictors.TemporalDifference,
            {
                "step": 1,
                "temperature_coefficient": predictors.TemporalDifference.obtain_default_configuration(
                    "temperature_coefficient"
                ),
                "trace": False,
            },
        )

    raise ValueError(f"Unknown recommendation type: {recommendation_type!r}")


def _get_dependency_monkey_predictor(predictor: str, decision_type: DecisionType) -> type:
    """Get dependency monkey predictor based on command line option."""
    if predictor != "AUTO":
        return getattr(predictors, predictor)

    if decision_type == DecisionType.RANDOM:
        return predictors.RandomWalk
    elif decision_type == DecisionType.ALL:
        return predictors.ApproximatingLatest

    raise ValueError(f"Unknown decision type: {decision_type!r}")


def _get_predictor_kwargs(predictor_config: Optional[str]) -> Dict[str, Any]:
    """Get kwargs for a predictor instance."""
    if predictor_config is None:
        return {}

    if os.path.isfile(predictor_config):
        with open(predictor_config, "r") as predictor_config_file:
            return yaml.safe_load(predictor_config_file)

    return yaml.safe_load(predictor_config)


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
        "parameters": {"whitelisted_indexes": whitelisted_sources, "project": None},
        "input": None,
    }
    try:
        project = _instantiate_project(requirements, requirements_locked)
        result["parameters"]["project"] = project.to_dict()
        report = project.check_provenance(
            whitelisted_sources=whitelisted_sources,
            digests_fetcher=GraphDigestsFetcher(),
        )
    except (AdviserException, UnsupportedConfigurationError) as exc:
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        _LOGGER.exception("Error during checking provenance: %s", str(exc))
        result["error"] = True
        result["error_msg"] = str(exc)
        result["report"] = [{"type": "ERROR", "justification": f"{str(exc)} ({type(exc).__name__})"}]
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
    default="stable",
    required=True,
    type=click.Choice([e.name.lower() for e in RecommendationType]),
    help="Type of recommendation generated based on knowledge base.",
)
@click.option(
    "--count",
    type=int,
    envvar="THOTH_ADVISER_COUNT",
    help="Number of software stacks shown in the output.",
    default=Resolver.DEFAULT_COUNT,
    show_default=True,
)
@click.option(
    "--limit",
    type=int,
    envvar="THOTH_ADVISER_LIMIT",
    help="Number of software stacks that should be taken into account (stop after reaching the limit).",
    default=Resolver.DEFAULT_LIMIT,
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
@click.option("--plot", envvar="THOTH_ADVISER_PLOT", type=str, help="Plot history of predictor.")
@click.option(
    "--beam-width",
    "-b",
    envvar="THOTH_ADVISER_BEAM_WIDTH",
    type=int,
    default=Resolver.DEFAULT_BEAM_WIDTH,
    help="Width of the beam used.",
)
@click.option(
    "--limit-latest-versions",
    envvar="THOTH_ADVISER_LIMIT_LATEST_VERSIONS",
    type=int,
    default=Resolver.DEFAULT_LIMIT_LATEST_VERSIONS,
    help="Limit number of latest versions considered for dependency graphs.",
)
@click.option(
    "--predictor",
    envvar="THOTH_ADVISER_PREDICTOR",
    default="AUTO",
    type=click.Choice(predictors.__all__ + ["AUTO"]),
    help="Predictor to be used with the resolver, select the most appropriate one in case of AUTO.",
)
@click.option(
    "--predictor-config",
    envvar="THOTH_ADVISER_PREDICTOR_CONFIG",
    default=None,
    type=str,
    metavar="CONFIG",
    help="Predictor configuration - passed as a path to YAML file or as a YAML string.",
)
@click.option(
    "--pipeline",
    envvar="THOTH_ADVISER_PIPELINE",
    default=None,
    type=str,
    metavar="PIPELINE",
    help="Pipeline configuration supplied in a form of JSON/YAML or a path to a file, "
    "disjoint with pipeline prescription.",
)
@click.option(
    "--prescription",
    envvar="THOTH_ADVISER_PRESCRIPTION",
    default=None,
    type=str,
    multiple=True,
    metavar="PRESCRIPTION",
    help="Pipeline prescription supplied in a form of JSON/YAML or a path to a file, "
    "disjoint with pipeline configuration. Multiple files can be supplied by using `,' as a delimiter.",
)
@click.option(
    "--constraints",
    envvar="THOTH_ADVISER_CONSTRAINTS",
    default=None,
    type=str,
    metavar="CONSTRAINTS.txt",
    help="Constraints to be used during the resolution.",
)
@click.option(
    "--labels",
    "-l",
    envvar="THOTH_ADVISER_LABELS",
    type=str,
    metavar='{"key1": "val1", "key2": "val2"}',
    default=None,
    show_default=True,
    help="Labels used used to label the request.",
)
@click.option(
    "--user-stack-scoring/--no-user-stack-scoring",
    envvar="THOTH_ADVISER_USER_STACK_SCORING",
    is_flag=True,
    default=True,
    show_default=True,
    help="Turn off or on user stack scoring - the lock file supplied, if any, will be used "
    "as a base for relative stack quality comparision. Adviser will score the supplied "
    "lock file and will try to find a better stack.",
)
@click.option(
    "--dev/--no-dev",
    envvar="THOTH_ADVISER_DEV",
    is_flag=True,
    default=False,
    show_default=True,
    help="Consider or do not consider development dependencies during resolution.",
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
    predictor: str,
    predictor_config: Optional[str] = None,
    library_usage: Optional[str] = None,
    limit_latest_versions: Optional[int] = None,
    no_pretty: bool = False,
    plot: Optional[str] = None,
    requirements_locked: Optional[str] = None,
    runtime_environment: Optional[str] = None,
    seed: Optional[int] = None,
    pipeline: Optional[str] = None,
    prescription: Optional[str] = None,
    constraints: Optional[str] = None,
    user_stack_scoring: bool = True,
    dev: bool = False,
    labels: Optional[str] = None,
):
    """Advise package and package versions in the given stack or on solely package only."""
    parameters = locals()
    parameters.pop("click_ctx")

    if pipeline and prescription:
        sys.exit("Options --pipeline/--prescription are disjoint")

    if library_usage:
        if os.path.isfile(library_usage):
            try:
                with open(library_usage, "r") as f:
                    library_usage = json.load(f)
            except Exception:
                _LOGGER.error("Failed to load library usage file %r", library_usage)
                raise
        else:
            library_usage = json.loads(library_usage)

        # Show library usage in the final report.
        parameters["library_usage"] = library_usage

    labels_dict = {}
    if labels:
        if os.path.isfile(labels):
            try:
                with open(labels, "r") as f:
                    labels_dict = json.load(f)
            except Exception:
                _LOGGER.error("Failed to load labels file %r", labels)
                raise
        else:
            labels_dict = json.loads(labels)

        # Show labels in the final report.
        parameters["labels"] = labels_dict

    runtime_environment = RuntimeEnvironment.load(runtime_environment)
    recommendation_type = RecommendationType.by_name(recommendation_type)
    _LOGGER.info("Using recommendation type %s", recommendation_type.name.lower())

    requirements_format = PythonRecommendationOutput.by_name(requirements_format)
    project = _instantiate_project(
        requirements, requirements_locked, runtime_environment=runtime_environment, constraints=constraints
    )

    pipeline_config = None
    if pipeline:
        pipeline_config = PipelineBuilder.load(pipeline)

    parameters["project"] = project.to_dict()
    if pipeline_config is not None:
        parameters["pipeline"] = pipeline_config.to_dict()

    prescription_instance = None
    if prescription:
        if len(prescription) == 1:
            # Click does not support multiple parameters when supplied via env vars. Perform split on delimiter.
            prescription_instance = Prescription.load(*prescription[0].split(","))
        else:
            prescription_instance = Prescription.load(*prescription)

    predictor_class, predictor_kwargs = _get_adviser_predictor(predictor, recommendation_type)
    predictor_kwargs = _get_predictor_kwargs(predictor_config) or predictor_kwargs
    predictor_instance = predictor_class(**predictor_kwargs, keep_history=plot is not None)

    # Use current time to make sure we have possibly reproducible runs - the seed is reported.
    seed = seed if seed is not None else int(time.time())
    _LOGGER.info(
        "Starting resolver using %r predictor with random seed set to %r, predictor parameters: %r",
        predictor_class.__name__,
        seed,
        predictor_kwargs,
    )
    random.seed(seed)
    termial_random.seed(seed)

    resolver = Resolver.get_adviser_instance(
        predictor=predictor_instance,
        project=project,
        labels=labels_dict,
        library_usage=library_usage,
        recommendation_type=recommendation_type,
        limit=limit,
        count=count,
        beam_width=beam_width,
        limit_latest_versions=limit_latest_versions,
        pipeline_config=pipeline_config,
        prescription=prescription_instance,
        cli_parameters=parameters,
    )

    del prescription  # No longer needed, garbage collect it.

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
        resolver,
        print_func,
        plot=plot,
        result_dict={"parameters": parameters},
        with_devel=dev,
        user_stack_scoring=user_stack_scoring,
        verbose=click_ctx.parent.params.get("verbose", False),
    )

    # Push metrics.
    if _THOTH_METRICS_PUSHGATEWAY_URL:
        _METRIC_INFO.labels(_THOTH_DEPLOYMENT_NAME, analyzer_version).inc()
        _METRIC_DATABASE_SCHEMA_SCRIPT.labels(
            analyzer_name, resolver.graph.get_script_alembic_version_head(), _THOTH_DEPLOYMENT_NAME
        ).inc()

        try:
            _LOGGER.debug("Submitting metrics to Prometheus pushgateway %s", _THOTH_METRICS_PUSHGATEWAY_URL)
            push_to_gateway(_THOTH_METRICS_PUSHGATEWAY_URL, job="adviser", registry=prometheus_registry)
        except Exception:
            _LOGGER.exception("An error occurred when pushing metrics")

    click_ctx.exit(int(exit_code != 0))


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
    type=int,
)
@click.option(
    "--count",
    type=int,
    envvar="THOTH_DEPENDENCY_MONKEY_COUNT",
    default=Resolver.DEFAULT_COUNT,
    help="Number of software stacks that should be computed.",
)
@click.option(
    "--decision-type",
    required=False,
    envvar="THOTH_DEPENDENCY_MONKEY_DECISION_TYPE",
    default="all",
    type=click.Choice([e.name.lower() for e in DecisionType]),
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
    help="The context into which computed stacks should be placed (either a file or"
    "a JSON); if omitted, raw software stacks will be created. This option cannot be set when generating "
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
@click.option("--plot", envvar="THOTH_ADVISER_PLOT", type=str, help="Plot predictor history.")
@click.option(
    "--beam-width",
    "-b",
    envvar="THOTH_ADVISER_BEAM_WIDTH",
    type=int,
    default=Resolver.DEFAULT_BEAM_WIDTH,
    help="Width of the beam used.",
)
@click.option(
    "--limit-latest-versions",
    envvar="THOTH_ADVISER_LIMIT_LATEST_VERSIONS",
    type=int,
    default=Resolver.DEFAULT_LIMIT_LATEST_VERSIONS,
    help="Limit number of latest versions considered for dependency graphs.",
)
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
@click.option(
    "--predictor",
    envvar="THOTH_ADVISER_PREDICTOR",
    default="AUTO",
    type=click.Choice(predictors.__all__ + ["AUTO"]),
    help="Predictor to be used with the resolver.",
)
@click.option(
    "--predictor-config",
    envvar="THOTH_ADVISER_PREDICTOR_CONFIG",
    default=None,
    type=str,
    metavar="CONFIG",
    help="Predictor configuration - passed as a path to YAML file or as a YAML string.",
)
@click.option(
    "--pipeline",
    envvar="THOTH_ADVISER_PIPELINE",
    default=None,
    type=str,
    metavar="PIPELINE",
    help="Pipeline configuration supplied in a form of JSON/YAML or a path to a file, "
    "disjoint with pipeline prescription. Multiple files can be supplied by using `,' as a delimiter.",
)
@click.option(
    "--prescription",
    envvar="THOTH_ADVISER_PRESCRIPTION",
    default=None,
    type=str,
    metavar="PRESCRIPTION",
    help="Pipeline prescription supplied in a form of JSON/YAML or a path to a file, "
    "disjoint with pipeline configuration.",
)
@click.option(
    "--dev/--no-dev",
    envvar="THOTH_ADVISER_DEV",
    is_flag=True,
    default=False,
    show_default=True,
    help="Consider or do not consider development dependencies during resolution.",
)
def dependency_monkey(
    click_ctx: click.Context,
    *,
    beam_width: int,
    count: int,
    decision_type: str,
    predictor: str,
    report_output: str,
    requirements: str,
    requirements_format: str,
    stack_output: str,
    predictor_config: Optional[str] = None,
    context: Optional[str] = None,
    dry_run: bool = False,
    library_usage: Optional[str] = None,
    limit_latest_versions: Optional[int] = None,
    no_pretty: bool = False,
    plot: Optional[str] = None,
    runtime_environment: str = None,
    seed: Optional[int] = None,
    pipeline: Optional[str] = None,
    prescription: Optional[str] = None,
    dev: bool = False,
):
    """Generate software stacks based on all valid resolutions that conform version ranges."""
    parameters = locals()
    parameters.pop("click_ctx")

    if pipeline and prescription:
        sys.exit("Options --pipeline/--prescription are disjoint")

    if library_usage:
        if os.path.isfile(library_usage):
            try:
                with open(library_usage, "r") as f:
                    library_usage = json.load(f)
            except Exception:
                _LOGGER.error("Failed to load library usage file %r", library_usage)
                raise
        else:
            library_usage = json.loads(library_usage)

        # Show library usage in the final report.
        parameters["library_usage"] = library_usage

    runtime_environment = RuntimeEnvironment.load(runtime_environment)
    parameters["runtime_environment"] = runtime_environment.to_dict()

    decision_type = DecisionType.by_name(decision_type)
    requirements_format = PythonRecommendationOutput.by_name(requirements_format)
    project = _instantiate_project(requirements, runtime_environment=runtime_environment)
    parameters["requirements"] = project.pipfile.to_dict()
    parameters["project"] = project.to_dict()

    pipeline_config = None if pipeline is None else PipelineBuilder.load(pipeline)
    if pipeline_config is not None:
        parameters["pipeline"] = pipeline_config.to_dict()

    prescription_instance = None
    if prescription:
        if len(prescription) == 1:
            # Click does not support multiple parameters when supplied via env vars. Perform split on delimiter.
            prescription_instance = Prescription.load(*prescription[0].split(","))
        else:
            prescription_instance = Prescription.load(*prescription)

    # Use current time to make sure we have possibly reproducible runs - the seed is reported.
    seed = seed if seed is not None else int(time.time())
    predictor_class = _get_dependency_monkey_predictor(predictor, decision_type)
    predictor_kwargs = _get_predictor_kwargs(predictor_config)
    predictor_instance = predictor_class(**predictor_kwargs, keep_history=plot is not None)
    _LOGGER.info(
        "Starting resolver using predictor %r with random seed set to %r, predictor parameters: %r",
        predictor_class.__name__,
        seed,
        predictor_kwargs,
    )
    random.seed(seed)
    termial_random.seed(seed)

    resolver = Resolver.get_dependency_monkey_instance(
        predictor=predictor_instance,
        project=project,
        library_usage=library_usage,
        count=count,
        beam_width=beam_width,
        limit_latest_versions=limit_latest_versions,
        decision_type=decision_type,
        pipeline_config=pipeline_config,
        prescription=prescription_instance,
        cli_parameters=parameters,
    )

    del prescription  # No longer needed, garbage collect it.

    context_content = {}
    try:
        with open(context) as f:
            context_content = json.load(f)
    except (FileNotFoundError, IOError):
        # IOError raised if context is too large to be handled with open.
        context_content = json.loads(context)
    parameters["context"] = context_content

    dependency_monkey_runner = DependencyMonkey(
        resolver=resolver,
        stack_output=stack_output,
        context=context_content,
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
        dependency_monkey_runner,
        print_func,
        result_dict={"parameters": parameters},
        plot=plot,
        with_devel=dev,
        user_stack_scoring=False,
        # Keep verbose output (stating pipeline units run) in dependency-monkey.
        verbose=True,
    )

    click_ctx.exit(int(exit_code != 0))


@cli.command("validate-prescriptions")
@click.argument("prescriptions", nargs=1, metavar="PRESCRIPTION_DIR")
@click.option(
    "--show-unit-names",
    envvar="THOTH_ADVISER_VALIDATE_PRESCRIPTION_SHOW_UNIT_NAMES",
    is_flag=True,
    default=False,
    show_default=True,
    help="Show names of prescriptions that were validated.",
)
@click.option(
    "--output",
    envvar="THOTH_ADVISER_VALIDATE_PRESCRIPTION_OUTPUT",
    type=str,
    metavar="PRESCRIPTIONS.pickle",
    required=False,
    help="Serialize validated prescriptions into an output pickle file.",
)
def validate_prescription(prescriptions: str, show_unit_names: bool, output: str) -> None:
    """Validate the given prescription."""
    _LOGGER.info("Validating prescriptions in %r", prescriptions)
    prescription = Prescription.validate(prescriptions)
    _LOGGER.info("Prescriptions %r validated successfully", prescriptions)

    result = {
        "prescriptions": [{"name": p[0], "release": p[1]} for p in prescription.prescriptions],
        "count": {
            "boots_count": sum(1 for _ in prescription.iter_boot_units()),
            "pseudonyms_count": sum(1 for _ in prescription.iter_pseudonym_units()),
            "sieves_count": sum(1 for _ in prescription.iter_sieve_units()),
            "steps_count": sum(1 for _ in prescription.iter_step_units()),
            "strides_count": sum(1 for _ in prescription.iter_stride_units()),
            "wraps_count": sum(1 for _ in prescription.iter_wrap_units()),
        },
        "count_all": sum(1 for _ in prescription.units),
    }

    if show_unit_names:
        result["boots"] = sorted(prescription.boots_dict.keys())
        result["pseudonyms"] = sorted(prescription.pseudonyms_dict.keys())
        result["sieves"] = sorted(prescription.sieves_dict.keys())
        result["steps"] = sorted(prescription.steps_dict.keys())
        result["strides"] = sorted(prescription.strides_dict.keys())
        result["wraps"] = sorted(prescription.wraps_dict.keys())

    yaml.safe_dump(result, sys.stdout)

    if output:
        _LOGGER.info("Writing validated prescriptions to %r", output)
        with open(output, "wb") as fp:
            pickle.dump(prescription, fp)


__name__ == "__main__" and cli()
