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

"""Implementation of stack generation pipeline."""

from typing import Generator
from typing import List
from typing import Tuple
from typing import Dict
from itertools import chain
import logging
from time import monotonic

import attr

from thoth.adviser.python.solver import PythonPackageGraphSolver
from thoth.adviser.python.bin.exceptions import PrematureStreamEndError
from thoth.adviser.python.bin.dependency_graph import DependencyGraph
from thoth.python import Project
from thoth.solver.python.base import SolverException
from thoth.storages import GraphDatabase

from .step import Step
from .step_context import StepContext
from .stride import Stride
from .stride_context import StrideContext
from .stack_candidates import StackCandidates
from .exceptions import StrideRemoveStack
from .product import PipelineProduct

_LOGGER = logging.getLogger(__name__)


@attr.s
class Pipeline:
    """A stack generation pipeline."""

    graph = attr.ib(type=GraphDatabase)
    project = attr.ib(type=Project)
    steps = attr.ib(type=List[Tuple[type, dict]], default=attr.Factory(list))
    strides = attr.ib(type=List[Tuple[type, dict]], default=attr.Factory(list))
    library_usage = attr.ib(type=dict, default=attr.Factory(dict))
    _solver = attr.ib(type=PythonPackageGraphSolver, default=None)
    _stack_info = attr.ib(type=List[Dict], default=attr.Factory(list))

    @property
    def solver(self) -> PythonPackageGraphSolver:
        """Get solver instance - solver implemented on top of graph database."""
        if not self._solver:
            self._solver = PythonPackageGraphSolver(
                graph_db=self.graph,
                runtime_environment=self.project.runtime_environment,
            )

        return self._solver

    def get_stack_info(self) -> List[Dict]:
        """Get report of a pipeline run.

        This report includes reports from dependency graph walk.
        """
        return self._stack_info

    def _prepare_direct_dependencies(self, *, with_devel: bool) -> StepContext:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        # It's important that solver preserves order in which packages were inserted.
        # This is also a requirement for running under Python3.6+!!!
        _LOGGER.info("Resolving direct dependencies")
        step_context = StepContext()
        resolved_direct_dependencies = self.solver.solve(
            list(self.project.iter_dependencies(with_devel=with_devel)),
            graceful=False,
            all_versions=True,
        )

        unresolved = []
        for package_name, package_versions in resolved_direct_dependencies.items():
            if not package_versions:
                # This means that there were found versions in the graph
                # database but none was matching the given version range.
                unresolved.append(package_name)
                _LOGGER.error(
                    "No versions were found for direct dependency %r", package_name
                )
                continue

            for package_version in package_versions:
                step_context.add_resolved_direct_dependency(package_version)

        if unresolved:
            raise SolverException(
                "Unable to resolve all direct dependencies, no versions were found for packages %s",
                ",".join(unresolved),
            )

        return step_context

    def _get_python_package_tuples(
        self, ids_map: Dict[int, tuple], transitive_dependencies: List
    ) -> List[List[Tuple[str, str, str]]]:
        """Retrieve tuples representing package name, package version and index url for the given set of ids."""
        # We need to explicitly iterate over these results as gremlin-python wraps result into Path object
        # which does not support advanced indexing like 0::2.
        seen_ids = ids_map.keys()
        unseen_ids = set()
        for entry in transitive_dependencies:
            for idx in range(len(entry)):
                if entry[idx] not in seen_ids:
                    unseen_ids.add(entry[idx])

        if len(unseen_ids) > 0:
            _LOGGER.debug(
                "Retrieving package tuples for transitive dependencies (count: %d)",
                len(unseen_ids),
            )

        package_tuples = self.graph.get_python_package_tuples(unseen_ids)
        for python_package_id, package_tuple in package_tuples.items():
            ids_map[python_package_id] = package_tuple

        result = []
        for entries in transitive_dependencies:
            new_entries = []
            for idx, entry in enumerate(entries):
                new_entries.append(ids_map[entry])
            result.append(new_entries)

        return result

    def _resolve_transitive_dependencies(self, step_context: StepContext) -> None:
        """Solve all direct dependencies to find all transitive paths (all possible transitive dependencies)."""
        _LOGGER.info("Resolving transitive dependencies of direct dependencies")

        ids_map = {}
        for package_version in step_context.iter_direct_dependencies():
            _LOGGER.debug(
                "Retrieving transitive dependencies for %r in version %r from %r",
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
            )
            transitive_dependencies = self.graph.retrieve_transitive_dependencies_python(
                package_version.name,
                package_version.locked_version,
                package_version.index.url,
            )
            transitive_dependencies = self._get_python_package_tuples(
                ids_map, transitive_dependencies
            )
            step_context.add_paths(transitive_dependencies)

    def _initialize_stepping(self) -> StepContext:
        """Initialize pipeline - resolve direct dependencies and all the transitive dependencies."""
        _LOGGER.debug("Initializing pipeline")
        step_context = self._prepare_direct_dependencies(with_devel=True)
        _LOGGER.info("Retrieving transitive dependencies of direct dependencies")
        transitive_dependencies_tuples = set(
            (pv.name, pv.locked_version, pv.index.url)
            for pv in step_context.iter_direct_dependencies()
        )
        _LOGGER.debug(
            "Direct dependencies considered: %r", transitive_dependencies_tuples
        )
        transitive_dependencies = self.graph.retrieve_transitive_dependencies_python_multi(
            transitive_dependencies_tuples
        )
        transitive_dependencies = list(chain(*transitive_dependencies.values()))
        step_context.add_paths(transitive_dependencies)
        return step_context

    @staticmethod
    def _finalize_stepping(step_context: StepContext) -> DependencyGraph:
        """Finalize pipeline - run dependency graph to resolve fully pinned down stacks."""
        _LOGGER.debug("Finalizing stepping")
        step_context.final_sort()
        dependency_graph = DependencyGraph(
            direct_dependencies=list(step_context.iter_direct_dependencies_tuple()),
            paths=step_context.raw_paths,
        )
        _LOGGER.info(
            "Estimated number of stacks: %d", dependency_graph.stacks_estimated
        )
        return dependency_graph

    def _instantiate_strides(self) -> List[Stride]:
        """Instantiate stride classes with configuration supplied."""
        _LOGGER.debug("Instantiating strides")
        strides = []
        for stride_class, parameters_dict in self.strides:
            filter_instance: Stride = stride_class(
                graph=self.graph, project=self.project, library_usage=self.library_usage
            )
            if parameters_dict:
                filter_instance.update_parameters(parameters_dict)
            strides.append(filter_instance)

        return strides

    @staticmethod
    def _log_pipeline_msg(count: int = None, limit: int = None) -> None:
        msg = "Starting stack generation pipeline"
        if count:
            msg += f", pipeline will produce at most {count} stacks"
        if limit:
            msg += f", limit for number of stacks scored in total is set to {limit}"
        _LOGGER.info(msg)

    def conduct(
        self, count: int = None, limit: int = None
    ) -> Generator[PipelineProduct, None, None]:
        """Chain execution of each step and filter in a pipeline and execute it."""
        start_time = monotonic()
        step_context = self._initialize_stepping()
        strides = self._instantiate_strides()

        if count is not None and count <= 0:
            raise ValueError(
                "Number of projects produced by pipeline (count) has to be higher than 0"
            )

        if limit is not None and limit <= 0:
            raise ValueError(
                "Number of projects scored by pipeline (limit) has to be higher than 0"
            )

        if count is not None and limit is not None and count > limit:
            _LOGGER.warning(
                "Cannot return more stacks (%d) than scored, adjusting count to %d based on limit provided",
                count,
                limit,
            )
            count = limit

        self._log_pipeline_msg(count, limit)
        step_context.stats.start_timer()
        for step_class, parameters_dict in self.steps:
            step_instance: Step = step_class(
                graph=self.graph, project=self.project, library_usage=self.library_usage
            )
            _LOGGER.info("Running pipeline step %r", step_instance.name)
            if parameters_dict:
                step_instance.update_parameters(parameters_dict)
            step_context.stats.reset_stats(step_instance)
            step_instance.run(step_context)

        step_context.stats.log_report()

        stacks_seen = 0
        stacks_added = 0
        stack_candidates = StackCandidates(
            input_project=self.project,
            count=count,
            direct_dependencies_map=step_context.direct_dependencies_map,
            transitive_dependencies_map=step_context.transitive_dependencies_map,
        )
        if len(strides) > 0:
            _LOGGER.info("Running strides on stack candidates")
        dependency_graph = self._finalize_stepping(step_context)
        try:
            for stack_candidate in dependency_graph.walk():
                stacks_seen += 1
                stride_context = StrideContext(stack_candidate)

                stride_context.stats.start_timer()
                for stride_instance in strides:
                    _LOGGER.debug("Running stride %r", stride_instance.name)
                    stride_context.stats.reset_stats(stride_instance)
                    try:
                        stride_instance.run(stride_context)
                    except StrideRemoveStack as exc:
                        _LOGGER.debug(
                            "Stride %r filtered out stack %r: %s",
                            stride_instance.name,
                            stack_candidate,
                            str(exc),
                        )
                        break
                else:
                    stack_candidates.add(stride_context)
                    stacks_added += 1
                    if limit is not None and stacks_added >= limit:
                        break

                if len(strides) > 0:
                    stride_context.stats.log_report()
        except PrematureStreamEndError as exc:
            _LOGGER.info("Error while dependency graph walk: %s", str(exc))
            self._stack_info.append(
                {
                    "type": "WARNING",
                    "justification": "Resolver was closed prematurely because of memory or time-out, consider "
                    "decreasing latest versions considered in software stacks",
                }
            )
        finally:
            if len(strides) == 0:
                _LOGGER.debug("No strides were configured")

            _LOGGER.info(
                "Pipeline produced %d stacks in total in %.4f seconds, %d stacks were discarded by strides",
                stacks_added,
                monotonic() - start_time,
                stacks_seen - stacks_added,
            )
            return stack_candidates.generate_pipeline_products()
