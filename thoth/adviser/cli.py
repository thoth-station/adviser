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

"""Thoth-adviser CLI."""

import sys

import click
import logging

from thoth.analyzer import print_command_result
from thoth.common import init_logging

from thoth.adviser import __version__ as analyzer_version
from thoth.adviser import __title__ as analyzer_name
from thoth.adviser.enums import RecommendationType
from thoth.adviser.python import advise_python

init_logging()

_LOG = logging.getLogger(__name__)


def _print_version(ctx, _, value):
    """Print adviser version and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(analyzer_version)
    ctx.exit()


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
        _LOG.setLevel(logging.DEBUG)

    _LOG.debug("Debug mode is on")


@cli.command()
@click.pass_context
@click.option('--requirements', '-r', type=str, envvar='THOTH_ADVISER_PACKAGES', required=True,
              help="Requirements to be advised and (if requested) locked.")
@click.option('--output', '-o', type=str, envvar='THOTH_ADVISER_OUTPUT', default='-',
              help="Output file or remote API to print results to, in case of URL a POST request is issued.")
@click.option('--no-pretty', '-P', is_flag=True,
              help="Do not print results nicely.")
@click.option('--runtime-environment', envvar='THOTH_ADVISER_RUNTIME_ENVIRONMENT', type=str, required=False,
              help="Generate recommendations considering the given runtime environment.")
@click.option('--recommendation-type', '-t', envvar='THOTH_ADVISER_RECOMMENDATION_TYPE', required=True,
              type=click.Choice(['STABLE', 'TESTING', 'LATEST']), default='STABLE', show_default=True,
              help="Generate recommendations respecting recommendation restriction type.")
def pypi(click_ctx, requirements, output=None, no_pretty=False, runtime_environment=None, recommendation_type=None):
    """Advise package and package versions in the given stack or on solely package only."""
    requirements = [requirement.strip() for requirement in requirements.split('\\n') if requirement]
    for recom_type in RecommendationType:
        if recommendation_type == recom_type.name:
            recommendation_type = recom_type
            break
    else:
        # This will not occur due to click's choice
        raise RuntimeError

    if not requirements:
        _LOG.error("No requirements specified, exiting")
        sys.exit(1)

    result = advise_python(requirements, recommendation_type, runtime_environment)
    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=output,
        pretty=not no_pretty
    )


if __name__ == '__main__':
    cli()
