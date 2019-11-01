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

"""Implementation of Adaptive Simulated Annealing (ASA) used to resolve software stacks."""

import time
import os
from typing import Generator
from typing import Dict
from typing import Callable
from typing import Any
from typing import Tuple
from typing import Optional
from typing import List
import logging
from itertools import chain
from itertools import product as itertools_product
from math import exp
import random

from thoth.python import PackageVersion
from thoth.python import Project
from thoth.storages import GraphDatabase
from thoth.storages.exceptions import NotFoundError

from .beam import Beam
from .context import Context
from .enums import RecommendationType
from .exceptions import CannotProduceStack
from .exceptions import NotAcceptable
from .exceptions import UnresolvedDependencies
from .exceptions import BootError
from .exceptions import SieveError
from .exceptions import StepError
from .exceptions import StrideError
from .exceptions import EagerStopPipeline
from .exceptions import WrapError

from .pipeline_builder import PipelineBuilder
from .pipeline_config import PipelineConfig
from .product import Product
from .report import Report
from .solver import PythonPackageGraphSolver  # type: ignore
from .state import State
from .temperature import ASATemperatureFunction
from .unit import Unit

import attr

_LOGGER = logging.getLogger(__name__)


def _keep_temperature_history(value: Any) -> bool:
    """Check if the history should be kept.

    If not set explicitly during invocation, check environment variable to turn of history tracking.
    """
    if value is None:
        return not bool(int(os.getenv("THOTH_ADVISER_NO_HISTORY", 0)))

    if isinstance(value, bool):
        return value

    raise ValueError(
        f"Unknown keep temperature history value: {value!r} if of type {type(value)!r}"
    )


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


