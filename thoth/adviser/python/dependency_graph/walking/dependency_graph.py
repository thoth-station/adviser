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
from contextlib import suppress
from typing import List
from typing import Tuple
from collections import Counter
from functools import reduce

_LOGGER = logging.getLogger(__name__)
_DEFAULT_LIBDEPENDENCY_GRAPH_SO = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "libdependency_graph.so"
)
_LIBDEPENDENCY_GRAPH_SO = os.getenv(
    "LIBDEPENDENCY_GRAPH_SO_PATH", _DEFAULT_LIBDEPENDENCY_GRAPH_SO
)
_LIBDEPENDENCY_GRAPH = ctypes.cdll.LoadLibrary(_LIBDEPENDENCY_GRAPH_SO)


class DependencyGraphWalkerException(Exception):
    """A base class for dependency graph exception hierarchy."""


class PrematureStreamEndError(DependencyGraphWalkerException):
    """An exception raised if the stack stream was closed prematurely.

    This can happen for example due to OOM, which can kill stack producer. In that case we would like to
    report to user what we have computed so far.
    """


class NoDependenciesError(DependencyGraphWalkerException):
    """An exception raised if no direct dependencies were provided to dependency graph."""


class DependenciesCountOverflow(DependencyGraphWalkerException):
    """An exception raised if number of dependencies cannot be processed due to overflow.

    Based on internal representation of packages (fixed size unsigned integers).
    """


