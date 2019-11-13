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
from typing import Generator
from typing import Dict
from typing import Any
from typing import Optional
from typing import List
import logging
from itertools import chain
from itertools import product as itertools_product

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


@attr.s(slots=True)
class Resolver:
    """Resolver for resolving software stacks using pipeline configuration and a predictor."""

    DEFAULT_LIMIT = 10000
    DEFAULT_COUNT = DEFAULT_LIMIT
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

    _solver = attr.ib(
        type=Optional[PythonPackageGraphSolver], kw_only=True, default=None
    )
    _context = attr.ib(type=Optional[Context], default=None, kw_only=True)

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
            return list(sorted_package_versions)[: self.limit_latest_versions]

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
            if self.project.runtime_environment.is_fully_specified():
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

    def _do_resolve_states(
        self, *, with_devel: bool = True
    ) -> Generator[State, None, None]:
        """Actually perform adaptive simulated annealing."""
        self._run_boots()
        beam = self._prepare_initial_states(with_devel=with_devel)

        self.context.iteration = 0
        while True:
            if self.context.accepted_final_states_count >= self.limit:
                _LOGGER.info(
                    "Reached limit of stacks to be generated - %r (limit is %r), stopping resolver "
                    "with the current beam size %d",
                    self.context.accepted_final_states_count,
                    self.limit,
                    beam.size,
                )
                break

            if beam.size == 0:
                _LOGGER.info("The beam is empty")
                break

            self.context.iteration += 1

            state_idx = self.predictor.run(self.context, beam)
            to_expand_state = beam.pop(state_idx)

            _LOGGER.debug(
                "Expanding state with score %g at index %d: %r",
                to_expand_state.score,
                state_idx,
                to_expand_state,
            )
            final_state = self._expand_state(beam, to_expand_state)
            if final_state:
                if self._run_strides(final_state):
                    self._run_wraps(final_state)
                    self.context.accepted_final_states_count += 1
                    yield final_state
                else:
                    self.context.discarded_final_states_count += 1

    def resolve_products(
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
                    "Pipeline created reached a new final state, yielding pipeline product with score %g",
                    final_state.score
                )
                product = Product.from_final_state(
                    graph=self.graph,
                    project=self.project,
                    context=self.context,
                    state=final_state,
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

    def resolve(self, *, with_devel: bool = True) -> Report:
        """Resolve software stacks and return resolver report."""
        report = Report(count=self.count, pipeline=self.pipeline)

        self._context = Context(
            project=self.project,
            graph=self.graph,
            library_usage=self.library_usage,
            limit=self.limit,
            count=self.count,
            recommendation_type=self.recommendation_type,
            decision_type=self.decision_type,
        )

        with Unit.assigned_context(self.context):
            for product in self.resolve_products(with_devel=with_devel):
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
    ) -> "Resolver":
        """Get instance of resolver based on the project given to recommend software stacks."""
        graph = graph or GraphDatabase()
        if not graph.is_connected():
            graph.connect()

        pipeline = PipelineBuilder.get_adviser_pipeline_config(
            recommendation_type=recommendation_type,
            project=project,
            library_usage=library_usage,
            graph=graph,
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
    ) -> "Resolver":
        """Get instance of resolver based on the project given to run dependency monkey."""
        graph = graph or GraphDatabase()
        if not graph.is_connected():
            graph.connect()

        pipeline = PipelineBuilder.get_dependency_monkey_pipeline_config(
            decision_type=decision_type,
            graph=graph,
            project=project,
            library_usage=library_usage,
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