@attr.s(slots=True)
class AdaptiveSimulatedAnnealing:
    """Implementation of adaptive simulated annealing looking for stacks based on the scoring function."""

    DEFAULT_LIMIT = 1000
    DEFAULT_COUNT = DEFAULT_LIMIT
    DEFAULT_BEAM_WIDTH = -1
    DEFAULT_LIMIT_LATEST_VERSIONS = -1

    pipeline = attr.ib(type=PipelineConfig, kw_only=True)
    project = attr.ib(type=Project, kw_only=True)
    hill_climbing = attr.ib(type=bool, default=False, kw_only=True)
    library_usage = attr.ib(
        type=Optional[Dict[str, Any]], default=attr.Factory(dict), kw_only=True
    )
    graph = attr.ib(type=GraphDatabase, kw_only=True)
    limit = attr.ib(type=int, kw_only=True, default=DEFAULT_LIMIT)
    count = attr.ib(type=int, kw_only=True, default=DEFAULT_COUNT)
    temperature_function = attr.ib(
        type=Callable[[int, float, int, int], float],
        kw_only=True,
        default=ASATemperatureFunction.exp,
    )
    seed = attr.ib(type=Optional[int], default=None, kw_only=True)
    beam_width = attr.ib(
        type=Optional[int],
        kw_only=True,
        default=DEFAULT_BEAM_WIDTH,
        converter=_beam_width,  # type: ignore
    )
    keep_temperature_history = attr.ib(
        type=bool, kw_only=True, default=None, converter=_keep_temperature_history
    )
    limit_latest_versions = attr.ib(
        type=Optional[int],
        kw_only=True,
        default=DEFAULT_LIMIT_LATEST_VERSIONS,
        converter=_limit_latest_versions,  # type: ignore
    )
    _solver = attr.ib(
        type=Optional[PythonPackageGraphSolver], kw_only=True, default=None
    )
    _context = attr.ib(type=Optional[Context], default=None, kw_only=True)
    _fully_specified_runtime_environment = attr.ib(
        type=Optional[bool], default=None, kw_only=True
    )
    _temperature_history = attr.ib(
        type=List[Tuple[float, bool, float, int]],
        default=attr.Factory(list),
        kw_only=True,
    )

    @graph.default
    def _graph_default(self) -> GraphDatabase:
        """Get default graph instance if no explicitly provided."""
        graph = GraphDatabase()
        graph.connect()
        return graph

    @property
    def context(self) -> Context:
        """Return context bound to this annealing."""
        if not self._context:
            raise ValueError("Context is not bound to annealing (has annealing run?)")

        return self._context

    @property
    def solver(self) -> PythonPackageGraphSolver:
        """Get solver instance - solver implemented on top of graph database."""
        if not self._solver:
            self._solver = PythonPackageGraphSolver(
                graph_db=self.graph,
                runtime_environment=self.project.runtime_environment,
            )

        return self._solver

    def get_temperature_history(self) -> List[Tuple[float, bool, float, int]]:
        """Retrieve temperature history from the last run."""
        return self._temperature_history

    @staticmethod
    def _compute_acceptance_probability(
        top_score: float, neighbour_score: float, temperature: float
    ) -> float:
        """Check the probability of acceptance the given solution to expansion."""
        if neighbour_score > top_score:
            return 1.0

        acceptance_probability = exp((neighbour_score - top_score) / temperature)
        _LOGGER.debug(
            "Acceptance probability for (top_score=%g, neighbour_score=%g, temperature=%g) = %g",
            top_score,
            neighbour_score,
            temperature,
            acceptance_probability,
        )
        return acceptance_probability

    def _is_fully_specified_runtime_environment(self) -> bool:
        """Pre-cache check if the given runtime environment is fully specified."""
        # TODO: move this to RuntimeEnvironment class
        if self._fully_specified_runtime_environment is None:
            runtime_environment = (
                self.project.runtime_environment.operating_system.name,
                self.project.runtime_environment.operating_system.version,
                self.project.runtime_environment.python_version,
            )
            self._fully_specified_runtime_environment = all(
                i is not None for i in runtime_environment
            )

            if not self._fully_specified_runtime_environment:
                _LOGGER.warning(
                    "Environment is not fully specified, pre-computed environment markers will not be "
                    "taken into account"
                )

        return self._fully_specified_runtime_environment

    def _resolve_direct_dependencies(
        self, *, with_devel: bool
    ) -> Dict[str, PackageVersion]:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        # It's important that solver preserves order in which packages were inserted.
        # This is also a requirement for running under Python3.6+!!!
        _LOGGER.info("Resolving direct dependencies")
        resolved_direct_dependencies: Dict[str, PackageVersion] = self.solver.solve(
            list(self.project.iter_dependencies(with_devel=with_devel)),
            graceful=True,
            all_versions=True,
        )

        if not resolved_direct_dependencies:
            raise CannotProduceStack("No direct dependencies were resolved")

        unresolved = []
        for package_name, package_versions in resolved_direct_dependencies.items():
            if not package_versions:
                # This means that there were found versions in the graph
                # database but none was matching the given version range.
                unresolved.append(package_name)

                error_msg = (
                    f"No versions were found for direct dependency {package_name!r}"
                )
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
                "Unable to resolve all direct dependencies, no versions "
                "were found for packages %s" % ", ".join(f"{i!r}" for i in unresolved),
                unresolved=unresolved,
            )

        # Now we are free to de-instantiate solver.
        del self._solver

        return resolved_direct_dependencies

    def _run_boots(self) -> None:
        """Run all boots bound to the current annealing run context."""
        for boot in self.pipeline.boots:
            try:
                boot.run()
            except Exception as exc:
                raise BootError(
                    f"Failed to run pipeline boot {boot.__class__.__name__!r}: {str(exc)}"
                ) from exc

    def _run_sieves(self, *package_versions: PackageVersion) -> List[PackageVersion]:
        """Run sieves on each package tuple."""
        accepted = []
        for package_version in package_versions:
            for sieve in self.pipeline.sieves:
                try:
                    sieve.run(package_version)
                except NotAcceptable as exc:
                    _LOGGER.debug(
                        "Sieve %r removed package %r: %s",
                        sieve.__class__.__name__,
                        package_version.to_tuple(),
                        str(exc),
                    )
                    break
                except Exception as exc:
                    raise SieveError(
                        f"Failed to run sieve {sieve.__class__.__name__!r} for "
                        f"Python package {package_version.to_tuple()!r}: {str(exc)}"
                    ) from exc
            else:
                accepted.append(package_version)

        return accepted

    def _run_steps(
        self, beam: Beam, state: State, *package_versions: PackageVersion
    ) -> None:
        """Run steps to score next state or filter out invalid steps."""
        # TODO: check if we have already dependency
        score = 0.0
        justification = []
        new_state = state.clone()
        package_version_tuples = [pv.to_dict() for pv in package_versions]
        for package_version in package_versions:
            for step in self.pipeline.steps:
                try:
                    step_result = step.run(state, package_version)
                except NotAcceptable as exc:
                    _LOGGER.debug(
                        "Step %r discarded addition of package %r in combination %r: %s",
                        step.__class__.__name__,
                        package_version.to_tuple(),
                        package_version_tuples,
                        str(exc),
                    )
                    return None
                except Exception as exc:
                    raise StepError(
                        f"Failed to run step {step.__class__.__name__!r} for Python package "
                        f"{package_version.to_tuple()!r}: {str(exc)}"
                    ) from exc

                if step_result:
                    score_addition, justification_addition = step_result
                    if score_addition is not None:
                        score += score_addition

                    if justification_addition is not None:
                        justification.extend(justification_addition)

            new_state.add_unresolved_dependency(package_version.to_tuple())

            new_state.score += score
            new_state.add_justification(justification)

        _LOGGER.debug(
            "Adding a new state with new entries %r: %r",
            package_version_tuples,
            new_state,
        )
        beam.add_state(new_state)

    def _run_strides(self, state: State) -> bool:
        """Run strides and check if the given state should be accepted."""
        for stride in self.pipeline.strides:
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
            try:
                wrap.run(state)
            except Exception as exc:
                raise WrapError(
                    f"Failed to run wrap {wrap.__class__.__name__!r} on a final step: {str(exc)}"
                ) from exc

    def _semver_sort_and_limit_latest_versions(
        self, *package_versions: PackageVersion
    ) -> List[PackageVersion]:
        """Sort package tuples based on version and apply latest version limit if configured so.

        Each package tuple has to be registered to the ASA context. Ordering is from the most recent version down to
        older versions.
        """
        sorted_package_versions = sorted(
            package_versions, key=lambda pv: pv.semantic_version, reverse=True
        )

        if self.limit_latest_versions is not None:
            _LOGGER.debug(
                "Limiting latest versions of packages to %d", self.limit_latest_versions
            )
            return list(sorted_package_versions)[:self.limit_latest_versions]

        return list(sorted_package_versions)

    def _prepare_initial_states(self, *, with_devel: bool) -> Beam:
        """Prepare initial states for simulated annealing.

        Initial states are all combinations of direct dependencies.
        """
        direct_dependencies = self._resolve_direct_dependencies(with_devel=with_devel)

        for direct_dependency_name, package_versions in direct_dependencies.items():
            # Register the given dependency first.
            for direct_dependency in package_versions:
                self.context.register_package_version(direct_dependency)

            package_versions = self._run_sieves(*package_versions)
            direct_dependencies[
                direct_dependency_name
            ] = self._semver_sort_and_limit_latest_versions(*package_versions)
            if not direct_dependencies[direct_dependency_name]:
                raise CannotProduceStack(
                    f"Cannot satisfy direct dependencies - direct dependencies "
                    f"of type {direct_dependency_name!r} were removed by pipeline sieves"
                )

        # Create an empty state which will be extended with packages based on step results. We know we have resolved
        # all the dependencies so start with beam which has just empty state and subsequently expand it based on
        # resolved direct dependencies.
        beam = Beam(width=self.beam_width)
        for package_versions in direct_dependencies.values():
            # If the beam is empty, create an initial state to be added to the beam if accepted by pipeline steps.
            # Even if number of initial states is more than beam.width, we create a list of current states explicitly
            # to make sure we iterate over all possible combinations. The beam trims down low scoring states
            # as expected.
            # As we sort dependencies based on versions, we know we add latest first.
            for state in list(beam.iter_states()) or [State()]:
                for package_version in package_versions:
                    self._run_steps(beam, state, package_version)

        return beam

    def _expand_state(self, beam: Beam, state: State) -> Optional[State]:
        """Expand the given state, generate new states respecting the pipeline configuration."""
        _, package_tuple = state.unresolved_dependencies.popitem()

        # Obtain extras for the given package. Extras are non-empty only for direct dependencies. If indirect
        # dependencies use extras, they don't need to be explicitly stated as solvers mark "hard" dependency on
        # the given package.
        package_version = self.context.get_package_version(package_tuple)
        extras = package_version.extras or [None]

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
            beam.add_state(state)
            return None

        all_dependencies: Dict[str, List[PackageVersion]] = {}
        for package_name, version in chain(*dependencies.values()):
            if self._is_fully_specified_runtime_environment():
                marker_evaluation_result = self.graph.get_python_environment_marker_evaluation_result(
                    *package_tuple,
                    dependency_name=package_name,
                    dependency_version=version,
                    os_name=self.project.runtime_environment.operating_system.name,
                    os_version=self.project.runtime_environment.operating_system.version,
                    python_version=self.project.runtime_environment.python_version,
                )

                if marker_evaluation_result is False:
                    _LOGGER.debug(
                        "Removing package %r from dependency graph as it will not be installed into "
                        "the given runtime environment",
                        package_tuple,
                    )
                    continue

            records = self.graph.get_python_package_version_records(
                package_name=package_name,
                package_version=version,
                index_url=None,  # Do cross-index resolving.
                os_name=self.project.runtime_environment.operating_system.name,
                os_version=self.project.runtime_environment.operating_system.version,
                python_version=self.project.runtime_environment.python_version,
            )

            for record in records:
                dependency_tuple = (
                    record["package_name"],
                    record["package_version"],
                    record["index_url"],
                )
                environment_marker = self.graph.get_python_environment_marker(
                    *package_tuple,
                    dependency_name=dependency_tuple[0],
                    dependency_version=dependency_tuple[1],
                    os_name=record["os_name"],
                    os_version=record["os_version"],
                    python_version=record["python_version"],
                )
                registered_package_version = self.context.register_package_tuple(
                    dependency_tuple,
                    develop=package_version.develop,  # Propagate develop flag from parent.
                    markers=environment_marker,
                    # A special value of `None' is used in the query to indicate the given direct
                    # dependency has no extra (see `GraphDatabase.get_depends_on' query for more info).
                    extras=[extra for extra in extras if extra is not None],
                )

                if dependency_tuple[0] not in all_dependencies:
                    all_dependencies[dependency_tuple[0]] = []

                all_dependencies[dependency_tuple[0]].append(registered_package_version)

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

        for dependency_name, package_versions in all_dependencies.items():
            package_versions = self._run_sieves(*package_versions)
            all_dependencies[
                dependency_name
            ] = self._semver_sort_and_limit_latest_versions(*package_versions)
            if not all_dependencies[dependency_name]:
                _LOGGER.debug(
                    "All dependencies of type %r were discarded by sieves, aborting creation of new states",
                    dependency_name,
                )
                return None

        for combination_package_versions in itertools_product(
            *all_dependencies.values()
        ):
            self._run_steps(beam, state, *combination_package_versions)

        return None

    def _heat_and_cool(
        self, *, with_devel: bool = True
    ) -> Generator[State, None, None]:
        """Heat and cool the steel - perform the actual adaptive simulated annealing."""
        self._run_boots()
        beam = self._prepare_initial_states(with_devel=with_devel)

        iteration = 0
        temperature = float(self.limit)
        while True:
            if self.context.accepted_final_states_count >= self.limit:
                _LOGGER.info(
                    "Reached limit of stacks to be generated - %r (limit is %r), stopping annealing "
                    "with the current beam size %d",
                    self.context.accepted_final_states_count,
                    self.limit,
                    beam.size,
                )
                break

            if beam.size == 0:
                _LOGGER.info("The beam is empty")
                break

            temperature = self.temperature_function(
                iteration,
                temperature,
                self.context.accepted_final_states_count,
                self.limit,
            )
            if temperature <= 0.0:
                _LOGGER.error(
                    "Iteration %r with temperature %g (k=%d)",
                    iteration,
                    temperature,
                    self.context.accepted_final_states_count,
                )
                return None

            # Expand highest promising by default if not acceptance probability.
            to_expand_state = beam.top()

            expanding_top = True
            acceptance_probability = 1.0
            if not self.hill_climbing and beam.size > 1:
                # Pick a random state to be expanded if accepted.
                probable_state_idx = random.randrange(1, beam.size)
                probable_state = beam.get(probable_state_idx)
                acceptance_probability = self._compute_acceptance_probability(
                    to_expand_state.score, probable_state.score, temperature
                )
                if acceptance_probability >= random.uniform(0.0, 1.0):
                    # Skip to probable state, do not use the top rated state.
                    _LOGGER.debug(
                        "Performing transition to neighbour state with score %g",
                        probable_state.score,
                    )
                    to_expand_state = probable_state
                    beam.pop(probable_state_idx)
                    expanding_top = False
                else:
                    # Remove highest rated which is going to be expanded in this round.
                    _LOGGER.debug(
                        "Keeping TOP rated state with score %g", to_expand_state.score
                    )
                    beam.pop()
            else:
                # If we have latest recommendations, try to expand the most recent version, always.
                _LOGGER.debug(
                    "Expanding TOP rated state with score %g", to_expand_state.score
                )
                beam.pop()

            iteration += 1
            if self.keep_temperature_history:
                self._temperature_history.append(
                    (
                        temperature,
                        expanding_top,
                        acceptance_probability,
                        self.context.accepted_final_states_count,
                    )
                )

            _LOGGER.debug(
                "Expanding state with score %g: %r",
                to_expand_state.score,
                to_expand_state,
            )
            final_state = self._expand_state(beam, to_expand_state)
            if final_state:
                if self._run_strides(final_state):
                    self._run_wraps(final_state)
                    self.context.inc_accepted_final_states_count()
                    yield final_state
                else:
                    self.context.inc_discarded_final_states_count()

    def _do_anneal_products(
        self, *, with_devel: bool = True
    ) -> Generator[State, None, None]:
        """Actually perform adaptive simulated annealing."""
        self._context = Context()
        self._temperature_history = []

        with Unit.assigned_context(self.context):
            try:
                yield from self._heat_and_cool(with_devel=with_devel)
            except EagerStopPipeline as exc:
                _LOGGER.info(f"Stopping pipeline eagerly as per request: %s", str(exc))

        _LOGGER.info(
            "Pipeline strides discarded %d and accepted %d final states in total",
            self.context.discarded_final_states_count,
            self.context.accepted_final_states_count,
        )

    def anneal_products(
        self, *, with_devel: bool = True
    ) -> Generator[Product, None, None]:
        """Run simulated annealing, produce product."""
        if self.count > self.limit:
            _LOGGER.warning(
                "Count (%d) is higher than limit (%d), setting count to %d",
                self.count,
                self.limit,
                self.limit,
            )
            self.count = self.limit

        # Use current time to make sure we have possibly reproducible runs - the seed is reported.
        seed = self.seed if self.seed is not None else int(time.time())
        stored_random_state = random.getstate()
        _LOGGER.info("Starting annealing with random seed set to %r", seed)
        random.seed(seed)

        try:
            start_time = time.monotonic()
            for final_state in self._do_anneal_products(with_devel=with_devel):
                product = Product.from_final_state(
                    graph=self.graph,
                    project=self.project,
                    context=self.context,
                    state=final_state,
                )
                yield product
            _LOGGER.info(
                "Annealing pipeline steps took %g seconds in total",
                time.monotonic() - start_time,
            )
        finally:
            # Restore random state to be nice to out users.
            random.setstate(stored_random_state)

    def anneal(self, *, with_devel: bool = True) -> Report:
        """Perform adaptive simulated annealing and report back a report of run."""
        report = Report(count=self.count, pipeline=self.pipeline)

        for product in self.anneal_products(with_devel=with_devel):
            report.add_product(product)

        if report.product_count() == 0:
            raise CannotProduceStack("No stack was produced")

        if self.keep_temperature_history:
            report.set_temperature_history(self._temperature_history)

        if self.context.stack_info:
            report.set_stack_info(self.context.stack_info)

        if self.context.advised_runtime_environment:
            report.set_advised_runtime_environment(
                self.context.advised_runtime_environment
            )

        return report

    @classmethod
    def compute_on_project(
        cls,
        *,
        beam_width: Optional[int] = None,
        count: int = DEFAULT_COUNT,
        graph: Optional[GraphDatabase] = None,
        library_usage: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        limit_latest_versions: Optional[int] = DEFAULT_LIMIT_LATEST_VERSIONS,
        project: Project,
        recommendation_type: RecommendationType,
        seed: Optional[int] = None,
        temperature_function: Callable[
            [int, float, int, int], float
        ] = ASATemperatureFunction.exp,
    ) -> Report:
        """Compute recommendations on the given project."""
        graph = graph or GraphDatabase()
        if not graph.is_connected():
            graph.connect()

        pipeline = PipelineBuilder.get_adviser_pipeline_config(
            recommendation_type=recommendation_type,
            project=project,
            library_usage=library_usage,
            graph=graph,
        )

        asa = cls(
            beam_width=beam_width,
            count=count,
            graph=graph,
            hill_climbing=recommendation_type == RecommendationType.LATEST,
            library_usage=library_usage,
            limit_latest_versions=limit_latest_versions,
            limit=limit,
            pipeline=pipeline,
            project=project,
            seed=seed,
            temperature_function=temperature_function,
        )

        return asa.anneal()
