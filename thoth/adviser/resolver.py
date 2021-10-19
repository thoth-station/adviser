#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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
from typing import TYPE_CHECKING
import logging
from itertools import chain
import contextlib
import signal
import weakref
import heapq

import attr
from thoth.common import get_justification_link as jl
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
from .exceptions import NoHistoryKept
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

if TYPE_CHECKING:
    import matplotlib
    from .prescription import Prescription  # noqa: F401


_LOGGER = logging.getLogger(__name__)
_NO_EXTRAS = frozenset([None])


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

    pipeline = attr.ib(type=PipelineConfig, kw_only=True)
    project = attr.ib(type=Project, kw_only=True)
    library_usage = attr.ib(type=Dict[str, Any], kw_only=True, converter=_library_usage)
    graph = attr.ib(type=GraphDatabase, kw_only=True)
    predictor = attr.ib(type=Predictor, kw_only=True)
    labels = attr.ib(type=Dict[str, str], kw_only=True, default=attr.Factory(dict))
    recommendation_type = attr.ib(type=Optional[RecommendationType], kw_only=True, default=None)
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

    prescription = attr.ib(type=Optional["Prescription"], default=None, kw_only=True)
    cli_parameters = attr.ib(type=Dict[str, Any], default=attr.Factory(dict), kw_only=True)
    stop_resolving = attr.ib(type=bool, default=False, kw_only=True)
    log_iteration = attr.ib(type=int, kw_only=True, default=int(os.getenv("THOTH_ADVISER_LOG_ITERATION", 7500)))

    _beam = attr.ib(type=Optional[Beam], kw_only=True, default=None)
    _solver = attr.ib(type=Optional[PythonPackageGraphSolver], kw_only=True, default=None)
    _context = attr.ib(type=Optional[Context], default=None, kw_only=True)
    _history = attr.ib(type=List[Optional[float]], factory=list, init=False)
    _history_max = attr.ib(type=List[Optional[float]], factory=list, init=False)

    _log_unresolved = attr.ib(type=Set[Tuple[str, str, str]], default=attr.Factory(set), kw_only=True)
    _log_unsolved = attr.ib(type=Set[str], default=attr.Factory(set), kw_only=True)
    _log_sieved = attr.ib(type=Set[str], default=attr.Factory(set), kw_only=True)
    _log_step_skip_package = attr.ib(type=Set[Tuple[str, str, str]], default=attr.Factory(set), kw_only=True)
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

    @property
    def context(self) -> Context:
        """Retrieve context bound to the current resolver."""
        if self._context is None:
            raise ValueError("Context not assigned yet to the current resolver instance")

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
            labels=self.labels,
            library_usage=self.library_usage,
            limit=self.limit,
            count=self.count,
            beam=self.beam,
            recommendation_type=self.recommendation_type,
            decision_type=self.decision_type,
            prescription=self.prescription,
            cli_parameters=self.cli_parameters,
        )

    def _run_boots(self, *, with_devel: bool = True) -> None:
        """Run all boots bound to the current run context."""
        package_boots = []
        for package_version in self.project.iter_dependencies(with_devel=with_devel):
            package_boots.extend(self.pipeline.boots_dict.get(package_version.name, []))

        for boot in chain(package_boots, self.pipeline.boots_dict.get(None, [])):
            _LOGGER.debug("Running boot %r", boot.name)
            boot.unit_run = True
            try:
                boot.run()
            except NotAcceptable as exc:
                msg = f"Boot pipeline unit {boot.name} failed: {str(exc)}"
                raise CannotProduceStack(msg, stack_info=self.context.stack_info)
            except Exception as exc:
                raise BootError(f"Failed to run pipeline boot {boot.name!r}: {str(exc)}") from exc

    def _run_sieves(
        self, package_versions: List[PackageVersion], *, log_level: int = logging.DEBUG
    ) -> Generator[PackageVersion, None, None]:
        """Run sieves on each package tuple."""
        result = (pv for pv in package_versions)
        if package_versions:
            for sieve in chain(
                self.pipeline.sieves_dict.get(package_versions[0].name, []), self.pipeline.sieves_dict.get(None, [])
            ):
                _LOGGER.debug("Running sieve %r", sieve.name)
                sieve.unit_run = True
                try:
                    result = sieve.run(result)
                except SkipPackage:
                    raise
                except NotAcceptable as exc:
                    _LOGGER.log(
                        log_level,
                        "Sieve %r removed packages %r: %s",
                        sieve.name,
                        exc,
                    )
                    result = []  # type: ignore
                    break
                except Exception as exc:
                    raise SieveError(
                        f"Failed to run sieve {sieve.name!r} for "
                        f"Python packages {[pv.to_tuple() for pv in package_versions]}: {str(exc)}"
                    ) from exc

        yield from result

    def _run_steps(
        self,
        state: State,
        package_version: PackageVersion,
        unresolved_dependencies: Optional[Dict[str, List[Tuple[str, str, str]]]] = None,
        newly_added: Optional[List[Tuple[str, str, str]]] = None,
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
        skip_package = False
        step_result = None
        for step in chain(
            self.pipeline.steps_dict.get(package_version.name, []), self.pipeline.steps_dict.get(None, [])
        ):
            _LOGGER.debug("Running step %r for %r", step.name, package_version_tuple)
            step.unit_run = True

            if multi_package_resolution and not step.configuration["multi_package_resolution"]:
                _LOGGER.debug(
                    "Skipping running step %r - this step was already run for package %r "
                    "and the given step has no multi_package_resolution flag set",
                    step.name,
                    package_version_tuple,
                )
                continue

            try:
                step_result = step.run(state, package_version)
            except SkipPackage as exc:
                # This should be fine also for user-stacks steps. The recommendation engine will compute alternatives.
                log_once(
                    _LOGGER,
                    self._log_step_skip_package,
                    package_version_tuple,
                    "Step %r discarded addition of package %r: %s",
                    step.name,
                    package_version_tuple,
                    exc,
                    level=log_level,
                )
                skip_package = True
                break
            except NotAcceptable as exc:
                log_once(
                    _LOGGER,
                    self._log_step_not_acceptable,
                    package_version_tuple,
                    "Step %r discarded addition of package %r: %s",
                    step.name,
                    package_version_tuple,
                    exc,
                    level=log_level,
                )
                if not user_stack_scoring:
                    if package_version_tuple[0] not in state.unresolved_dependencies:
                        self.beam.remove(state)

                    self.predictor.set_reward_signal(state, package_version_tuple, math.nan)
                return None
            except Exception as exc:
                raise StepError(
                    f"Failed to run step {step.name!r} for Python package {package_version_tuple!r}: {str(exc)}"
                ) from exc

            if step_result:
                step_score_addition, step_justification_addition = step_result

                if step_score_addition is not None:
                    if math.isnan(step_score_addition):
                        raise StepError(
                            f"Step {step.name} returned score which is not a number",
                        )

                    if math.isinf(step_score_addition):
                        raise StepError(
                            f"Step {step.name} returned score that is infinite",
                        )

                    if step_score_addition > step.SCORE_MAX:
                        _LOGGER.warning(
                            "Step %r returned score higher than allowed (%g), normalizing to %g",
                            step.name,
                            step_score_addition,
                            step.SCORE_MAX,
                        )
                        step_score_addition = step.SCORE_MAX
                    elif step_score_addition < step.SCORE_MIN:
                        _LOGGER.warning(
                            "Step %r returned score lower than allowed (%g), normalizing to %g",
                            step.name,
                            step_score_addition,
                            step.SCORE_MIN,
                        )
                        step_score_addition = step.SCORE_MIN

                    score_addition += step_score_addition

                if step_justification_addition is not None:
                    justification_addition.extend(step_justification_addition)

        if (
            state.unresolved_dependencies
            and package_version_tuple[0] in state.unresolved_dependencies
            and not skip_package
        ):
            cloned_state = state.clone()
            weakref.finalize(cloned_state, self.predictor.finalize_state, id(cloned_state)).atexit = False
        else:
            # Optimization - reuse the old one as it would be discarded anyway.
            cloned_state = state
            if not user_stack_scoring and (
                (not skip_package and step_result)
                or (not state.unresolved_dependencies and (skip_package or not unresolved_dependencies))
            ):
                self.beam.remove(cloned_state)

        if unresolved_dependencies and not skip_package:
            cloned_state.set_unresolved_dependencies(unresolved_dependencies)

        if not skip_package:
            cloned_state.remove_unresolved_dependency_subtree(package_version_tuple[0])
            cloned_state.add_resolved_dependency(package_version_tuple)
            cloned_state.add_justification(justification_addition)
            cloned_state.score += score_addition
            self._run_pseudonyms(cloned_state, newly_added)

        cloned_state.iteration = self.context.iteration

        if not user_stack_scoring:
            if cloned_state.unresolved_dependencies:
                self.predictor.set_reward_signal(cloned_state, package_version_tuple, score_addition)
                if not skip_package and (state is not cloned_state or step_result):
                    self.beam.add_state(cloned_state)
            else:
                self.predictor.set_reward_signal(cloned_state, package_version_tuple, math.inf)

        return cloned_state

    def _run_strides(self, state: State) -> bool:
        """Run strides and check if the given state should be accepted."""
        package_strides = []
        for package_name in state.resolved_dependencies:
            package_strides.extend(self.pipeline.strides_dict.get(package_name, []))

        for stride in chain(package_strides, self.pipeline.strides_dict.get(None, [])):
            _LOGGER.debug("Running stride %r", stride.name)
            stride.unit_run = True
            try:
                stride.run(state)
            except NotAcceptable as exc:
                _LOGGER.debug(
                    "Stride %r removed final state %r: %s",
                    stride.name,
                    state,
                    exc,
                )
                return False
            except Exception as exc:
                raise StrideError(f"Failed to run stride {stride.name!r}: {str(exc)}") from exc

        return True

    def _run_wraps(self, state: State, *, sort: bool = False) -> None:
        """Run all wraps bound to the current run context."""
        package_wraps = []
        for package_name in state.resolved_dependencies:
            package_wraps.extend(self.pipeline.wraps_dict.get(package_name, []))

        for wrap in chain(package_wraps, self.pipeline.wraps_dict.get(None, [])):
            _LOGGER.debug("Running wrap %r", wrap.name)
            wrap.unit_run = True
            try:
                wrap.run(state)
            except Exception as exc:
                raise WrapError(f"Failed to run wrap {wrap.name!r} on a final state: {str(exc)}") from exc

        if sort:
            state.justification.sort(key=lambda i: (i.get("package_name", ""), i["type"], i["message"]))

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
                            package_version.name,
                            package_version.locked_version,
                            source.url,
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
            _LOGGER.info("Cannot score user's stack - no user's stack provided - see %s", jl("user_stack"))
            return None

        self._prepare_user_lock_file(with_devel=True)

        skipped_packages: List[PackageVersion] = []
        _LOGGER.info("Scoring user's stack based on the lock file submitted - see %s", jl("user_stack"))
        for package_version in self.project.iter_dependencies_locked(with_devel=with_devel):
            # First time seen, register this package for pipeline units.
            self.context.register_package_version(package_version)
            try:
                package_version = list(self._run_sieves([package_version], log_level=logging.INFO))
            except SkipPackage as exc:
                skipped_packages.append(package_version)
                _LOGGER.debug("Package %r skipped by sieves: %s", package_version.name, exc)
                continue

            if not package_version:
                _LOGGER.info("User's stack was removed based on sieves - see %s", jl("rm_user_stack"))
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
                _LOGGER.info("User's stack was removed based on steps - see %s", jl("rm_user_stack"))
                return None

        state.add_justification(
            [
                {
                    "type": "INFO",
                    "message": "Score of the supplied lock file is the highest possible "
                    "according to the current knowledge in Thoth and the parameters used to solve the stack",
                    "link": jl("user_stack"),
                },
                {
                    "type": "WARNING",
                    "message": "Correctness and the dependency graph of the supplied lock file is not verified",
                    "link": jl("user_stack"),
                },
            ]
        )
        _LOGGER.info("User's software stack has a score of %.2f - see %s", state.score, jl("user_stack"))
        return state

    def _resolve_direct_dependencies(self, *, with_devel: bool) -> Dict[str, List[PackageVersion]]:
        """Resolve all the direct dependencies based on the resolution and data available in the graph."""
        # It's important that solver preserves order in which packages were inserted.
        # This is also a requirement for running under Python3.6+!!!
        _LOGGER.info("Resolving direct dependencies")
        resolved_direct_dependencies: Dict[str, List[PackageVersion]] = self.solver.solve(
            sorted(
                self.project.iter_dependencies(with_devel=with_devel),
                key=lambda p: p.name,
            ),
            graceful=True,
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

                self.context.stack_info.append(
                    {
                        "message": error_msg,
                        "type": "ERROR",
                        "link": jl("solve_direct"),
                    }
                )
                _LOGGER.warning("%s - see %s", error_msg, jl("solve_direct"))
                continue

            _LOGGER.info(
                "Found direct dependency %r with version specification %r",
                package_version.name,
                package_version.version,
            )

        if unresolved:
            for dep in unresolved:
                error_msg = f"Resolver failed as it was unable to resolve direct dependency {dep!r}"
                self.context.stack_info.append(
                    {"message": error_msg, "type": "ERROR", "link": jl("unresolved"), "package_name": dep}
                )
                _LOGGER.warning("%s - see %s", error_msg, jl("unresolved"))

            self.context.stack_info.append(
                {
                    "message": "Visit thoth-station/support repository and request analyses of unresolved packages "
                    "to have them available in recommendations",
                    "link": "https://tinyurl.com/thoth-unresolved",
                    "type": "INFO",
                }
            )

            raise UnresolvedDependencies(
                "Unable to resolve all direct dependencies", unresolved=unresolved, stack_info=self.context.stack_info
            )

        # Now we are free to de-instantiate solver to save some memory.
        self._solver = None

        return resolved_direct_dependencies

    def _prepare_initial_state(self, *, with_devel: bool) -> State:
        """Prepare initial state for resolver."""
        direct_dependencies = self._resolve_direct_dependencies(with_devel=with_devel)

        if not direct_dependencies:
            msg = "No direct dependencies found"
            self.context.stack_info.append(
                {
                    "message": msg,
                    "type": "ERROR",
                    "link": jl("solve_direct"),
                }
            )
            raise CannotProduceStack(msg, stack_info=self.context.stack_info)

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
                _LOGGER.debug("Package %r skipped by sieves: %s", direct_dependency_name, exc)
                continue

            if not package_versions:
                msg = (
                    f"Cannot satisfy direct dependencies: direct dependencies of type {direct_dependency_name!r} "
                    "were removed by pipeline sieves"
                )
                self.context.stack_info.append(
                    {
                        "type": "ERROR",
                        "message": msg,
                        "link": jl("unresolved"),
                    }
                )
                raise CannotProduceStack(msg, stack_info=self.context.stack_info)

            if self.limit_latest_versions:
                direct_dependencies[direct_dependency_name] = package_versions[: self.limit_latest_versions]
            else:
                direct_dependencies[direct_dependency_name] = package_versions

        for direct_dependency_name in skipped_packages:
            # Remove separately due to dictionary size changes during dict iterations in items. Also, this loop
            # should occur rarely so it's more efficient to do it this way instead of creating a swallow copy of
            # dict during iteration.
            direct_dependencies.pop(direct_dependency_name)

        if not direct_dependencies:
            msg = "Cannot satisfy direct dependencies: all direct dependencies were filtered by sieves"
            self.context.stack_info.append(
                {
                    "type": "ERROR",
                    "message": msg,
                    "link": jl("unresolved"),
                }
            )
            raise CannotProduceStack(msg, stack_info=self.context.stack_info)

        # Create an initial state which is made out of all the direct dependencies (kept as unresolved) in
        # resolved versions.
        self.beam.wipe()
        state = State.from_direct_dependencies(direct_dependencies)
        weakref.finalize(state, self.predictor.finalize_state, id(state)).atexit = False
        self.beam.add_state(state)
        return state

    def _run_pseudonyms(self, state: State, package_tuples: Optional[List[Tuple[str, str, str]]] = None) -> None:
        """Run pseudonyms for the given package, clone state and add it to beam if needed."""
        for package_tuple in package_tuples or []:
            self._run_pseudonym_units(state, package_tuple)

    def _run_pseudonym_units(self, state: State, package_tuple: Tuple[str, str, str]) -> None:
        """Run pseudonym units the given package tuple."""
        package_version: PackageVersion = self.context.get_package_version(package_tuple)
        for unit in self.pipeline.pseudonyms_dict.get(package_tuple[0], []):
            _LOGGER.debug("Running pseudonym %r", unit.name)
            unit.unit_run = True
            for pseudonym_package_tuple in unit.run(package_version):
                # Pseudonyms introduced do not have dependents (we work on direct dependencies - initial state).
                if pseudonym_package_tuple[0] in state.resolved_dependencies:
                    _LOGGER.debug(
                        "Pseudonym %r already present in a resolved form, skipping pseudonym creation",
                        pseudonym_package_tuple,
                    )
                    continue

                if (
                    pseudonym_package_tuple
                    in state.unresolved_dependencies.get(pseudonym_package_tuple[0], {}).values()
                ):
                    _LOGGER.debug(
                        "Pseudonym %r already present in state in unresolved form, not creating a new state",
                        pseudonym_package_tuple,
                    )
                    continue

                self.context.register_package_tuple(
                    pseudonym_package_tuple,
                    develop=package_version.develop,
                    os_name=None,  # TODO: pass based on the package_tuple
                    os_version=None,
                    python_version=None,
                )
                new_state = state.clone()
                new_state.remove_unresolved_dependency_subtree(package_tuple[0])
                new_state.add_unresolved_dependency(pseudonym_package_tuple)
                self.beam.add_state(new_state)

    def _run_pseudonyms_initial_state(self, state: State) -> None:
        """Run pseudonyms on an initial state."""
        to_run_pseudonyms = state.unresolved_dependencies.keys() & self.pipeline.pseudonyms_dict.keys()
        for pseudonym_name in to_run_pseudonyms:
            for package_tuple in state.unresolved_dependencies[pseudonym_name].values():
                self._run_pseudonym_units(state, package_tuple)

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
        newly_added: List[Tuple[str, str, str]] = []
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
                newly_added.append(dependency_tuple)

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
                _LOGGER.debug("Package %r skipped by sieves: %s", dependency_name, exc)
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

        return self._run_steps(state, package_version, all_dependencies, newly_added)

    def _do_resolve_states_raw(
        self,
        *,
        with_devel: bool = True,
        user_stack_scoring: bool = True,
    ) -> Generator[State, None, None]:
        """Actually perform states resolution."""
        self._log_once_init()
        self._run_boots(with_devel=with_devel)

        if not self.project.runtime_environment.is_fully_specified():
            _LOGGER.warning(
                "Environment is not fully specified, pre-computed environment markers will "
                "not be taken into account - see %s",
                jl("spec_env"),
            )

        if user_stack_scoring:
            _LOGGER.info("Scoring user's stack - see %s", jl("user_stack"))
            try:
                user_stack = self._maybe_score_user_lock_file(with_devel=with_devel)
            except UserLockFileError as exc:
                _LOGGER.warning("Failed to score user's lock file: %s", exc)
            except Exception:
                _LOGGER.exception("Failed to score supplied user stack, the error is not fatal")
            else:
                if user_stack:
                    yield user_stack
        else:
            _LOGGER.info("No scoring done on user's stack - see %s", jl("user_stack"))

        _LOGGER.info("Preparing initial states for the resolution pipeline")
        state = self._prepare_initial_state(with_devel=with_devel)
        self._run_pseudonyms_initial_state(state)

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
                        "No more possible paths found for resolution, terminating resolver in iteration %d, see - %s",
                        self.context.iteration,
                        jl("no_paths"),
                    )
                    break

                self.beam.new_iteration()
                self.context.iteration += 1

                state, unresolved_package_tuple = self.predictor.run()

                _LOGGER.debug(
                    "Resolving package %r in state with score %g: %r",
                    unresolved_package_tuple,
                    state.score,
                    state,
                )
                state_returned = self._expand_state(state, unresolved_package_tuple)
                if state_returned is not None and not state_returned.unresolved_dependencies:
                    # A final state produced by the pipeline.
                    if self._run_strides(state_returned):
                        self.context.accepted_final_states_count += 1
                        self.context.register_accepted_final_state(state_returned)
                        yield state_returned
                    else:
                        self.context.discarded_final_states_count += 1

                    if self.beam.keep_history:
                        self._history.append(state_returned.score)
                        self._history_max.append(
                            max(
                                self._history_max[-1]
                                if self._history_max and self._history_max[-1] is not None
                                else state_returned.score,
                                state_returned.score,
                            )
                        )
                else:
                    if self.beam.keep_history:
                        self._history.append(None)
                        self._history_max.append(self._history_max[-1] if self._history_max else None)

        if self.stop_resolving:
            _LOGGER.warning(
                "Resolving stopped with the current beam size %d as the allocated CPU time was exhausted",
                self.beam.size,
            )

    def _do_resolve_states(
        self,
        *,
        with_devel: bool = True,
        user_stack_scoring: bool = True,
    ) -> Generator[State, None, None]:
        """Resolve states as produced by this resolver pipeline, ready to be used to build a product."""
        if self.count > self.limit:
            _LOGGER.warning(
                "Count (%d) is higher than limit (%d), setting count to %d",
                self.count,
                self.limit,
                self.limit,
            )
            self.count = self.limit

        self._history.clear()
        self._history_max.clear()
        self.predictor.pre_run()
        self.pipeline.call_pre_run()

        start_time = time.monotonic()
        max_score = None
        last_iteration_logged = 0
        try:
            for final_state in self._do_resolve_states_raw(
                with_devel=with_devel, user_stack_scoring=user_stack_scoring
            ):
                _LOGGER.debug(
                    "Pipeline reached a new final state, yielding pipeline product with a score of %g - %d/%d",
                    final_state.score,
                    self.context.accepted_final_states_count,
                    self.context.limit,
                )

                max_score = final_state.score if max_score is None else max(max_score, final_state.score)

                if (
                    self.context.iteration - last_iteration_logged > self.log_iteration
                    or self.context.accepted_final_states_count == 1
                ):
                    _LOGGER.info(
                        "Pipeline performed %d moves in the dependency graph and generated %d software stacks out "
                        "of %d requested (pipeline pace %.02f stacks/second); top rated software stack in beam "
                        "has a score of %.2f; top rated software stack found so far has a score of %.2f",
                        self.context.iteration,
                        self.context.accepted_final_states_count,
                        self.context.limit,
                        self.context.accepted_final_states_count / (time.monotonic() - start_time),
                        self.beam.max().score if self.beam.size > 0 else float("nan"),
                        float("nan") if max_score is None else max_score,
                    )
                    last_iteration_logged = self.context.iteration

                yield final_state
                del final_state
        except EagerStopPipeline as exc:
            _LOGGER.info("Stopping pipeline eagerly as per request: %s", exc)
        except Exception:
            self.predictor.post_run()
            self.pipeline.call_post_run()
            raise

        duration = time.monotonic() - start_time
        _LOGGER.info(
            "Resolver took %g seconds in total, pipeline speed %g stacks/second",
            duration,
            self.context.accepted_final_states_count / duration,
        )

        if max_score is not None:
            _LOGGER.info("The highest rated software stack resolved has a score of %0.2f", max_score)

        _LOGGER.info(
            "Pipeline strides discarded %d and accepted %d software stacks in total",
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
            for state in self._do_resolve_states(with_devel=with_devel, user_stack_scoring=user_stack_scoring):
                # Always run wraps as raw products are computed.
                self._run_wraps(state, sort=True)
                yield Product.from_final_state(context=self.context, state=state)

    def resolve(self, *, with_devel: bool = True, user_stack_scoring: bool = True) -> Report:
        """Resolve software stacks and return resolver report."""
        states: List[Tuple[Tuple[float, int], State]] = []  # The first item in tuple is used for sorting.
        heapq_counter = 0  # Making sure the first resolved state takes precedence when adding to the report.

        self._init_context()
        with Unit.assigned_context(self.context), self.predictor.assigned_context(self.context):
            for state in self._do_resolve_states(with_devel=with_devel, user_stack_scoring=user_stack_scoring):
                item = ((state.score, heapq_counter), state)
                heapq_counter -= 1

                if len(states) >= self.count:
                    heapq.heappushpop(states, item)
                else:
                    heapq.heappush(states, item)

            if len(states) == 0:
                msg = (
                    f"Resolver did not find any stack that would satisfy requirements and stack "
                    f"characteristics given the time allocated"
                )
                link = jl("no_stack")
                self.context.stack_info.append(
                    {
                        "message": msg,
                        "type": "ERROR",
                        "link": link,
                    }
                )
                raise CannotProduceStack(msg + f" - see {link}", stack_info=self.context.stack_info)

            for item in states:
                self._run_wraps(item[1], sort=True)

            report = Report(
                products=[
                    Product.from_final_state(context=self.context, state=s[1])
                    for s in sorted(states, key=lambda s: s[0], reverse=True)
                ],
                pipeline=self.pipeline,
                resolver_iterations=self.context.iteration,
                accepted_final_states_count=self.context.accepted_final_states_count,
                discarded_final_states_count=self.context.discarded_final_states_count,
                stack_info=self.context.stack_info,
            )

            self.predictor.post_run_report(report)
            self.pipeline.call_post_run_report(report)

            return report

    def plot(self) -> "matplotlib.figure.Figure":
        """Plot history captured during the resolution process."""
        if not self._history:
            raise NoHistoryKept("No history datapoints kept")

        import matplotlib.pyplot as plt
        from matplotlib.font_manager import FontProperties

        x = [i for i in range(len(self._history))]
        y1 = self._history
        y2 = self._history_max

        fig, host = plt.subplots()
        fig.subplots_adjust(right=0.75)

        par1 = host.twinx()

        par1.spines["right"].set_position(("axes", 1.10))
        self.beam._make_patch_spines_invisible(par1)

        par1.spines["right"].set_visible(True)
        host.spines["right"].set_visible(False)
        host.spines["top"].set_visible(False)

        (p1,) = host.plot(x, y1, ",g", label="Score of the resolved stack")
        (p2,) = par1.plot(x, y2, ",b", label="The highest score")

        host.set_xlabel("iteration")
        host.set_ylabel("Score of the resolved stack in iteration")
        par1.set_ylabel("Score of the best resolved stack found")

        host.yaxis.label.set_color(p1.get_color())
        par1.yaxis.label.set_color(p2.get_color())

        tkw = dict(size=4, width=1.5)
        host.tick_params(axis="y", colors=p1.get_color(), **tkw)
        host.tick_params(axis="x", **tkw)
        par1.tick_params(axis="y", colors=p2.get_color(), **tkw)

        font_prop = FontProperties()
        font_prop.set_size("medium")
        fig.legend(
            loc="upper center",
            bbox_to_anchor=(0.50, 1.00),
            ncol=2,
            fancybox=True,
            shadow=True,
            prop=font_prop,
        )
        return fig

    @classmethod
    def get_adviser_instance(
        cls,
        *,
        predictor: Predictor,
        beam_width: Optional[int] = None,
        count: int = DEFAULT_COUNT,
        graph: Optional[GraphDatabase] = None,
        labels: Optional[Dict[str, str]] = None,
        library_usage: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        limit_latest_versions: Optional[int] = DEFAULT_LIMIT_LATEST_VERSIONS,
        project: Project,
        recommendation_type: RecommendationType,
        pipeline_config: Optional[Union[PipelineConfig, Dict[str, Any]]] = None,
        prescription: Optional["Prescription"] = None,
        cli_parameters: Optional[Dict[str, Any]] = None,
    ) -> "Resolver":
        """Get instance of resolver based on the project given to recommend software stacks."""
        graph = graph or GraphDatabase()
        if not graph.is_connected():
            graph.connect()

        if pipeline_config is None:
            pipeline = PipelineBuilder.get_adviser_pipeline_config(
                recommendation_type=recommendation_type,
                project=project,
                labels=labels or {},
                library_usage=library_usage,
                graph=graph,
                prescription=prescription,
                cli_parameters=cli_parameters or {},
            )
        else:
            assert prescription is None, "Cannot supply prescription and pipeline config at the same time"

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
            labels=labels or {},
            library_usage=library_usage,
            limit_latest_versions=limit_latest_versions,
            limit=limit,
            pipeline=pipeline,
            predictor=predictor,
            project=project,
            recommendation_type=recommendation_type,
            prescription=prescription,
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
        labels: Optional[Dict[str, str]] = None,
        library_usage: Optional[Dict[str, Any]] = None,
        limit_latest_versions: Optional[int] = DEFAULT_LIMIT_LATEST_VERSIONS,
        project: Project,
        decision_type: DecisionType,
        pipeline_config: Optional[Union[PipelineConfig, Dict[str, Any]]] = None,
        prescription: Optional["Prescription"] = None,
        cli_parameters: Optional[Dict[str, Any]] = None,
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
                labels=labels or {},
                library_usage=library_usage,
                prescription=prescription,
                cli_parameters=cli_parameters or {},
            )
        else:
            assert prescription is None, "Cannot supply prescription and pipeline config at the same time"

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
            labels=labels or {},
            library_usage=library_usage,
            limit_latest_versions=limit_latest_versions,
            pipeline=pipeline,
            predictor=predictor,
            project=project,
            decision_type=decision_type,
            prescription=prescription,
            cli_parameters=cli_parameters or {},
        )
