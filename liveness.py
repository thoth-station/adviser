#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

"""A liveness probe run in OpenShift.

This liveness probe is run by OpenShift in a deployment where adviser is run. It's intention is
to always kill stack producer (libdependency_graph.so) on request timeout so that the main process
reports back what stacks were scored meanwhile.

This Python script *HAS TO* be run in a container as it kills all the processes except the
main process (PID 1).
"""

import sys
import os
import signal
from pathlib import Path

# Create this file on kill for better reports in adviser logs.
_LIVENESS_PROBE_KILL_FILE = "/tmp/thoth_adviser_cpu_timeout"


def main() -> int:
    """Kill all processes except for main."""
    pids = [int(pid) for pid in os.listdir('/proc') if pid.isdigit()]

    for pid in pids:
        if pid == 1:
            # No attempt to kill main process.
            continue
        if os.getpid() == pid:
            # Do not kill self.
            continue

        print("Killing process with PID %d" % pid)
        os.kill(pid, signal.SIGTERM)
        Path(_LIVENESS_PROBE_KILL_FILE).touch()

    # Let liveness probe always fail with timeout.
    signal.pause()
    return 1


if __name__ == '__main__':
    sys.exit(main())
