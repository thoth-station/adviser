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

"""The main resolving algorithm working on top of states."""

import time
import math
from typing import Generator
from typing import Dict
from typing import Tuple
from typing import Any
from typing import Optional
from typing import List
from typing import Union
from typing import Set
import logging
from itertools import chain
from collections import deque
import contextlib
import signal

from thoth.python import PackageVersion
from thoth.python import Project
from thoth.storages import GraphDatabase
from thoth.storages.exceptions import NotFoundError

from .beam import Beam
from .context import Context
from .enums import DecisionType
from .enums import RecommendationType
from .exceptions import BootError
from .exceptions import CannotProduceStack
from .exceptions import EagerStopPipeline
from .exceptions import NotAcceptable
from .exceptions import SieveError
from .exceptions import StepError
from .exceptions import StrideError
from .exceptions import UnresolvedDependencies
from .exceptions import WrapError
from .exceptions import PipelineConfigurationError
from .pipeline_builder import PipelineBuilder
from .pipeline_config import PipelineConfig
from .predictor import Predictor
from .product import Product
from .report import Report
from .solver import PythonPackageGraphSolver
from .state import State
from .unit import Unit

import attr

_LOGGER = logging.getLogger(__name__)


class _NoStateAdd(Exception):
    """An exception used internally to signalize no state addition."""


def _beam_width(value: Any) -> Optional[int]:
    """Set and convert beam width."""
    if value is None:
        return None

    if not isinstance(value, int):
        raise ValueError(
            f"Unknown type for beam width: {value!r} is of type {type(value)!r}"
        )

    if value < 0:
        if value == -1:
            return None

        raise ValueError(
            "Cannot set beam width to a negative value %r, accepted values are [None, -1] for no "
            "width and any positive integer"
        )

    return value


def _limit_latest_versions(value: Any) -> Optional[int]:
    """Set and convert limit latest versions property."""
    if value is None:
        return None

    if not isinstance(value, int):
        raise ValueError(
            f"Unknown type for limit latest versions: {value!r} is of type {type(value)!r}"
        )

    if value < 0:
        if value == -1:
            return None

        raise ValueError(
            "Cannot set limit latest versions to a negative value %r, accepted values are [None, -1] for no "
            "limit and any positive integer"
        )

    return value


def _library_usage(value: Any) -> Dict[str, Any]:
    """Set and convert limit latest versions property."""
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise ValueError(
            f"Unknown type for library usage: {value!r} is of type {type(value)!r}, a dict expected"
        )

    return value


@contextlib.contextmanager
def _sigint_handler(resolver: "Resolver") -> None:
    """Register signal handler for resolver handling."""
    def handler(sig_num: int, _) -> None:
        resolver.stop_resolving = True

    old_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handler)
    yield
    signal.signal(signal.SIGINT, old_handler)


