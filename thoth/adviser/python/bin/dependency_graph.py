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

import os
import sys
import typing
import logging
import ctypes

from thoth.common import init_logging

init_logging()

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LIBDEPENDENCY_GRAPH_SO = os.getenv("LIBDEPENDENCY_GRAPH_SO_PATH", "./libdependency_graph.so")
_LIBDEPENDENCY_GRAPH = ctypes.cdll.LoadLibrary(_LIBDEPENDENCY_GRAPH_SO)


class DependencyGraph:
    """Adapter for C implementation of dependency graph."""

    # DependencyGraph::DependencyGraph
    _C_CONSTRUCTOR = _LIBDEPENDENCY_GRAPH.DependencyGraph_new
    _C_CONSTRUCTOR.restype = ctypes.c_void_p
    _C_CONSTRUCTOR.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]

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
            dependency_types: typing.List[int]
    ):
        """Construct dependency graph.

        Create a dependency graph by propagating arguments down to library. The arguments need to be first converted
        into C-type specific ones to have correct values in the C/C++ implementation..
        """
        read_pipe_fd, write_pipe_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_pipe_fd)
            self._stack_producer(direct_dependencies, dependencies_list, dependency_types, write_pipe_fd)
            _LOGGER.error("Stack producer exited, this code has to be unreachable")
            sys.exit(1)
        else:
            self.read_pipe = os.fdopen(read_pipe_fd, "rb")
            os.close(write_pipe_fd)

    def _stack_producer(
            self,
            direct_dependencies: typing.List[int],
            dependencies_list: typing.List[typing.List[int]],
            dependency_types: typing.List[int],
            write_pipe_fd: int,
    ):
        """A producer of stacks.

        Calls libdependency_graph.so routines to generate all the stacks and quits.
        """
        try:
            _LOGGER.info("Starting stack producer from %r library...", _LIBDEPENDENCY_GRAPH_SO)
            size = len(dependency_types)
            c_dependency_types = (ctypes.c_uint * len(dependency_types))(*dependency_types)
            c_direct_dependencies = (ctypes.c_uint * len(direct_dependencies))(*direct_dependencies)

            # Convert list into ctype representation.
            c_rows = ctypes.c_uint * len(dependencies_list[1])
            c_matrix = ctypes.POINTER(ctypes.c_uint)*len(dependencies_list[0])

            c_dependencies_list = c_matrix()
            for i, row in enumerate(dependencies_list):
                c_dependencies_list[i] = c_rows()

                for j, val in enumerate(row):
                    c_dependencies_list[i][j] = val

            dependency_graph = self._C_CONSTRUCTOR(
                c_direct_dependencies,
                c_dependencies_list,
                c_dependency_types,
                size,
                write_pipe_fd
            )
            self._C_WALK_ALL(dependency_graph)
        finally:
            # Return to callee to report error in case of exceptions.
            os.close(write_pipe_fd)

        _LOGGER.debug("Stack producer ended, closing pipe")
        sys.exit(0)

    def walk(self) -> typing.List[int]:
        """Generate a software stack by traversing the graph."""
        while True:
            stack_dependencies = []
            _LOGGER.debug("Reading from pipe, item size: %d", self._ITEM_SIZE)
            while True:
                item = int.from_bytes(self.read_pipe.read(self._ITEM_SIZE), byteorder=sys.byteorder)

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
        direct_dependencies=[1, 2],
        dependencies_list=[[1, 2], [3, 2]],
        dependency_types=[1, 2, 5]
    )

    for item in f.walk():
        print(item)
