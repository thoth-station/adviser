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

"""The main resolving algorithm working on top of states."""

import os
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
from typing import Iterator
import logging
from itertools import chain
import contextlib
import signal
import weakref

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
from .exceptions import SkipPackage
from .exceptions import SieveError
from .exceptions import StepError
from .exceptions import StrideError
from .exceptions import UnresolvedDependencies
from .exceptions import WrapError
from .exceptions import PipelineConfigurationError
from .exceptions import UserLockFileError
from .pipeline_builder import PipelineBuilder
from .pipeline_config import PipelineConfig
from .predictor import Predictor
from .product import Product
from .report import Report
from .solver import PythonPackageGraphSolver
from .state import State
from .unit import Unit
from .utils import log_once

import attr

_LOGGER = logging.getLogger(__name__)
_NO_EXTRAS = frozenset([None])


class _NoStateAdd(Exception):
    """An exception used internally to signalize no state addition."""


def _beam_width(value: Any) -> Optional[int]:
    """Set and convert beam width."""
    if value is None:
        return None

    if not isinstance(value, int):
        raise ValueError(f"Unknown type for beam width: {value!r} is of type {type(value)!r}")

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
        raise ValueError(f"Unknown type for limit latest versions: {value!r} is of type {type(value)!r}")

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
        raise ValueError(f"Unknown type for library usage: {value!r} is of type {type(value)!r}, a dict expected")

    return value


