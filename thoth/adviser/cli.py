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

"""Thoth-adviser CLI."""

import os
import random
import logging
import json
import sys
from functools import partial

from amun import inspect as amun_inspect
import click
from thoth.analyzer import print_command_result
from thoth.common import init_logging

from thoth.adviser.enums import PythonRecommendationOutput
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import ThothAdviserException
from thoth.adviser.exceptions import InternalError
from thoth.adviser import __title__ as analyzer_name
from thoth.adviser import __version__ as analyzer_version
from thoth.adviser.python import Pipfile, PipfileLock
from thoth.adviser.python import Project
from thoth.adviser.python import DependencyGraph
from thoth.solver.solvers.base import SolverException

init_logging()

_LOGGER = logging.getLogger(__name__)


def _print_version(ctx, _, value):
    """Print adviser version and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(analyzer_version)
    ctx.exit()


def _instantiate_project(requirements: str, requirements_locked: str, files: bool):
    """Create Project instance based on arguments passed to CLI."""
    if files:
        with open(requirements, 'r') as requirements_file:
            requirements = requirements_file.read()

        if requirements_locked:
            with open(requirements_locked, 'r') as requirements_file:
                requirements_locked = requirements_file.read()
            del requirements_file
    else:
        # We we gather values from env vars, un-escape new lines.
        requirements = requirements.replace('\\n', '\n')
        if requirements_locked:
            requirements_locked = requirements_locked.replace('\\n', '\n')

    pipfile = Pipfile.from_string(requirements)
    pipfile_lock = PipfileLock.from_string(requirements_locked, pipfile) if requirements_locked else None
    project = Project(
        pipfile=pipfile,
        pipfile_lock=pipfile_lock
    )

    return project


def _dm_amun_inspect_wrapper(output: str, context: dict, generated_project: Project, count: int):
    """A wrapper around Amun inspection call."""
    context['python'] = generated_project.to_dict()
    response = amun_inspect(output, context)
    _LOGGER.info("Submitted Amun inspection #%d: %r", count, response)
    return response['inspection_id']


def _dm_amun_directory_output(output: str, generated_project: Project, count: int):
    """A wrapper for placing generated software stacks onto filesystem."""
    _LOGGER.debug("Writing stack %d", count)

    path = os.path.join(output, f'{count:05d}')
    os.makedirs(path, exist_ok=True)
    pipfile_path = os.path.join(path, 'Pipfile')
    pipfile_lock_path = os.path.join(path, 'Pipfile.lock')

    generated_project.to_files(pipfile_path, pipfile_lock_path)
    return path


def _dm_stdout_output(generated_project: Project, count: int):
    """A function called if the project should be printed to stdout as a dict."""
    json.dump(generated_project.to_dict(), fp=sys.stdout, sort_keys=True, indent=2)
    return None


@click.group()
@click.pass_context
@click.option('-v', '--verbose', is_flag=True, envvar='THOTH_ADVISER_DEBUG',
              help="Be verbose about what's going on.")
@click.option('--version', is_flag=True, is_eager=True, callback=_print_version, expose_value=False,
              help="Print adviser version and exit.")
def cli(ctx=None, verbose=False):
    """Thoth adviser command line interface."""
    if ctx:
        ctx.auto_envvar_prefix = 'THOTH_ADVISER'

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    _LOGGER.debug("Debug mode is on")


@cli.command()
@click.pass_context
@click.option('--requirements', '-r', type=str, envvar='THOTH_ADVISER_REQUIREMENTS', required=True,
              help="Pipfile to be checked for provenance.")
@click.option('--requirements-locked', '-l', type=str, envvar='THOTH_ADVISER_REQUIREMENTS_LOCKED', required=True,
              help="Pipenv.lock file stating currently locked packages.")
@click.option('--output', '-o', type=str, envvar='THOTH_ADVISER_OUTPUT', default='-',
              help="Output file or remote API to print results to, in case of URL a POST request is issued.")
@click.option('--no-pretty', '-P', is_flag=True,
              help="Do not print results nicely.")
@click.option('--whitelisted-sources', '-i', type=str, required=False, envvar='THOTH_WHITELISTED_SOURCES',
              help="A comma separated list of whitelisted simple repositories providing packages - if not "
                   "provided, all indexes are whitelisted (example: https://pypi.org/simple/).")
@click.option('--files', '-F', is_flag=True,
              help="Requirements passed represent paths to files on local filesystem.")
def provenance(click_ctx, requirements, requirements_locked=None, whitelisted_sources=None, output=None,
               files=False, no_pretty=False):
    """Check provenance of packages based on configuration."""
    _LOGGER.debug("Passed arguments: %s", locals())

    whitelisted_sources = whitelisted_sources.split(',') if whitelisted_sources else []
    result = {
        'error': None,
        'report': [],
        'parameters': {
            'whitelisted_indexes': whitelisted_sources,
        },
        'input': None
    }
    try:
        project = _instantiate_project(requirements, requirements_locked, files)
        result['input'] = project.to_dict()
        report = project.check_provenance(whitelisted_sources=whitelisted_sources)
    except ThothAdviserException as exc:
        # TODO: we should extend exceptions so they are capable of storing more info.
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        _LOGGER.exception("Error during checking provenance: %s", str(exc))
        result['error'] = True
        result['report'] = [{
            'type': 'ERROR',
            'justification': f'{str(exc)} ({type(exc).__name__})'
        }]
    else:
        result['error'] = False
        result['report'] = report

    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=output,
        pretty=not no_pretty
    )
    return int(result['error'] is True)


@cli.command()
@click.pass_context
@click.option('--requirements', '-r', type=str, envvar='THOTH_ADVISER_REQUIREMENTS', required=True,
              help="Requirements to be advised.")
@click.option('--requirements-locked', '-l', type=str, envvar='THOTH_ADVISER_REQUIREMENTS_LOCKED',
              help="Currently locked down requirements used.")
@click.option('--requirements-format', '-f', envvar='THOTH_REQUIREMENTS_FORMAT', default='pipenv', required=True,
              type=click.Choice(['pipenv', 'requirements']),
              help="The output format of requirements that are computed based on recommendations.")
@click.option('--output', '-o', type=str, envvar='THOTH_ADVISER_OUTPUT', default='-',
              help="Output file or remote API to print results to, in case of URL a POST request is issued.")
@click.option('--no-pretty', '-P', is_flag=True,
              help="Do not print results nicely.")
@click.option('--recommendation-type', '-t', envvar='THOTH_ADVISER_RECOMMENDATION_TYPE', default='stable',
              required=True,
              type=click.Choice(['stable', 'testing', 'latest']),
              help="Type of recommendation generated based on knowledge base.")
@click.option('--runtime-environment', '-e', envvar='THOTH_ADVISER_RUNTIME_ENVIRONMENT', type=str,
              help="Type of recommendation generated based on knowledge base.")
@click.option('--files', '-F', is_flag=True,
              help="Requirements passed represent paths to files on local filesystem.")
def advise(click_ctx, requirements, requirements_format=None, requirements_locked=None,
           recommendation_type=None, runtime_environment=None, output=None, no_pretty=False, files=False):
    """Advise package and package versions in the given stack or on solely package only."""
    _LOGGER.debug("Passed arguments: %s", locals())

    recommendation_type = RecommendationType.by_name(recommendation_type)
    requirements_format = PythonRecommendationOutput.by_name(requirements_format)
    result = {
        'error': None,
        'report': [],
        'parameters': {
            'runtime_environment': runtime_environment,
            'recommendation_type': recommendation_type.name.lower(),
            'requirements_format': requirements_format.name.lower()
        },
        'input': None,
        'output': {
            'requirements': None,
            'requirements_locked': None
        }
    }
    try:
        project = _instantiate_project(requirements, requirements_locked, files)
        result['input'] = project.to_dict()
        report = project.advise(runtime_environment, recommendation_type)
    except ThothAdviserException as exc:
        # TODO: we should extend exceptions so they are capable of storing more info.
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        _LOGGER.exception("Error during computing recommendation: %s", str(exc))
        result['error'] = True
        result['report'] = [{
            'justification': f'{str(exc)} ({type(exc).__name__})',
            'type': 'ERROR',
        }]
    else:
        result['error'] = False
        if report:
            # If we have something to suggest, add it to output field.
            # Do not replicate input to output without any reason.
            if requirements_format == PythonRecommendationOutput.PIPENV:
                output_requirements = project.pipfile.to_dict()
                output_requirements_locked = project.pipfile_lock.to_dict()
            else:
                output_requirements = project.pipfile.to_requirements_file()
                output_requirements_locked = project.pipfile_lock.to_requirements_file()

            result['report'] = report
            result['output']['requirements'] = output_requirements
            result['output']['requirements_locked'] = output_requirements_locked

    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=output,
        pretty=not no_pretty
    )
    return int(result['error'] is True)


@cli.command('dependency-monkey')
@click.pass_context
@click.option('--requirements', '-r', type=str, envvar='THOTH_ADVISER_REQUIREMENTS', required=True,
              help="Requirements to be advised.")
@click.option('--stack-output', '-o', type=str, envvar='THOTH_DEPENDENCY_MONKEY_STACK_OUTPUT', required=True,
              help="Output directory or remote API to print results to, in case of URL a POST request "
                   "is issued to the Amun REST API.")
@click.option('--report-output', '-R', type=str, envvar='THOTH_DEPENDENCY_MONKEY_REPORT_OUTPUT',
              required=False, default='-',
              help="Output directory or remote API where reports of dependency monkey run should be posted..")
@click.option('--files', '-F', is_flag=True,
              help="Requirements passed represent paths to files on local filesystem.")
@click.option('--seed', type=int, envvar='THOTH_DEPENCENCY_MONKEY_SEED',
              help="A seed to be used for generating software stack samples (defaults to time if omitted).")
@click.option('--decision', required=False, envvar='THOTH_DEPENDENCY_MONKEY_DECISION',
              type=click.Choice(['uniform-distribution']),
              help="A decision function that should be used for generating software stack samples; "
                   "if omitted, all software stacks will be created.")
@click.option('--dry-run', is_flag=True, envvar='THOTH_DEPENDENCY_MONKEY_DRY_RUN',
              help="Do not generate software stacks, just report how many software stacks will be "
                   "generated given the provided configuration.")
@click.option('--context', type=str, envvar='THOTH_AMUN_CONTEXT',
              help="The context into which computed stacks should be placed; if omitteed, "
                   "raw software stacks will be created. This option cannot be set when generating "
                   "software stacks onto filesystem.")
@click.option('--no-pretty', '-P', is_flag=True,
              help="Do not print results nicely.")
def dependency_monkey(click_ctx, requirements: str, stack_output: str, report_output: str, files: bool,
                      seed: int = None, decision: str = None, dry_run: bool = False,
                      context: str = None, no_pretty: bool = False):
    """Generate software stacks based on all valid resolutions that conform version ranges."""
    project = _instantiate_project(requirements, requirements_locked=None, files=files)

    if context:
        try:
            context = json.loads(context)
        except Exception:
            _LOGGER.exception("Failed to load Amun context that should be passed with generated stacks")
            raise
    else:
        context = {}
        _LOGGER.warning("Context to Amun API is empty")

    if decision == 'uniform-distribution':
        # Seed can be None or the one explicitly supplied from CLI.
        random.seed(seed)
        decision_function = random.uniform
    elif decision is None:
        if seed:
            raise NotImplementedError("Seed provided but no decision function selected")
        # Always consider the given software stack (generate all).
        decision_function = lambda _: True
    else:
        raise NotImplementedError("The provided decision function %r is supported", decision)

    if stack_output.startswith(('https://', 'http://')):
        # Submitting to Amun
        if context:
            try:
                context = json.loads(context)
            except Exception as exc:
                _LOGGER.error("Failed to load Amun context that should be passed with generated stacks: %s", str(exc))
                return 1
        else:
            context = {}
        output_function = partial(_dm_amun_inspect_wrapper, stack_output, context)
    elif stack_output == '-':
        output_function = _dm_stdout_output
    else:
        # TODO: stdout
        if context:
            _LOGGER.error("Unable to use context when writing generated projects onto filesystem")
            return 2

        if not os.path.isdir(stack_output):
            os.makedirs(stack_output, exist_ok=True)

        output_function = partial(_dm_amun_directory_output, stack_output)

    result = {
        'error': False,
        'report': [],
        'parameters': {
            'requirements': project.pipfile.to_dict(),
            'seed': seed,
            'decision': decision,
            'context': context,
            'stack_output': stack_output,
            'report_output': report_output
        },
        'input': None,
        'output': [],
        'count': None
    }

    count = 0
    try:
        dependency_graph = DependencyGraph.from_project(project)
        for generated_project in dependency_graph.walk(decision_function):
            count += 1

            if not dry_run:
                entry = output_function(generated_project, count=count)
                if entry:
                    result['output'].append(entry)

        result['count'] = count
    except SolverException as exc:
        _LOGGER.exception("An error occurred during solving")
        result['error'] = True

    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=report_output,
        pretty=not no_pretty
    )

    return int(result['error'] is True)


if __name__ == '__main__':
    cli()
