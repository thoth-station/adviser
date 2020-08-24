#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Utilities which wrap adviser's and dependency monkey's and run them in a subprocess.

This is useful for a cluster deployment where we restrict resources allocated for an adviser or dependency monkey run.
Annealing is run as a subprocess to the main process - if resources are exhausted (CPU time or memory allocated), the
subprocess is killed (either by liveness probe or by OOM killer) and the main process can still produce an
error message.
"""

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Union
from typing import Optional
import logging
import os
import time

from .exceptions import AdviserRunException
from .exceptions import UnresolvedDependencies
from .dependency_monkey import DependencyMonkey
from .dm_report import DependencyMonkeyReport
from .report import Report
from .resolver import Resolver

_LOGGER = logging.getLogger(__name__)
# This file is created by OpenShift's liveness probe on timeout.
_LIVENESS_PROBE_KILL_FILE = "/tmp/thoth_adviser_cpu_timeout"
_FORK = bool(int(os.getenv("THOTH_ADVISER_FORK", 0)))


def subprocess_run(
    resolver: Union[Resolver, DependencyMonkey],
    print_func: Callable[[float, Union[Dict[str, Any], List[Any]]], None],
    result_dict: Dict[str, Any],
    plot: Optional[str] = None,
    *,
    with_devel: bool = True,
    user_stack_scoring: bool = True,
) -> int:
    """Run the given function (partial annealing method) in a subprocess and output the produced report."""
    if not with_devel:
        _LOGGER.warning("Development dependencies will not be taken into account")

    start_time = time.monotonic()

    pid = 0
    if _FORK:
        pid = os.fork()

    if pid == 0:  # Child or no-fork mode.
        return_code = 0
        # We need to re-init logging for the sub-process.
        _LOGGER.debug("Created a child process to compute report")
        try:
            report: Union[DependencyMonkeyReport, Report] = resolver.resolve(
                with_devel=with_devel, user_stack_scoring=user_stack_scoring
            )
            if plot:
                parts = plot.rsplit(".", maxsplit=1)
                file_name = parts[0]
                extension = parts[1] if len(parts) == 2 else "png"

                predictor_history_file = f"{file_name}_{resolver.predictor.__class__.__name__}.{extension}"
                beam_history_file = f"{file_name}_{resolver.beam.__class__.__name__}.{extension}"
                try:
                    figure = resolver.predictor.plot()
                    figure.savefig(predictor_history_file, format=extension)
                except Exception as exc:
                    _LOGGER.exception("Failed to plot predictor history to %r: %s", plot, str(exc))
                else:
                    _LOGGER.info("Predictor history saved to %r", predictor_history_file)

                try:
                    figure = resolver.beam.plot()
                    figure.savefig(beam_history_file, format=extension)
                except Exception as exc:
                    _LOGGER.exception("Failed to plot beam history to %r: %s", plot, str(exc))
                else:
                    _LOGGER.info("Beam history saved to %r", beam_history_file)

            result_dict.update(dict(error=False, error_msg=None, report=report.to_dict()))
        except AdviserRunException as exc:
            if isinstance(exc, UnresolvedDependencies):
                _LOGGER.error(
                    "Resolver failed due to unsolved dependencies for packages %s; these dependencies will be "
                    "automatically marked for solving by the system for future resolutions",
                    ", ".join(exc.unresolved),
                )
                return_code = 2
            else:
                _LOGGER.error("Resolver run failed: %s", str(exc))
                return_code = 1

            result_dict.update(dict(error=True, error_msg=str(exc), report=exc.to_dict()))

        except Exception as exc:
            _LOGGER.exception("Adviser raised exception: %s", str(exc))
            result_dict.update(
                dict(error=True, error_msg=str(exc), report=dict(ERROR="An error occurred, see logs for more info"))
            )
            return_code = 2

        # Always submit results, even on error.
        print_func(time.monotonic() - start_time, result_dict)

        if _FORK:
            # 1 - error based on user input
            # 2 - error based on system not capable giving recommendations (not enough data) or internal error.
            os._exit(return_code)

        return return_code
    else:  # Parent waits for its child to terminate.
        _LOGGER.debug("Waiting for child process %r", pid)
        _, exit_code = os.waitpid(pid, 0)
        if exit_code != 0:
            _LOGGER.error("Child exited with exit code %r", exit_code)
            if (exit_code & 0xF) == 9:
                err_msg = "Adviser was killed as allocated memory has been exceeded (OOM)"
            elif os.path.isfile(_LIVENESS_PROBE_KILL_FILE):
                err_msg = "Adviser was killed as allocated CPU time was exceeded"
            else:
                err_msg = "Resolution was terminated based on errors encountered; see logs for more info"

            _LOGGER.error(err_msg)

            if _FORK and (exit_code >> 8) == 2:
                # Do not overwrite results computed in the forked process.
                return exit_code

            result_dict.update(dict(error=True, error_msg=err_msg, report=None))
            print_func(time.monotonic() - start_time, result_dict)
        else:
            _LOGGER.debug("Subprocess computing report finished successfully")

        # Propagate exit code from child process.
        return exit_code