@contextlib.contextmanager
def _sigint_handler(resolver: "Resolver") -> Iterator[None]:
    """Register signal handler for resolver handling."""
    # noqa
    def handler(sig_num: int, _: Any) -> None:
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
    DEFAULT_LOG_FINAL_STATE_COUNT = 500
    DEFAULT_LOG_FINAL_STATE_TOP = False
    pipeline = attr.ib(type=PipelineConfig, kw_only=True)
    project = attr.ib(type=Project, kw_only=True)
    library_usage = attr.ib(type=Dict[str, Any], kw_only=True, converter=_library_usage)
    graph = attr.ib(type=GraphDatabase, kw_only=True)
    predictor = attr.ib(type=Predictor, kw_only=True)
    recommendation_type = attr.ib(type=Optional[RecommendationType], kw_only=True, default=None)
    decision_type = attr.ib(type=Optional[DecisionType], kw_only=True, default=None)
    limit = attr.ib(type=int, kw_only=True, default=DEFAULT_LIMIT)
    count = attr.ib(type=int, kw_only=True, default=DEFAULT_COUNT)
    beam_width = attr.ib(
        type=Optional[int], kw_only=True, default=DEFAULT_BEAM_WIDTH, converter=_beam_width,  # type: ignore
    )
    limit_latest_versions = attr.ib(
        type=Optional[int],
        kw_only=True,
        default=DEFAULT_LIMIT_LATEST_VERSIONS,
        converter=_limit_latest_versions,  # type: ignore
    )

    cli_parameters = attr.ib(type=Dict[str, Any], default=attr.Factory(dict), kw_only=True)
    stop_resolving = attr.ib(type=bool, default=False, kw_only=True)
    log_final_state_count = attr.ib(type=int, kw_only=True)

    _beam = attr.ib(type=Optional[Beam], kw_only=True, default=None)
    _solver = attr.ib(type=Optional[PythonPackageGraphSolver], kw_only=True, default=None)
    _context = attr.ib(type=Optional[Context], default=None, kw_only=True)

    _log_unresolved = attr.ib(type=Set[Tuple[str, str, str]], default=attr.Factory(set), kw_only=True)
    _log_unsolved = attr.ib(type=Set[str], default=attr.Factory(set), kw_only=True)
    _log_sieved = attr.ib(type=Set[str], default=attr.Factory(set), kw_only=True)
    _log_step_not_acceptable = attr.ib(type=Set[Tuple[str, str, str]], default=attr.Factory(set), kw_only=True)
    _log_no_intersected = attr.ib(type=Set[Tuple[Tuple[str, str, str], str]], default=attr.Factory(set), kw_only=True)

    @limit.validator
    @count.validator
    def _positive_int_validator(self, attribute: str, value: int) -> None:
        """Validate the given attribute - the given attribute should have a value of a positive integer."""
        if not isinstance(value, int):
            raise ValueError(f"Attribute {attribute!r} should be of type int, got {type(value)!r} instead")

        if value <= 0:
            raise ValueError(f"Value for attribute {attribute!r} should be a positive integer, got {value} instead")

    @log_final_state_count.default
    def _log_final_state_count_default(self) -> int:
        """Determine how often the pipeline should log about its progress."""
        # Log each 10% by default.
        return int(os.getenv("THOTH_ADVISER_LOG_FINAL_STATE_COUNT", self.limit // 10)) or 1

    @property
    def context(self) -> Context:
        """Retrieve context bound to the current resolver."""
        if self._context is None:
            raise ValueError("Context not assigned yes to the current resolver instance")

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
            self._beam = Beam(self.beam_width, keep_history=self.predictor.keep_history)

        return self._beam

    def _log_once_init(self) -> None:
        """Re-initialize log-once state."""
        self._log_unresolved.clear()
        self._log_unsolved.clear()
        self._log_sieved.clear()
        self._log_step_not_acceptable.clear()
        self._log_no_intersected.clear()

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
            cli_parameters=self.cli_parameters,
        )

    def _run_boots(self) -> None:
        """Run all boots bound to the current annealing run context."""
        for boot in self.pipeline.boots:
            _LOGGER.debug("Running boot %r", boot.__class__.__name__)
            try:
                boot.run()
            except NotAcceptable as exc:
                raise CannotProduceStack(f"Boot pipeline unit {boot.__class__.__name__} failed: {str(exc)!r}")
            except Exception as exc:
                raise BootError(f"Failed to run pipeline boot {boot.__class__.__name__!r}: {str(exc)}") from exc

    def _run_sieves(
        self, package_versions: List[PackageVersion], *, log_level: int = logging.DEBUG
    ) -> Generator[PackageVersion, None, None]:
        """Run sieves on each package tuple."""
        result = (pv for pv in package_versions)
        for sieve in self.pipeline.sieves:
            _LOGGER.debug("Running sieve %r", sieve.__class__.__name__)
            try:
                result = sieve.run(result)
            except SkipPackage:
                raise
            except NotAcceptable as exc:
                _LOGGER.log(
                    log_level, "Sieve %r removed packages %r: %s", sieve.__class__.__name__, str(exc),
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
        self,
        state: State,
        package_version: PackageVersion,
        unresolved_dependencies: Optional[Dict[str, List[Tuple[str, str, str]]]] = None,
        *,
        user_stack_scoring: bool = False,
        log_level: int = logging.DEBUG,
    ) -> Optional[State]:
        """Run steps and generate a new state."""
        package_version_tuple = package_version.to_tuple()

        multi_package_resolution = False
        if package_version.name in state.resolved_dependencies:
            if package_version_tuple != state.resolved_dependencies[package_version.name]:
                _LOGGER.error(
                    "Different package versions treated in the resolved dependencies, this assert "
                    "is not fatal but can lead to a wrong stack resolved (programming error)"
                )
            if user_stack_scoring:
                _LOGGER.error(
                    "Multi package resolution cannot occur when scoring user stacks, this assert "
                    "is not fatal but can lead to a wrong stack resolved (programming error)"
                )
            # We already have this dependency in stack, run steps that are
            # required to be run in such cases. The resolver logic called before guarantees there is
            # no version or package source clash.
            multi_package_resolution = True

        score_addition = 0.0
        justification_addition = []
        for step in self.pipeline.steps:
            _LOGGER.debug("Running step %r for %r", step.__class__.__name__, package_version_tuple)

            if multi_package_resolution and not step.MULTI_PACKAGE_RESOLUTIONS:
                _LOGGER.debug(
                    "Skipping running step %r - this step was already run for package %r "
                    "and the given step has no MULTI_PACKAGE_RESOLUTIONS flag set",
                    step.__class__.__name__,
                    package_version_tuple,
                )
                continue

            try:
                step_result = step.run(state, package_version)
            except NotAcceptable as exc:
                log_once(
                    _LOGGER,
                    self._log_step_not_acceptable,
                    package_version_tuple,
                    "Step %r discarded addition of package %r: %s",
                    step.__class__.__name__,
                    package_version_tuple,
                    str(exc),
                    level=log_level,
                )
                if not user_stack_scoring:
                    if package_version_tuple[0] not in state.unresolved_dependencies:
                        self.beam.remove(state)

                    self.predictor.set_reward_signal(state, package_version_tuple, math.nan)
                return None
            except Exception as exc:
                raise StepError(
                    f"Failed to run step {step.__class__.__name__!r} for Python package "
                    f"{package_version_tuple!r}: {str(exc)}"
                ) from exc

            if step_result:
                step_score_addition, step_justification_addition = step_result

                if step_score_addition is not None:
                    if math.isnan(step_score_addition):
                        raise StepError(f"Step {step.__class__.__name__} returned score which is not a number",)

                    if math.isinf(step_score_addition):
                        raise StepError(f"Step {step.__class__.__name__} returned score that is infinite",)

                    if step_score_addition > step.SCORE_MAX:
                        _LOGGER.warning(
                            "Step %r returned score higher than allowed (%g), normalizing to %g",
                            step.__class__.__name__,
                            step_score_addition,
                            step.SCORE_MAX,
                        )
                        step_score_addition = step.SCORE_MAX
                    elif step_score_addition < step.SCORE_MIN:
                        _LOGGER.warning(
                            "Step %r returned score lower than allowed (%g), normalizing to %g",
                            step.__class__.__name__,
                            step_score_addition,
                            step.SCORE_MIN,
                        )
                        step_score_addition = step.SCORE_MIN

                    score_addition += step_score_addition

                if step_justification_addition is not None:
                    justification_addition.extend(step_justification_addition)

        if state.unresolved_dependencies and package_version_tuple[0] in state.unresolved_dependencies:
            cloned_state = state.clone()
            weakref.finalize(cloned_state, self.predictor.finalize_state, id(cloned_state)).atexit = False
        else:
            # Optimization - reuse the old one as it would be discarded anyway.
            cloned_state = state
            if not user_stack_scoring and (
                score_addition != 0.0 or (not state.unresolved_dependencies and not unresolved_dependencies)
            ):
                self.beam.remove(cloned_state)

        if unresolved_dependencies:
            cloned_state.set_unresolved_dependencies(unresolved_dependencies)

        cloned_state.remove_unresolved_dependency_subtree(package_version_tuple[0])
        cloned_state.add_resolved_dependency(package_version_tuple)
        cloned_state.iteration = self.context.iteration
        cloned_state.add_justification(justification_addition)
        cloned_state.score += score_addition

        if not user_stack_scoring:
            if cloned_state.unresolved_dependencies:
                self.predictor.set_reward_signal(cloned_state, package_version_tuple, score_addition)
                if state is not cloned_state or score_addition != 0.0:
                    self.beam.add_state(cloned_state)
            else:
                self.predictor.set_reward_signal(cloned_state, package_version_tuple, math.inf)

        return cloned_state

    def _run_strides(self, state: State) -> bool:
        """Run strides and check if the given state should be accepted."""
        for stride in self.pipeline.strides:
            _LOGGER.debug("Running stride %r", stride.__class__.__name__)
            try:
                stride.run(state)
            except NotAcceptable as exc:
                _LOGGER.debug(
                    "Stride %r removed final state %r: %s", stride.__class__.__name__, state, str(exc),
                )
                return False
            except Exception as exc:
                raise StrideError(f"Failed to run stride {stride.__class__.__name__!r}: {str(exc)}") from exc

        return True

    def _run_wraps(self, state: State) -> None:
        """Run all wraps bound to the current annealing run context."""
        for wrap in self.pipeline.wraps:
            _LOGGER.debug("Running wrap %r", wrap.__class__.__name__)
            try:
                wrap.run(state)
            except Exception as exc:
                raise WrapError(f"Failed to run wrap {wrap.__class__.__name__!r} on a final step: {str(exc)}") from exc

    def _prepare_user_lock_file(self, *, with_devel: bool = True) -> None:
        """Perform operations on the user's lock file required before running the pipeline.

        One of the preparation steps is to assign index for each and every
        package present in the lock file so we know from where these packages
        were installed. Pipfile.lock does not need to state the python index
        used when installing dependencies.
        """
        sources = list(self.project.pipfile_lock.meta.sources.values())
        source_urls = {source.url for source in sources}

        enabled_indexes = set(self.graph.get_python_package_index_urls_all(enabled=True))
        if not source_urls.issubset(enabled_indexes):
            raise UserLockFileError(
                "User's lock file uses one or more indexes that are "
                f"not enabled: {', '.join(source_urls - enabled_indexes)}"
            )

        for package_version in self.project.iter_dependencies_locked(with_devel=with_devel):
            if package_version.index is not None:
                continue

            if len(sources) == 1:
                # Only one source configured, we can use it directly.
                package_version.index = sources[0]
            else:
                package_version_hashes = {h[len("sha256:") :] for h in package_version.hashes}

                # Assign index based on sources.
                for source in sources:
                    known_hashes = set(
                        self.graph.get_python_package_hashes_sha256(
                            package_version.name, package_version.locked_version, source.url,
                        )
                    )

                    if not known_hashes:
                        continue

                    if known_hashes & package_version_hashes:
                        _LOGGER.debug(
                            "Assigning index %r for package %r in version %r based on "
                            "the provenance database as index was not assigned in the lock file entry",
                            source.url,
                            package_version.name,
                            package_version.locked_version,
                        )
                        package_version.index = source
                        break
                else:
                    raise UserLockFileError(
                        f"Could not determine provenance of package {package_version.name!r} "
                        f"in version {package_version.locked_version!r}"
                    )

    def _maybe_score_user_lock_file(self, *, with_devel: bool = True) -> Optional[State]:
        """Score user's lock file submitted.

        As adviser is stochastic, it can explore different parts of the state
        space across different runs. To avoid this, we usually run adviser with
        a fixed random seed in deployments which preserves parts of the state
        space explored. However, if other parts of Thoth Knowledge graph changes (e.g.
        new observations, new package releases) we can, again, be
        exploring different parts of the state space. This function scores
        user's lockfile submitted first and then, in the adviser run itself, we
        try to find a better stack than the one user is using.
        """
        if not self.project.pipfile_lock:
            _LOGGER.info("Cannot score user's stack - no user's stack provided")
            return None

        self._prepare_user_lock_file(with_devel=True)

        skipped_packages: List[PackageVersion] = []
        _LOGGER.info("Scoring user's stack based on the lock file submitted")
        for package_version in self.project.iter_dependencies_locked(with_devel=with_devel):
            # First time seen, register this package for pipeline units.
            self.context.register_package_version(package_version)
            try:
                package_version = list(self._run_sieves([package_version], log_level=logging.INFO))
            except SkipPackage as exc:
                skipped_packages.append(package_version)
                _LOGGER.debug("Package %r skipped by sieves: %s", package_version.name, str(exc))
                continue

            if not package_version:
                _LOGGER.info("User's stack was removed based on sieves")
                return None

        for skipped_package in skipped_packages:
            if skipped_package.develop:
                package_lock_listing = self.project.pipfile_lock.dev_packages
                package_listing = self.project.pipfile.dev_packages
            else:
                package_lock_listing = self.project.pipfile_lock.packages
                package_listing = self.project.pipfile.packages

            try:
                package_lock_listing.packages.pop(skipped_package.name)
            except KeyError:
                _LOGGER.exception("Tried to skip a package which is not part of the application stack")
                continue

            # If the package is not direct dependency, do no-op with pop.
            package_listing.packages.pop(skipped_package.name, None)

        state = State()
        for package_version in self.project.iter_dependencies_locked(with_devel=with_devel):
            if not self._run_steps(state, package_version, user_stack_scoring=True, log_level=logging.INFO):
                _LOGGER.info("User's stack was removed based on steps")
                return None

        state.add_justification(
            [
                {
                    "type": "INFO",
                    "message": "Score of the supplied lock file is the highest possible \
                according to the current knowledge in Thoth and the parameters used to solve the stack.",
                }
            ]
        )
        self._run_wraps(state)
        self.beam.add_state(state)
        _LOGGER.info("User's software stack has a score of %g", state.score)
        return state

    def _resolve_direct_dependencies(self, *, with_devel: bool) -> Dict[str, List[PackageVersion]]:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        # It's important that solver preserves order in which packages were inserted.
        # This is also a requirement for running under Python3.6+!!!
        _LOGGER.info("Resolving direct dependencies")
        resolved_direct_dependencies: Dict[str, List[PackageVersion]] = self.solver.solve(
            sorted(self.project.iter_dependencies(with_devel=with_devel), key=lambda p: p.name,), graceful=True,
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
                    error_msg += f" for Python in version {runtime_environment.python_version!r}"

                if runtime_environment.platform:
                    error_msg += f" using platform {runtime_environment.platform!r}"

                _LOGGER.warning(error_msg)
                continue

            _LOGGER.info(
                "Found direct dependency %r with version specification %r",
                package_version.name,
                package_version.version,
            )

        if unresolved:
            raise UnresolvedDependencies("Unable to resolve all direct dependencies", unresolved=unresolved)

        # Now we are free to de-instantiate solver.
        del self._solver

        return resolved_direct_dependencies

    def _prepare_initial_state(self, *, with_devel: bool) -> None:
        """Prepare initial state for resolver."""
        direct_dependencies = self._resolve_direct_dependencies(with_devel=with_devel)

        if not direct_dependencies:
            raise CannotProduceStack("No direct dependencies found")

        skipped_packages: List[str] = []
        for direct_dependency_name, package_versions in direct_dependencies.items():
            # Register the given dependency first.
            for direct_dependency in package_versions:
                self.context.register_package_version(direct_dependency)

            package_versions.sort(key=lambda pv: pv.semantic_version, reverse=True)
            try:
                package_versions = list(self._run_sieves(package_versions))
            except SkipPackage as exc:
                skipped_packages.append(direct_dependency_name)
                _LOGGER.debug("Package %r skipped by sieves: %s", direct_dependency_name, str(exc))
                continue

            if not package_versions:
                raise CannotProduceStack(
                    f"Cannot satisfy direct dependencies - direct dependencies "
                    f"of type {direct_dependency_name!r} were removed by pipeline sieves"
                )

            if self.limit_latest_versions:
                direct_dependencies[direct_dependency_name] = package_versions[: self.limit_latest_versions]
            else:
                direct_dependencies[direct_dependency_name] = package_versions

        for direct_dependency_name in skipped_packages:
            # Remove separately due to dictionary size changes during dict iterations in items. Also, this loop
            # should occur rarely so it's more efficient to do it this way instead of creating a swallow copy of
            # dict during iteration.
            direct_dependencies.pop(direct_dependency_name)

        # Create an initial state which is made out of all the direct dependencies (kept as unresolved) in
        # resolved versions.
        self.beam.wipe()
        state = State.from_direct_dependencies(direct_dependencies)
        weakref.finalize(state, self.predictor.finalize_state, id(state)).atexit = False
        self.beam.add_state(state)

    def _expand_state(self, state: State, package_tuple: Tuple[str, str, str]) -> Optional[State]:
        """Expand the given state, generate new states respecting the pipeline configuration.

        This function retrieves dependencies of the expanded state. The decision tree:

          - is package_tuple resolved?
            |
            -> yes -> proceed to self._expand_state_add_dependencies (regardless there are any dependencies)
            |
            -> no -> are there any other dependencies of the same type which could be resolved?
                  |
                  -> yes -> keep the state in beam
                  |
                  -> no -> state needs to be removed as dependencies cannot be satisfied.

        Returns None if package_tuple was not resolved, otherwise the newly created state out of state (can be
        same object allocated based on memory optimizations in self._expand_state_add_dependencies.
        """
        _LOGGER.debug("Expanding state by resolving %r", package_tuple)
        # Obtain extras for the given package. Extras are non-empty only for direct dependencies. If indirect
        # dependencies use extras, they don't need to be explicitly stated as solvers mark "hard" dependency on
        # the given package.
        package_version: PackageVersion = self.context.get_package_version(package_tuple, graceful=False)

        state.remove_unresolved_dependency(package_tuple)

        extras = _NO_EXTRAS
        if package_version.extras:
            extras = frozenset(list(package_version.extras) + [None])

        try:
            dependencies = self.graph.get_depends_on(
                *package_tuple,
                os_name=self.project.runtime_environment.operating_system.name,
                os_version=self.project.runtime_environment.operating_system.version,
                python_version=self.project.runtime_environment.python_version,
                extras=extras,
                marker_evaluation_result=True if self.project.runtime_environment.is_fully_specified() else None,
                is_missing=False,
            )
        except NotFoundError:
            log_once(
                _LOGGER,
                self._log_unresolved,
                package_tuple,
                "Dependency %r is not yet resolved, trying different resolution path...",
                package_tuple,
            )

            if package_tuple[0] not in state.unresolved_dependencies:
                # There are no dependencies of the same type, remove the state from the beam.
                self.beam.remove(state)

            self.predictor.set_reward_signal(state, package_tuple, math.nan)
            return None

        return self._expand_state_add_dependencies(
            state=state, package_version=package_version, dependencies=list(chain(*dependencies.values())),
        )

    def _expand_state_add_dependencies(
        self, state: State, package_version: PackageVersion, dependencies: List[Tuple[str, str]],
    ) -> Optional[State]:
        """Create new state out of existing ones based on dependencies if necessary.

        This function ensures there are run steps on the newly added dependency. Prior that,
        there are obtained dependencies solved for the given runtime environment.

          - are all dependencies of a type were solved in the given runtime environment
            |
            -> no - the transition is not accepted, predictor receives NaN reward signal
                  |
                   -> is there any dependency of the same type as package_version?
                       |
                       -> yes - keep state in the beam
                       |
                       -> no - remove state from the beam as we cannot satisfy all the dependencies
            -> yes - are these dependencies already shared with dependencies marked as resolved in the state?
                   |
                   -> no - sort dependencies and run sieves
                          |
                           -> sieves removed all dependencies?
                              |
                              -> yes - is there any dependency of the same type as package_version?
                                     |
                                     -> yes - keep state in the beam
                                     |
                                     -> no - remove state from the beam as we cannot satisfy all the dependencies
                              -> no - run steps
                   -> yes - computed intersection is empty?
                          |
                          -> yes - is there any dependency of the same type as package_version?
                                 |
                                 -> yes - keep state in the beam
                                 |
                                 -> no - remove state from the beam as we cannot satisfy all the dependencies
                          -> no - sort dependencies and run sieves
                                 |
                                  -> sieves removed all dependencies?
                                     |
                                     -> yes - is there any dependency of the same type as package_version?
                                            |
                                            -> yes - keep state in the beam
                                            |
                                            -> no - remove state from the beam as we cannot satisfy all the dependencies
                                     -> no - run steps

        """
        _LOGGER.debug("Expanding state with dependencies based on packages solved in software environments")

        package_tuple = package_version.to_tuple()
        all_dependencies: Dict[str, List[Tuple[str, str, str]]] = {}
        for dependency_name, dependency_version in dependencies:
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
            all_dependencies.setdefault(dependency_name, [])
            resolved_dependency_tuple = state.resolved_dependencies.get(dependency_name)
            if resolved_dependency_tuple and resolved_dependency_tuple[1] != dependency_version:
                _LOGGER.debug(
                    "Skipping adding dependency %r in version %r as this dependency is already present "
                    "in state in a different version: %r",
                    dependency_name,
                    dependency_version,
                    state.resolved_dependencies[dependency_name],
                )
                continue

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
            dependency_name for dependency_name, package_versions in all_dependencies.items() if not package_versions
        ]
        if unsolved:
            # We don't have all dependencies of package_tuple solved for the given environment, give up here.
            for unsolved_item in unsolved:
                log_once(
                    _LOGGER,
                    self._log_unsolved,
                    unsolved_item,
                    "No solved releases found for %r which would satisfy version requirements of %r, "
                    "trying different resolution path...",
                    unsolved_item,
                    package_tuple,
                )

            if package_tuple[0] not in state.unresolved_dependencies:
                # There are no dependencies of the same type that could lead this state to a final state, remove
                # the state from the beam.
                self.beam.remove(state)

            self.predictor.set_reward_signal(state, package_tuple, math.nan)
            return None

        skipped_packages: List[str] = []
        dependency_tuples: Union[List[Any], Set[Any]]  # indicate that dependency_tuples type change during iteration
        for dependency_name, dependency_tuples in all_dependencies.items():
            if dependency_name in state.unresolved_dependencies:
                # We have shared dependencies - let's compute intersection and use intersected dependencies if
                # we can satisfy them. No need to run sieves as they were run in previous iterations on the
                # intersected dependencies.
                dependency_tuples = set(dependency_tuples).intersection(
                    state.unresolved_dependencies[dependency_name].values()
                )

                if not dependency_tuples:
                    log_once(
                        _LOGGER,
                        self._log_no_intersected,
                        (package_tuple, dependency_name),
                        "No intersected dependencies for package %r found when resolving %r, "
                        "trying different resolution path...",
                        dependency_name,
                        package_tuple,
                    )

                    if package_tuple[0] not in state.unresolved_dependencies:
                        # No other candidate of same package type as package_tuple that would lead
                        # to a final state from this state.
                        self.beam.remove(state)

                    self.predictor.set_reward_signal(state, package_tuple, math.nan)
                    return None

                # Check intersection with the already resolved ones.
                resolved_dependency = state.resolved_dependencies.get(dependency_name)
                if resolved_dependency is not None:
                    if resolved_dependency not in dependency_tuples:
                        if package_tuple[0] not in state.unresolved_dependencies:
                            self.beam.remove(state)

                        self.predictor.set_reward_signal(state, package_tuple, math.nan)
                        return None

                    all_dependencies[dependency_name] = [resolved_dependency]
                    continue

                all_dependencies[dependency_name] = sorted(
                    dependency_tuples,
                    key=lambda d: self.context.get_package_version(d).semantic_version,  # type: ignore
                    reverse=True,
                )
                continue

            # Check intersection with the already resolved ones.
            resolved_dependency = state.resolved_dependencies.get(dependency_name)
            if resolved_dependency is not None:
                if resolved_dependency not in dependency_tuples:
                    if package_tuple[0] not in state.unresolved_dependencies:
                        self.beam.remove(state)

                    self.predictor.set_reward_signal(state, package_tuple, math.nan)
                    return None

                # We have already run sieves for this one.
                all_dependencies[dependency_name] = [resolved_dependency]
                continue

            package_versions = [self.context.get_package_version(d) for d in dependency_tuples]
            package_versions.sort(key=lambda pv: pv.semantic_version, reverse=True)  # type: ignore
            try:
                package_versions = list(self._run_sieves(package_versions))
            except SkipPackage as exc:
                # This will probably happen occasionally. Let's maintain a separate list for this.
                skipped_packages.append(dependency_name)
                _LOGGER.debug("Package %r skipped by sieves: %s", dependency_name, str(exc))
                continue

            if not package_versions:
                log_once(
                    _LOGGER,
                    self._log_sieved,
                    dependency_name,
                    "All dependencies of type %r were discarded by resolver pipeline sieves, "
                    "trying different resolution path...",
                    dependency_name,
                )

                if package_tuple[0] not in state.unresolved_dependencies:
                    self.beam.remove(state)

                self.predictor.set_reward_signal(state, package_tuple, math.nan)
                return None

            if self.limit_latest_versions:
                all_dependencies[dependency_name] = [
                    pv.to_tuple() for pv in package_versions[: self.limit_latest_versions]  # type: ignore
                ]
            else:
                all_dependencies[dependency_name] = [pv.to_tuple() for pv in package_versions]  # type: ignore

        for skipped_package in skipped_packages:
            all_dependencies.pop(skipped_package)

        return self._run_steps(state, package_version, all_dependencies)

    def _do_resolve_states(
        self, *, with_devel: bool = True, user_stack_scoring: bool = True,
    ) -> Generator[State, None, None]:
        """Actually perform states resolution."""
        self._log_once_init()
        self._run_boots()

        if not self.project.runtime_environment.is_fully_specified():
            _LOGGER.warning(
                "Environment is not fully specified, pre-computed environment markers will not be " "taken into account"
            )

        if user_stack_scoring:
            try:
                user_stack = self._maybe_score_user_lock_file(with_devel=with_devel)
            except UserLockFileError as exc:
                _LOGGER.warning("Failed to score user's lock file: %s", str(exc))
            except Exception:
                _LOGGER.exception("Failed to score supplied user stack, the error is not fatal")
            else:
                if user_stack:
                    yield user_stack

        self._prepare_initial_state(with_devel=with_devel)

        _LOGGER.info("Hold tight, Thoth is computing recommendations for your application...")

        self.context.iteration = 0
        self.stop_resolving = False
        with _sigint_handler(self):
            while not self.stop_resolving:
                if self.context.accepted_final_states_count >= self.limit:
                    _LOGGER.info(
                        "Reached limit of stacks to be generated (limit is %r), stopping resolver "
                        "with the current beam size %d in iteration %d",
                        self.limit,
                        self.beam.size,
                        self.context.iteration,
                    )
                    break

                if self.beam.size == 0:
                    _LOGGER.warning(
                        "No more possible paths found for resolution, terminating resolver in iteration %d",
                        self.context.iteration,
                    )
                    break

                self.beam.new_iteration()
                self.context.iteration += 1

                state, unresolved_package_tuple = self.predictor.run()

                _LOGGER.debug(
                    "Resolving package %r in state with score %g: %r", unresolved_package_tuple, state.score, state,
                )
                state_returned = self._expand_state(state, unresolved_package_tuple)
                if state_returned is not None and not state_returned.unresolved_dependencies:
                    # A final state produced by the pipeline.
                    if self._run_strides(state_returned):
                        self._run_wraps(state_returned)
                        self.context.accepted_final_states_count += 1
                        self.context.register_accepted_final_state(state_returned)
                        yield state_returned
                    else:
                        self.context.discarded_final_states_count += 1

        if self.stop_resolving:
            _LOGGER.warning(
                "Resolving stopped with the current beam size %d as the allocated CPU time was exhausted",
                self.beam.size,
            )

    def _do_resolve_products(
        self, *, with_devel: bool = True, user_stack_scoring: bool = True,
    ) -> Generator[Product, None, None]:
        """Resolve raw products as produced by this resolver pipeline."""
        if self.count > self.limit:
            _LOGGER.warning(
                "Count (%d) is higher than limit (%d), setting count to %d", self.count, self.limit, self.limit,
            )
            self.count = self.limit

        self.predictor.pre_run()
        self.pipeline.call_pre_run()

        start_time = time.monotonic()
        try:
            for final_state in self._do_resolve_states(with_devel=with_devel, user_stack_scoring=user_stack_scoring):
                _LOGGER.debug(
                    "Pipeline reached a new final state, yielding pipeline product " "with a score of %g - %d/%d",
                    final_state.score,
                    self.context.accepted_final_states_count,
                    self.context.limit,
                )

                if (self.context.accepted_final_states_count - 1) % self.log_final_state_count == 0:
                    _LOGGER.info(
                        "Pipeline reached %d final states out of %d requested in iteration %d "
                        "(pipeline pace %.02f stacks/second), top rated software stack has a score of %s",
                        self.context.accepted_final_states_count,
                        self.context.limit,
                        self.context.iteration,
                        self.context.accepted_final_states_count / (time.monotonic() - start_time),
                        self.beam.max().score if self.beam.size > 0 else "N/A",
                    )

                product = Product.from_final_state(context=self.context, state=final_state)
                yield product
                del final_state
        except EagerStopPipeline as exc:
            _LOGGER.info("Stopping pipeline eagerly as per request: %s", str(exc))

        duration = time.monotonic() - start_time
        _LOGGER.info(
            "Resolver took %g seconds in total, pipeline speed %g stacks/second",
            duration,
            self.context.accepted_final_states_count / duration,
        )

        _LOGGER.info(
            "Pipeline strides discarded %d and accepted %d final states in total",
            self.context.discarded_final_states_count,
            self.context.accepted_final_states_count,
        )

        self.predictor.post_run()
        self.pipeline.call_post_run()

    def resolve_products(
        self, *, with_devel: bool = True, user_stack_scoring: bool = True
    ) -> Generator[Product, None, None]:
        """Resolve raw products as produced by this resolver pipeline."""
        self._init_context()
        with Unit.assigned_context(self.context), self.predictor.assigned_context(self.context):
            yield from self._do_resolve_products(with_devel=with_devel, user_stack_scoring=user_stack_scoring)

    def resolve(self, *, with_devel: bool = True, user_stack_scoring: bool = True) -> Report:
        """Resolve software stacks and return resolver report."""
        report = Report(count=self.count, pipeline=self.pipeline)

        self._init_context()
        with Unit.assigned_context(self.context), self.predictor.assigned_context(self.context):
            for product in self._do_resolve_products(with_devel=with_devel, user_stack_scoring=user_stack_scoring):
                report.add_product(product)

            if report.product_count() == 0:
                raise CannotProduceStack(
                    "Resolver did not find any stack that would satisfy "
                    "requirements and stack characteristics given the time allocated"
                )

            if self.context.stack_info:
                report.set_stack_info(self.context.stack_info)

            self.predictor.post_run_report(report)
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
        cli_parameters: Optional[Dict[str, Any]] = None,
    ) -> "Resolver":
        """Get instance of resolver based on the project given to recommend software stacks."""
        graph = graph or GraphDatabase()
        if not graph.is_connected():
            graph.connect()

        if pipeline_config is None:
            pipeline = PipelineBuilder.get_adviser_pipeline_config(
                recommendation_type=recommendation_type, project=project, library_usage=library_usage, graph=graph,
            )
        else:
            if isinstance(pipeline_config, PipelineConfig):
                pipeline = pipeline_config
            elif isinstance(pipeline_config, dict):
                pipeline = PipelineBuilder.from_dict(pipeline_config)
            else:
                raise PipelineConfigurationError(f"Unknown pipeline configuration type: {type(pipeline_config)!r}")

        return cls(
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
            cli_parameters=cli_parameters or {},
        )

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
        cli_parameters: Optional[Dict[str, Any]] = None,
    ) -> "Resolver":
        """Get instance of resolver based on the project given to run dependency monkey."""
        graph = graph or GraphDatabase()
        if not graph.is_connected():
            graph.connect()

        if pipeline_config is None:
            pipeline = PipelineBuilder.get_dependency_monkey_pipeline_config(
                decision_type=decision_type, graph=graph, project=project, library_usage=library_usage,
            )
        else:
            if isinstance(pipeline_config, PipelineConfig):
                pipeline = pipeline_config
            elif isinstance(pipeline_config, dict):
                pipeline = PipelineBuilder.from_dict(pipeline_config)
            else:
                raise PipelineConfigurationError(f"Unknown pipeline configuration type: {type(pipeline_config)!r}")

        return cls(
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
            cli_parameters=cli_parameters or {},
        )
