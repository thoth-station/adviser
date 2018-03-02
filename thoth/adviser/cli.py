#!/usr/bin/env python3
"""Thoth-adviser CLI."""

import sys

import click
import logging

from thoth.analyzer import print_command_result

from thoth.adviser import __version__ as analyzer_version
from thoth.adviser import __title__ as analyzer_name
from thoth.adviser.pypi import advise_pypi


_LOG = logging.getLogger(__name__)


def _setup_logging(verbose):
    """Set up Python logging based on verbosity level.

    :param verbose: verbosity level
    """
    # TODO: move this logic to thoth-analyzer or thoth-common
    level = logging.INFO if not verbose else logging.DEBUG
    logger = logging.getLogger()
    logger.setLevel(level)


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
    _setup_logging(verbose)


@cli.command()
@click.pass_context
@click.option('--requirements', '-r', type=str, envvar='THOTH_ADVISER_PACKAGES', required=True,
              help="Requirements to be advised and (if requested) locked.")
@click.option('--output', '-o', type=str, envvar='THOTH_ADVISER_OUTPUT', default='-',
              help="Output file or remote API to print results to, in case of URL a POST request is issued.")
@click.option('--no-pretty', '-P', is_flag=True,
              help="Do not print results nicely.")
@click.option('--packages-only', '-P', envvar='THOTH_ADVISER_PACKAGES_ONLY', is_flag=True,
              help="Advise on package level, do not use stacks.")
def pypi(click_ctx, requirements, output=None, no_pretty=False, packages_only=False):
    """Advise package and package versions in the given stack or on solely package only."""
    requirements = [requirement.strip() for requirement in requirements.split('\n') if requirement]

    if not requirements:
        _LOG.error("No requirements specified, exiting")
        sys.exit(1)

    result = advise_pypi(requirements, packages_only=packages_only)
    print_command_result(click_ctx, result,
                         analyzer=analyzer_name, analyzer_version=analyzer_version, output=output, pretty=not no_pretty)


if __name__ == '__main__':
    cli()