class DependencyGraph:
    """Adapter for C implementation of dependency graph."""

    __slots__ = [
        "_context",
        "_direct_dependencies",
        "_dependency_types",
        "_dependencies_list",
        "_read_pipe",
        "_producer_pid",
    ]

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
    _C_GET_STREAM_DELIMITER.restype = ctypes.c_uint16
    STREAM_DELIMITER = _C_GET_STREAM_DELIMITER()

    # Marker used to signalize end of the stack stream (one stack delimited by this marker).
    _C_GET_STREAM_STOP = _LIBDEPENDENCY_GRAPH.get_stream_stop
    _C_GET_STREAM_STOP.restype = ctypes.c_uint16
    STREAM_STOP = _C_GET_STREAM_STOP()

    # Given the fact we have uint16_t for representing a package and 2 markers - stream stop and delimiter marker.
    MAX_DEPENDENCIES_COUNT = (2 ** 16) - 2

    def __init__(
        self,
        direct_dependencies: typing.List[Tuple[str, str, str]],
        paths: typing.List[typing.List[Tuple[str, str, str]]],
    ):
        """Construct dependency graph.

        Create a dependency graph by propagating arguments down to library. The arguments need to be first converted
        into C-type specific ones to have correct values in the C/C++ implementation..
        """
        if len(direct_dependencies) == 0:
            raise NoDependenciesError(
                "Cannot run dependency graph if no direct dependencies are specified"
            )

        # Mapping id to a package tuple to reconstruct back results from C/C++ library.
        self._context = []

        self._read_pipe = None
        self._producer_pid = None
        self._direct_dependencies = []
        self._dependencies_list = []
        self._dependency_types = []

        # Remove duplicates of direct dependencies, if provided on input.
        direct_dependencies = list(
            dict.fromkeys(tuple(d) for d in direct_dependencies).keys()
        )

        # Make sure we assign each package type which was already seen.
        assigned_dependency_types = {}
        # Mapping from a package tuple to its id to match package tuple with exactly one id.
        reverse_context = {}
        for path in paths:
            for idx, package_tuple in enumerate(path):
                package_type = assigned_dependency_types.get(package_tuple[0])
                if package_type is None:
                    package_type = len(assigned_dependency_types)
                    assigned_dependency_types[package_tuple[0]] = package_type

                package_id = reverse_context.get(package_tuple)
                if package_id is None:
                    assert len(self._context) == len(reverse_context)
                    package_id = len(reverse_context)
                    reverse_context[package_tuple] = package_id
                    self._context.append(package_tuple)
                    self._dependency_types.append(package_type)

                if idx > 0:
                    # State this package is dependent on the previous one.
                    self._dependencies_list[-1].append(package_id)

                if idx + 1 < len(path):
                    # There is still one more package in path, we state dependency
                    # from the current package to the next one in next iteration - see above.
                    self._dependencies_list.append([package_id])

        for package_tuple in direct_dependencies:
            package_type = assigned_dependency_types.get(package_tuple[0])
            if package_type is None:
                package_type = len(assigned_dependency_types)
                assigned_dependency_types[package_tuple[0]] = package_type

            package_id = reverse_context.get(package_tuple)
            if package_id is None:
                # This can happen if a direct dependency has no dependencies.
                assert len(self._context) == len(reverse_context)
                package_id = len(reverse_context)
                reverse_context[package_tuple] = package_id
                self._context.append(package_tuple)
                self._dependency_types.append(package_type)

            self._direct_dependencies.append(package_id)

        if bool(os.getenv("THOTH_ADVISER_SHOW_PACKAGES", 0)):
            _LOGGER.info("Packages considered in dependency graph traversal:")
            for item in self._context:
                _LOGGER.info("    %r", item)

        if len(self._context) > self.MAX_DEPENDENCIES_COUNT:
            raise DependenciesCountOverflow(
                f"Number of dependencies overflowed dependency graph implementation, number "
                f"of dependencies: {len(self._context)}, limit is {self.MAX_DEPENDENCIES_COUNT}"
            )

        # Remove duplicates of paths, but preserve order of these dependencies so
        # dependency graph generates based on dependencies stated.
        self._dependencies_list = list(
            dict.fromkeys(tuple(d) for d in self._dependencies_list).keys()
        )

    def __del__(self):
        """Destructor - free up resources."""
        # Kill the child process that produces stacks.
        with suppress(AttributeError):
            if self._producer_pid is not None:
                os.kill(self._producer_pid, signal.SIGKILL)

    @property
    def stacks_estimated(self) -> int:
        """Estimate number of software stacks we could end up with (the upper bound)."""
        # We could estimate based on traversing the tree, it would give us better, but still rough estimate.
        counter = Counter(self._dependency_types)
        return reduce((lambda x, y: x * y), counter.values())

    def _reconstruct_stack(self, stack: List[int]) -> List[Tuple[str, str, str]]:
        """Reconstruct the stack based on results from libdependency graph walks.

        Convert numeric representation of stacks to package version tuples.
        """
        result = []
        for package_id in stack:
            package_entry = self._context[package_id]
            result.append(package_entry)

        return result

    def _stack_producer(self, write_fd: int):
        """A producer of stacks.

        Calls libdependency_graph.so routines to generate all the stacks and quits.
        """
        try:
            _LOGGER.info(
                "Starting stack producer from %r library...", _LIBDEPENDENCY_GRAPH_SO
            )
            size = len(self._dependency_types)
            c_dependency_types = (ctypes.c_uint16 * len(self._dependency_types))(
                *self._dependency_types
            )
            c_direct_dependencies = (ctypes.c_uint16 * len(self._direct_dependencies))(
                *self._direct_dependencies
            )

            # Convert list into ctype representation.
            c_rows = ctypes.c_uint16 * 2
            c_matrix = ctypes.POINTER(ctypes.c_uint16) * len(self._dependencies_list)

            c_dependencies_list = c_matrix()
            for i, row in enumerate(self._dependencies_list):
                c_dependencies_list[i] = c_rows()
                c_dependencies_list[i][0] = self._dependencies_list[i][0]
                c_dependencies_list[i][1] = self._dependencies_list[i][1]

            _LOGGER.debug("Calling dependency graph constructor")
            _LOGGER.debug("Dependencies list size: %d", len(self._dependencies_list))
            _LOGGER.debug(
                "Number of direct dependencies: %d", len(self._direct_dependencies)
            )
            _LOGGER.debug("Total number of packages considered: %d", size)
            dependency_graph = self._C_CONSTRUCTOR(
                c_direct_dependencies,
                len(self._direct_dependencies),
                c_dependencies_list,
                len(self._dependencies_list),
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
        # graph db are done in async coroutines. If the stack producer process finishes sooner, we get stuck in the
        # event loop which is halted due to SIGCHILD signal. Obviously, child cannot wait for parent in
        # waitpid call (in a POSIX compliant way), so we send SIGSTOP to self (stack producer process) and wait
        # for parent to finish passively so we are out of OS process scheduler. Once the parent finishes
        # we finish as well as we receive SIGTERM.
        _LOGGER.debug("Generation of stacks has finished, waiting passively for parent")
        os.kill(os.getpid(), signal.SIGSTOP)
        _LOGGER.info("Stack producer ended")
        sys.exit(0)

    def _create_stack_producer_subprocess(self):
        """Create a stack producer subprocess and instantiate pipe for IPC."""
        _LOGGER.debug("Forking and creating stack producer subprocess")
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            self._stack_producer(write_fd)
            _LOGGER.error(
                "Stack producer exited abnormally, this code has to be unreachable"
            )
            sys.exit(1)
        else:
            self._read_pipe = os.fdopen(read_fd, "rb")
            os.close(write_fd)
            self._producer_pid = pid

    def walk(
        self
    ) -> typing.Generator[typing.List[typing.Tuple[str, str, str]], None, None]:
        """Generate a software stack by traversing the graph."""
        stack_dependencies = []
        self._create_stack_producer_subprocess()

        _LOGGER.debug("Reading from pipe, item size: %d", self._ITEM_SIZE)
        try:
            while True:
                item = self._read_pipe.read(self._ITEM_SIZE)

                if not item:
                    raise PrematureStreamEndError("Reached end of stream prematurely")

                item = int.from_bytes(item, byteorder=sys.byteorder)

                if item == self.STREAM_DELIMITER:
                    _LOGGER.debug("Reached stack delimiter, yielding stack")
                    yield self._reconstruct_stack(stack_dependencies)
                    stack_dependencies = []
                    continue

                if item == self.STREAM_STOP:
                    _LOGGER.debug("Reached stream stop marker, closing read pipe")
                    self._read_pipe.close()
                    return

                stack_dependencies.append(item)
        finally:
            # Ensure stack producer gets killed if there is no consumer
            # e.g. on keyboard interrupt in Jupyter Notebook.
            try:
                os.kill(self._producer_pid, signal.SIGKILL)
            except Exception:
                pass
