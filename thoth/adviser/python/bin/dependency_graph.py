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

"""An adapter implementation for talking to libdependency_graph.so (C/C++ implementation of dependency graph)."""

import os
import sys
import typing
import logging
import ctypes
import signal

from thoth.common import init_logging
from .exceptions import PrematureStreamEndError

init_logging()

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_DEFAULT_LIBDEPENDENCY_GRAPH_SO = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "libdependency_graph.so"
)
_LIBDEPENDENCY_GRAPH_SO = os.getenv(
    "LIBDEPENDENCY_GRAPH_SO_PATH", _DEFAULT_LIBDEPENDENCY_GRAPH_SO
)
_LIBDEPENDENCY_GRAPH = ctypes.cdll.LoadLibrary(_LIBDEPENDENCY_GRAPH_SO)


class DependencyGraph:
    """Adapter for C implementation of dependency graph."""

    # DependencyGraph::DependencyGraph
    _C_CONSTRUCTOR = _LIBDEPENDENCY_GRAPH.DependencyGraph_new
    _C_CONSTRUCTOR.restype = ctypes.c_void_p
    _C_CONSTRUCTOR.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_int,
    ]

    # DependencyGraph::walk_all
    _C_WALK_ALL = _LIBDEPENDENCY_GRAPH.DependencyGraph_walk_all
    _C_WALK_ALL.argtypes = [ctypes.c_void_p]

    # DependencyGraph::walk
    _C_WALK = _LIBDEPENDENCY_GRAPH.DependencyGraph_walk
    _C_WALK.argtypes = [ctypes.c_void_p]
    _C_WALK.restype = ctypes.c_bool

    # Size of a package identifier as returned by dependency graph (note its platform specific).
    _C_GET_ITEM_SIZE = _LIBDEPENDENCY_GRAPH.get_item_size
    _C_GET_ITEM_SIZE.restype = ctypes.c_size_t
    _ITEM_SIZE = _C_GET_ITEM_SIZE()

    # Marker used to signalize delimit stacks in stack stream (one stack delimited by this marker).
    _C_GET_STREAM_DELIMITER = _LIBDEPENDENCY_GRAPH.get_stream_delimiter
    _C_GET_STREAM_DELIMITER.restype = ctypes.c_uint
    STREAM_DELIMITER = _C_GET_STREAM_DELIMITER()

    # Marker used to signalize end of the stack stream (one stack delimited by this marker).
    _C_GET_STREAM_STOP = _LIBDEPENDENCY_GRAPH.get_stream_stop
    _C_GET_STREAM_STOP.restype = ctypes.c_uint
    STREAM_STOP = _C_GET_STREAM_STOP()

    def __init__(
        self,
        direct_dependencies: typing.List[int],
        dependencies_list: typing.List[typing.List[int]],
        dependency_types: typing.List[int],
    ):
        """Construct dependency graph.

        Create a dependency graph by propagating arguments down to library. The arguments need to be first converted
        into C-type specific ones to have correct values in the C/C++ implementation..
        """
        read_fd, write_fd = os.pipe()

        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            self._stack_producer(
                direct_dependencies, dependencies_list, dependency_types, write_fd
            )
            _LOGGER.error(
                "Stack producer exited abnormally, this code has to be unreachable"
            )
            sys.exit(1)
        else:
            self.read_pipe = os.fdopen(read_fd, "rb")
            os.close(write_fd)
            self.producer_pid = pid

    def __del__(self):
        """Destructor - free up resources."""
        # Kill the child process that produces stacks.
        try:
            os.kill(self.producer_pid, signal.SIGKILL)
        except AttributeError:
            pass

    def _stack_producer(
        self,
        direct_dependencies: typing.List[int],
        dependencies_list: typing.List[typing.List[int]],
        dependency_types: typing.List[int],
        write_fd: int,
    ):
        """A producer of stacks.

        Calls libdependency_graph.so routines to generate all the stacks and quits.
        """
        try:
            _LOGGER.info(
                "Starting stack producer from %r library...", _LIBDEPENDENCY_GRAPH_SO
            )
            size = len(dependency_types)
            c_dependency_types = (ctypes.c_uint * len(dependency_types))(
                *dependency_types
            )
            c_direct_dependencies = (ctypes.c_uint * len(direct_dependencies))(
                *direct_dependencies
            )

            # Convert list into ctype representation.
            c_rows = ctypes.c_uint * 2
            c_matrix = ctypes.POINTER(ctypes.c_uint) * len(dependencies_list)

            c_dependencies_list = c_matrix()
            for i, row in enumerate(dependencies_list):
                c_dependencies_list[i] = c_rows()
                c_dependencies_list[i][0] = dependencies_list[i][0]
                c_dependencies_list[i][1] = dependencies_list[i][1]

            _LOGGER.debug("Calling dependency graph constructor")
            _LOGGER.debug("Dependencies list size: %d", len(dependencies_list))
            _LOGGER.debug("Number of direct dependencies: %d", len(direct_dependencies))
            _LOGGER.debug("Total number of packages considered: %d", size)
            dependency_graph = self._C_CONSTRUCTOR(
                c_direct_dependencies,
                len(direct_dependencies),
                c_dependencies_list,
                len(dependencies_list),
                c_dependency_types,
                size,
                write_fd,
            )
            _LOGGER.debug("Starting dependency graph walk...")
            self._C_WALK_ALL(dependency_graph)
        finally:
            # Return to callee to report error in case of exceptions.
            os.close(write_fd)

        # This is a really dirty hack, but it is required. We need to wait for parent to finish as queries to the
        # JanusGraph are done in async coroutines. If the stack producer process finishes sooner, we get stuck in the
        # event loop which is halted due to SIGCHILD signal. Obviously, child cannot wait for parent in
        # waitpid call (in a POSIX compliant way), so we send SIGSTOP to self (stack producer process) and wait
        # for parent to finish passively so we are out of OS process scheduler. Once the parent finishes
        # we finish as well as we receive SIGTERM.
        _LOGGER.debug("Generation of stacks has finished, waiting passively for parent")
        os.kill(os.getpid(), signal.SIGSTOP)
        _LOGGER.info("Stack producer ended")
        sys.exit(0)

    def walk(self) -> typing.Generator[typing.List[int], None, None]:
        """Generate a software stack by traversing the graph."""
        stack_dependencies = []
        _LOGGER.debug("Reading from pipe, item size: %d", self._ITEM_SIZE)
        while True:
            item = self.read_pipe.read(self._ITEM_SIZE)

            if not item:
                raise PrematureStreamEndError("Reached end of stream prematurely")

            item = int.from_bytes(item, byteorder=sys.byteorder)

            if item == self.STREAM_DELIMITER:
                _LOGGER.debug("Reached stack delimiter, yielding stack")
                yield stack_dependencies
                stack_dependencies = []
                continue

            if item == self.STREAM_STOP:
                _LOGGER.debug("Reached stream stop marker, closing read pipe")
                self.read_pipe.close()
                return

            stack_dependencies.append(item)


if __name__ == "__main__":
    f = DependencyGraph(
        direct_dependencies=[0, 1, 2],
        dependencies_list=[[1, 3], [2, 5], [3, 6], [3, 1]],
        dependency_types=[0, 0, 2, 3, 0, 5, 4],
    )

    for walk_item in f.walk():
        print(walk_item)
