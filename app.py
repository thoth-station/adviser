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

"""Thoth-adviser entrypoint for s2i build."""

import sys
import os
import logging

from click.testing import CliRunner
from thoth.adviser.cli import cli

_LOGGER = logging.getLogger('thoth.adviser')

# We need to distinguish whether we run adviser or provenance checker based on env variable injected by user-api.

if __name__ == '__main__':
    run_provenance = bool(int(os.getenv('THOTH_PROVENANCE', 0)))

    runner = CliRunner()
    result = runner.invoke(cli, ['provenance' if run_provenance else 'pypi'] + sys.argv)

    print(result.output)

    if result.exception:
        raise result.exception

    sys.exit(result.exit_code)