@attr.s(slots=True)
class Resolver:
    """Resolver for resolving software stacks using pipeline configuration and a predictor."""

    DEFAULT_LIMIT = 10000
    DEFAULT_COUNT = 3
    DEFAULT_BEAM_WIDTH = -1
    DEFAULT_LIMIT_LATEST_VERSIONS = -1

    pipeline = attr.ib(type=PipelineConfig, kw_only=True)
    project = attr.ib(type=Project, kw_only=True)
    library_usage = attr.ib(type=Dict[str, Any], kw_only=True, converter=_library_usage)
    graph = attr.ib(type=GraphDatabase, kw_only=True)
    predictor = attr.ib(type=Predictor, kw_only=True)
    recommendation_type = attr.ib(
        type=Optional[RecommendationType], kw_only=True, default=None
    )
    decision_type = attr.ib(type=Optional[DecisionType], kw_only=True, default=None)
    limit = attr.ib(type=int, kw_only=True, default=DEFAULT_LIMIT)
    count = attr.ib(type=int, kw_only=True, default=DEFAULT_COUNT)
    beam_width = attr.ib(
        type=Optional[int],
        kw_only=True,
        default=DEFAULT_BEAM_WIDTH,
        converter=_beam_width,  # type: ignore
    )
    limit_latest_versions = attr.ib(
        type=Optional[int],
        kw_only=True,
        default=DEFAULT_LIMIT_LATEST_VERSIONS,
        converter=_limit_latest_versions,  # type: ignore
    )
    stop_resolving = attr.ib(type=bool, default=False)

    _beam = attr.ib(type=Optional[Beam], kw_only=True, default=None)
    _solver = attr.ib(
        type=Optional[PythonPackageGraphSolver], kw_only=True, default=None
    )
    _context = attr.ib(type=Optional[Context], default=None, kw_only=True)
    _reported_shared_dependencies = attr.ib(
        type=Set[Tuple[Tuple[str, str, str], Tuple[str, str, str]]],
        default=attr.Factory(set),
        kw_only=True,
    )

    @limit.validator
    @count.validator
    def _positive_int_validator(self, attribute: str, value: int) -> None:
        """Validate the given attribute - the given attribute should have a value of a positive integer."""
        if not isinstance(value, int):
            raise ValueError(
                f"Attribute {attribute!r} should be of type int, got {type(value)!r} instead"
            )

        if value <= 0:
            raise ValueError(
                f"Value for attribute {attribute!r} should be a positive integer, got {value} instead"
            )

    @property
    def context(self) -> Context:
        """Retrieve context bound to the current resolver."""
        if self._context is None:
            raise ValueError(
                "Context not assigned yes to the current resolver instance"
            )

        return self._context

    @property
    def solver(self) -> PythonPackageGraphSolver:
        """Get solver instance - solver implemented on top of graph database."""
        if not self._solver:
            self._solver = PythonPackageGraphSolver(
                graph=self.graph, runtime_environment=self.project.runtime_environment
            )

        return self._solver

    @property
    def beam(self) -> Beam:
        """Get beam for storing states."""
        if not self._beam:
            self._beam = Beam(self.beam_width)

        return self._beam

    def _init_context(self) -> None:
        """Initialize context instance."""
        self._context = Context(
            project=self.project,
            graph=self.graph,
            library_usage=self.library_usage,
            limit=self.limit,
            count=self.count,
            beam=self.beam,
            recommendation_type=self.recommendation_type,
            decision_type=self.decision_type,
        )

    def _report_shared_dependency(self, package_tuple: Tuple[str, str, str]) -> None:
        """Report information about shared dependency in the dependency tree."""
        for library in [
            item[0] for item in self.context.dependents[package_tuple[0]][package_tuple]
        ]:
            if (package_tuple, library) not in self._reported_shared_dependencies:
                self._reported_shared_dependencies.add((package_tuple, library))
                _LOGGER.warning(
                    "Consider pinning dependency %r as it is introduced by multiple nodes in the dependency graph: %r",
                    package_tuple,
                    library,
                )

    def _run_boots(self) -> None:
        """Run all boots bound to the current annealing run context."""
        for boot in self.pipeline.boots:
            _LOGGER.debug("Running boot %r", boot.__class__.__name__)
            try:
                boot.run()
            except Exception as exc:
                raise BootError(
                    f"Failed to run pipeline boot {boot.__class__.__name__!r}: {str(exc)}"
                ) from exc

    def _run_sieves(
        self, package_versions: List[PackageVersion]
    ) -> Generator[PackageVersion, None, None]:
        """Run sieves on each package tuple."""
        result = (pv for pv in package_versions)
        for sieve in self.pipeline.sieves:
            _LOGGER.debug("Running sieve %r", sieve.__class__.__name__)
            try:
                result = sieve.run(result)
            except NotAcceptable as exc:
                _LOGGER.debug(
                    "Sieve %r removed packages %r: %s",
                    sieve.__class__.__name__,
                    str(exc),
                )
                result = []  # type: ignore
                break
            except Exception as exc:
                raise SieveError(
                    f"Failed to run sieve {sieve.__class__.__name__!r} for "
                    f"Python packages {[pv.to_tuple() for pv in package_versions]}: {str(exc)}"
                ) from exc

        yield from result

    def _run_steps(
        self, state: State, package_versions_dict: Dict[str, List[PackageVersion]]
    ) -> None:
        """Run steps and generate a new state.

        The algorithm under the hood performs backtracking to make sure each step is run once on
        the given state. This guarantees less calls to steps making the pipeline more efficient.
        """
        configuration_table = tuple(package_versions_dict.values())
        configuration_queue = deque([((0, 0), state)])

        iteration_states_added = 0
        while configuration_queue:
            idx, state = configuration_queue.popleft()
            package_version = configuration_table[idx[0]][idx[1]]
            package_version_tuple = package_version.to_tuple()
            multi_package_resolution = False

            try:
                if package_version.name in state.resolved_dependencies:
                    if (
                        state.resolved_dependencies[package_version.name]
                        != package_version_tuple
                    ):
                        # We already have the given dependency - there is a dependency clash (same name,
                        # different version or index url). Such state is invalid, drop it.
                        _LOGGER.debug(
                            "Discarding run of pipeline steps for %r: package %r was already "
                            "found in different version %r",
                            package_version_tuple,
                            package_version.name,
                            state.resolved_dependencies[package_version.name],
                        )
                        raise _NoStateAdd
                    else:
                        # We already have this dependency in stack, run steps that are
                        # required to be run in such cases.
                        multi_package_resolution = True
                        self._report_shared_dependency(package_version_tuple)

                score_addition = 0.0
                justification_addition = []
                for step in self.pipeline.steps:
                    _LOGGER.debug(
                        "Running step %r for %r",
                        step.__class__.__name__,
                        package_version_tuple,
                    )

                    if multi_package_resolution and not step.MULTI_PACKAGE_RESOLUTIONS:
                        _LOGGER.debug(
                            "Skipping running step %r - this step was already run for package %r "
                            "and step has no MULTI_PACKAGE_RESOLUTIONS flag set",
                            step.__class__.__name__,
                            package_version_tuple,
                        )
                        continue

                    try:
                        step_result = step.run(state, package_version)
                    except NotAcceptable as exc:
                        _LOGGER.debug(
                            "Step %r discarded addition of package %r in state %r: %s",
                            step.__class__.__name__,
                            package_version_tuple,
                            state,
                            str(exc),
                        )
                        raise _NoStateAdd
                    except Exception as exc:
                        raise StepError(
                            f"Failed to run step {step.__class__.__name__!r} for Python package "
                            f"{package_version_tuple!r}: {str(exc)}"
                        ) from exc

                    if step_result:
                        step_score_addition, step_justification_addition = step_result

                        if step_score_addition is not None:
                            if math.isnan(step_score_addition):
                                raise StepError(
                                    "Step %r returned score which is not a number",
                                    step.__class__.__name__,
                                )

                            if math.isinf(step_score_addition):
                                raise StepError(
                                    "Step %r returned score that is infinite",
                                    step.__class__.__name__,
                                )

                            score_addition += step_score_addition

                        if step_justification_addition is not None:
                            justification_addition.extend(step_justification_addition)
            except _NoStateAdd:
                pass
            else:
                cloned_state = state.clone()

                if not multi_package_resolution:
                    # Do NOT re-add package if it was already resolved.
                    _LOGGER.debug(
                        "Adding new unresolved dependency %r", package_version_tuple
                    )
                    cloned_state.add_unresolved_dependency(package_version_tuple)

                cloned_state.add_justification(justification_addition)
                cloned_state.score += score_addition
                cloned_state.latest_version_offset += idx[1]

                if len(configuration_table) == idx[0] + 1:
                    # No more to run - we passed all package_version of a type.
                    cloned_state.iteration = self.context.iteration
                    cloned_state.iteration_states_added = iteration_states_added
                    self.beam.add_state(cloned_state)
                    iteration_states_added += 1
                else:
                    configuration_queue.appendleft(((idx[0] + 1, 0), cloned_state))

            if idx[1] + 1 < len(configuration_table[idx[0]]):
                configuration_queue.append(((idx[0], idx[1] + 1), state))

            if len(configuration_table) == idx[0] + 1 and configuration_queue:
                # Pop last item from the queue to act like in case of back tracking.
                configuration_queue.appendleft(configuration_queue.pop())

    def _run_strides(self, state: State) -> bool:
        """Run strides and check if the given state should be accepted."""
        for stride in self.pipeline.strides:
            _LOGGER.debug("Running stride %r", stride.__class__.__name__)
            try:
                stride.run(state)
            except NotAcceptable as exc:
                _LOGGER.debug(
                    "Stride %r removed final state %r: %s",
                    stride.__class__.__name__,
                    state,
                    str(exc),
                )
                return False
            except Exception as exc:
                raise StrideError(
                    f"Failed to run stride {stride.__class__.__name__!r}: {str(exc)}"
                ) from exc

        return True

    def _run_wraps(self, state: State) -> None:
        """Run all wraps bound to the current annealing run context."""
        for wrap in self.pipeline.wraps:
            _LOGGER.debug("Running wrap %r", wrap.__class__.__name__)
            try:
                wrap.run(state)
            except Exception as exc:
                raise WrapError(
                    f"Failed to run wrap {wrap.__class__.__name__!r} on a final step: {str(exc)}"
                ) from exc

    def _resolve_direct_dependencies(
        self, *, with_devel: bool
    ) -> Dict[str, List[PackageVersion]]:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        # It's important that solver preserves order in which packages were inserted.
        # This is also a requirement for running under Python3.6+!!!
        _LOGGER.info("Resolving direct dependencies")
        resolved_direct_dependencies: Dict[
            str, List[PackageVersion]
        ] = self.solver.solve(
            list(self.project.iter_dependencies(with_devel=with_devel)), graceful=True
        )

        unresolved = []
        for package_version in self.project.iter_dependencies(with_devel=with_devel):
            package_versions = resolved_direct_dependencies.get(package_version.name)
            if not package_versions:
                # This means that there were found versions in the graph
                # database but none was matching the given version range.
                unresolved.append(package_version.name)

                error_msg = f"No versions were found for direct dependency {package_version.name!r}"
                runtime_environment = self.project.runtime_environment
                if runtime_environment.operating_system.name:
                    error_msg += f"; operating system {runtime_environment.operating_system.name!r}"
                    if runtime_environment.operating_system.version:
                        error_msg += f" in OS version {runtime_environment.operating_system.version!r}"

                if runtime_environment.python_version:
                    error_msg += (
                        f" for Python in version {runtime_environment.python_version!r}"
                    )

                _LOGGER.warning(error_msg)
                continue

        if unresolved:
            raise UnresolvedDependencies(
                "Unable to resolve all direct dependencies", unresolved=unresolved
            )

        # Now we are free to de-instantiate solver.
        del self._solver

        return resolved_direct_dependencies

    def _prepare_initial_states(self, *, with_devel: bool) -> None:
        """Prepare initial states for simulated annealing.

        Initial states are all combinations of direct dependencies.
        """
        direct_dependencies = self._resolve_direct_dependencies(with_devel=with_devel)

        for direct_dependency_name, package_versions in direct_dependencies.items():
            # Register the given dependency first.
            for direct_dependency in package_versions:
                self.context.register_package_version(direct_dependency)

            package_versions.sort(key=lambda pv: pv.semantic_version, reverse=True)
            package_versions = list(self._run_sieves(package_versions))
            if not package_versions:
                raise CannotProduceStack(
                    f"Cannot satisfy direct dependencies - direct dependencies "
                    f"of type {direct_dependency_name!r} were removed by pipeline sieves"
                )

            if self.limit_latest_versions:
                direct_dependencies[direct_dependency_name] = package_versions[:self.limit_latest_versions]
            else:
                direct_dependencies[direct_dependency_name] = package_versions

        # Create an empty state which will be extended with packages based on step results. We know we have resolved
        # all the dependencies so start with an empty beam which and an empty state and subsequently expand it based on
        # resolved direct dependencies.
        self.beam.wipe()
        self._reported_shared_dependencies = set()
        self._run_steps(State(), direct_dependencies)

    def _expand_state(self, state: State, package_name: str) -> Optional[State]:
        """Expand the given state, generate new states respecting the pipeline configuration."""
        if not state.unresolved_dependencies:
            # No unresolved dependencies, return the state -- its final.
            return state

        package_tuple = state.unresolved_dependencies.pop(package_name)

        # Obtain extras for the given package. Extras are non-empty only for direct dependencies. If indirect
        # dependencies use extras, they don't need to be explicitly stated as solvers mark "hard" dependency on
        # the given package.
        package_version: PackageVersion = self.context.get_package_version(
            package_tuple, graceful=False
        )

        extras = package_version.extras or []
        # Add None which will return also dependencies not marked as extra (see get_depends_on semantics for more info).
        extras.append(None)

        try:
            dependencies = self.graph.get_depends_on(
                *package_tuple,
                os_name=self.project.runtime_environment.operating_system.name,
                os_version=self.project.runtime_environment.operating_system.version,
                python_version=self.project.runtime_environment.python_version,
                extras=frozenset(extras),
            )
        except NotFoundError:
            _LOGGER.warning(
                "Dependency %r is not yet resolved, cannot expand state", package_tuple
            )
            return None

        state.resolved_dependencies[package_tuple[0]] = package_tuple

        if not dependencies:
            if not state.unresolved_dependencies:
                # The given package has no dependencies and nothing to resolve more, mark it as resolved.
                return state

            # No dependency, add back to beam for resolving unresolved in next rounds.
            state.iteration = self.context.iteration
            state.iteration_states_added = 0
            self.beam.add_state(state)
            return None

        return self._expand_state_add_dependencies(
            state=state,
            package_version=package_version,
            dependencies=list(chain(*dependencies.values())),
        )

    def _expand_state_add_dependencies(
        self,
        state: State,
        package_version: PackageVersion,
        dependencies: List[Tuple[str, str]],
    ) -> Optional[State]:
        """Create new states out of existing ones based on dependencies."""
        _LOGGER.debug(
            "Expanding state with dependencies based on packages solved in environments"
        )

        package_tuple = package_version.to_tuple()
        all_dependencies: Dict[str, List[Tuple[str, str, str]]] = {}
        for dependency_name, dependency_version in dependencies:
            if self.project.runtime_environment.is_fully_specified():
                marker_evaluation_result = self.graph.get_python_environment_marker_evaluation_result(
                    *package_tuple,
                    dependency_name=dependency_name,
                    dependency_version=dependency_version,
                    os_name=self.project.runtime_environment.operating_system.name,
                    os_version=self.project.runtime_environment.operating_system.version,
                    python_version=self.project.runtime_environment.python_version,
                )

                if marker_evaluation_result is False:
                    _LOGGER.debug(
                        "Removing package %r in version %r from dependency graph as it will not be installed into "
                        "the given runtime environment",
                        dependency_name,
                        dependency_version,
                    )
                    continue

            records = self.graph.get_python_package_version_records(
                package_name=dependency_name,
                package_version=dependency_version,
                index_url=None,  # Do cross-index resolving.
                os_name=self.project.runtime_environment.operating_system.name,
                os_version=self.project.runtime_environment.operating_system.version,
                python_version=self.project.runtime_environment.python_version,
            )

            # We could use a set here that would optimize a bit, but it will create randomness - it
            # will not work well with preserving seed across resolver runs.
            if dependency_name not in all_dependencies:
                all_dependencies[dependency_name] = []

            for record in records:
                dependency_tuple = (
                    record["package_name"],
                    record["package_version"],
                    record["index_url"],
                )
                self.context.register_package_tuple(
                    dependency_tuple,
                    dependent_tuple=package_tuple,
                    develop=package_version.develop,  # Propagate develop flag from parent.
                    extras=None,
                    os_name=record["os_name"],
                    os_version=record["os_version"],
                    python_version=record["python_version"],
                )

                if dependency_tuple not in all_dependencies[dependency_tuple[0]]:
                    all_dependencies[dependency_tuple[0]].append(dependency_tuple)

        # Check unsolved before sorting to optimize a bit.
        unsolved = [
            dependency_name
            for dependency_name, package_versions in all_dependencies.items()
            if not package_versions
        ]
        if unsolved:
            _LOGGER.debug(
                "Aborting creation of new states as no solved releases found for %r which would satisfy "
                "version requirements",
                ", ".join(unsolved),
            )
            return None

        for dependency_name, dependency_tuples in all_dependencies.items():
            package_versions = [
                self.context.get_package_version(d) for d in dependency_tuples
            ]
            package_versions.sort(key=lambda pv: pv.semantic_version, reverse=True)
            package_versions = list(self._run_sieves(package_versions))
            if not package_versions:
                _LOGGER.debug(
                    "All dependencies of type %r were discarded by sieves, aborting creation of new states",
                    dependency_name,
                )
                return None

            if self.limit_latest_versions:
                all_dependencies[dependency_name] = package_versions[:self.limit_latest_versions]
            else:
                all_dependencies[dependency_name] = package_versions

        if not all_dependencies and not state.unresolved_dependencies:
            # A special case when all the dependencies of the resolved one are installed conditionally
            # based on environment markers but none of the environment markers is evaluated to True. If
            # no more unresolved dependencies present, the state is final.
            return state

        if not all_dependencies:
            # All the dependencies of the resolved one are installed conditionally based on environment
            # markers but none of the environment markers is evaluated to True. As there are more
            # dependencies to be added re-add state with adjusted properties.
            state.iteration = self.context.iteration
            state.iteration_states_added = 0
            self.beam.add_state(state)
            return None

        self._run_steps(state, all_dependencies)
        return None

    def _do_resolve_states(
        self, *, with_devel: bool = True
    ) -> Generator[State, None, None]:
        """Actually perform adaptive simulated annealing."""
        self._run_boots()
        self._prepare_initial_states(with_devel=with_devel)

        _LOGGER.info(
            "Hold tight, Thoth is computing recommendations for your application..."
        )

        self.context.iteration = 0
        self.stop_resolving = False
        with _sigint_handler(self):
            while not self.stop_resolving:
                if (
                    self.context.accepted_final_states_count
                    + self.context.discarded_final_states_count
                    >= self.limit
                ):
                    _LOGGER.info(
                        "Reached limit of stacks to be generated - %r (limit is %r), stopping resolver "
                        "with the current beam size %d",
                        self.context.accepted_final_states_count,
                        self.limit,
                        self.beam.size,
                    )
                    break

                if self.beam.size == 0:
                    _LOGGER.info("The beam is empty")
                    break

                self.beam.new_iteration()
                self.context.iteration += 1

                state, package_name = self.predictor.run(self.context, self.beam)
                self.beam.remove(state)

                _LOGGER.debug(
                    "Resolving package %r in state with score %g: %r",
                    package_name,
                    state.score,
                    state
                )
                final_state = self._expand_state(state, package_name)
                if final_state:
                    if self._run_strides(final_state):
                        self._run_wraps(final_state)
                        self.context.accepted_final_states_count += 1
                        self.context.register_accepted_final_state(final_state)
                        yield final_state
                    else:
                        self.context.discarded_final_states_count += 1

        if self.stop_resolving:
            _LOGGER.warning("Resolving stopped based on SIGINT")

    def _do_resolve_products(
        self, *, with_devel: bool = True
    ) -> Generator[Product, None, None]:
        """Resolve raw products as produced by this resolver pipeline."""
        if self.count > self.limit:
            _LOGGER.warning(
                "Count (%d) is higher than limit (%d), setting count to %d",
                self.count,
                self.limit,
                self.limit,
            )
            self.count = self.limit

        if not self.project.runtime_environment.is_fully_specified():
            _LOGGER.warning(
                "Environment is not fully specified, pre-computed environment markers will not be "
                "taken into account"
            )

        self.predictor.pre_run(self.context)
        self.pipeline.call_pre_run()

        start_time = time.monotonic()
        try:
            for final_state in self._do_resolve_states(with_devel=with_devel):
                _LOGGER.info(
                    "Pipeline reached a new final state, yielding pipeline product with a score of %g",
                    final_state.score,
                )
                product = Product.from_final_state(
                    context=self.context, state=final_state
                )
                yield product
        except EagerStopPipeline as exc:
            _LOGGER.info("Stopping pipeline eagerly as per request: %s", str(exc))

        _LOGGER.info(
            "Resolver took %g seconds in total (consumer time also included)",
            time.monotonic() - start_time,
        )

        _LOGGER.info(
            "Pipeline strides discarded %d and accepted %d final states in total",
            self.context.discarded_final_states_count,
            self.context.accepted_final_states_count,
        )

        self.predictor.post_run(self.context)
        self.pipeline.call_post_run()

    def resolve_products(
        self, *, with_devel: bool = True
    ) -> Generator[Product, None, None]:
        """Resolve raw products as produced by this resolver pipeline."""
        self._init_context()
        with Unit.assigned_context(self.context):
            return self._do_resolve_products(with_devel=with_devel)

    def resolve(self, *, with_devel: bool = True) -> Report:
        """Resolve software stacks and return resolver report."""
        report = Report(count=self.count, pipeline=self.pipeline)

        self._init_context()
        with Unit.assigned_context(self.context):
            for product in self._do_resolve_products(with_devel=with_devel):
                report.add_product(product)

            if report.product_count() == 0:
                raise CannotProduceStack("No stack was produced")

            if self.context.stack_info:
                report.set_stack_info(self.context.stack_info)

            self.predictor.post_run_report(self.context, report)
            self.pipeline.call_post_run_report(report)

        return report

    @classmethod
    def get_adviser_instance(
        cls,
        *,
        predictor: Predictor,
        beam_width: Optional[int] = None,
        count: int = DEFAULT_COUNT,
        graph: Optional[GraphDatabase] = None,
        library_usage: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        limit_latest_versions: Optional[int] = DEFAULT_LIMIT_LATEST_VERSIONS,
        project: Project,
        recommendation_type: RecommendationType,
        pipeline_config: Optional[Union[PipelineConfig, Dict[str, Any]]] = None,
    ) -> "Resolver":
        """Get instance of resolver based on the project given to recommend software stacks."""
        graph = graph or GraphDatabase()
        if not graph.is_connected():
            graph.connect()

        if pipeline_config is None:
            pipeline = PipelineBuilder.get_adviser_pipeline_config(
                recommendation_type=recommendation_type,
                project=project,
                library_usage=library_usage,
                graph=graph,
            )
        else:
            if isinstance(pipeline_config, PipelineConfig):
                pipeline = pipeline_config
            elif isinstance(pipeline_config, dict):
                pipeline = PipelineBuilder.from_dict(pipeline_config)
            else:
                raise PipelineConfigurationError(
                    f"Unknown pipeline configuration type: {type(pipeline_config)!r}"
                )

        resolver = cls(
            beam_width=beam_width,
            count=count,
            graph=graph,
            library_usage=library_usage,
            limit_latest_versions=limit_latest_versions,
            limit=limit,
            pipeline=pipeline,
            predictor=predictor,
            project=project,
            recommendation_type=recommendation_type,
        )

        return resolver

    @classmethod
    def get_dependency_monkey_instance(
        cls,
        *,
        predictor: Predictor,
        beam_width: Optional[int] = None,
        count: int = DEFAULT_COUNT,
        graph: Optional[GraphDatabase] = None,
        library_usage: Optional[Dict[str, Any]] = None,
        limit_latest_versions: Optional[int] = DEFAULT_LIMIT_LATEST_VERSIONS,
        project: Project,
        decision_type: DecisionType,
        pipeline_config: Optional[Union[PipelineConfig, Dict[str, Any]]] = None,
    ) -> "Resolver":
        """Get instance of resolver based on the project given to run dependency monkey."""
        graph = graph or GraphDatabase()
        if not graph.is_connected():
            graph.connect()

        if pipeline_config is None:
            pipeline = PipelineBuilder.get_dependency_monkey_pipeline_config(
                decision_type=decision_type,
                graph=graph,
                project=project,
                library_usage=library_usage,
            )
        else:
            if isinstance(pipeline_config, PipelineConfig):
                pipeline = pipeline_config
            elif isinstance(pipeline_config, dict):
                pipeline = PipelineBuilder.from_dict(pipeline_config)
            else:
                raise PipelineConfigurationError(
                    f"Unknown pipeline configuration type: {type(pipeline_config)!r}"
                )

        resolver = cls(
            beam_width=beam_width,
            count=count,
            limit=count,  # always match as limit is always same as count for Dependency Monkey.
            graph=graph,
            library_usage=library_usage,
            limit_latest_versions=limit_latest_versions,
            pipeline=pipeline,
            predictor=predictor,
            project=project,
            decision_type=decision_type,
        )

        return resolver
