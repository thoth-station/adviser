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

"""Representation of an advised stack."""

import os
import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

import attr

from thoth.common import RuntimeEnvironment
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion
from thoth.python import Project
from thoth.python import PipfileLock
from thoth.storages.exceptions import NotFoundError

from .context import Context
from .state import State
from .utils import log_once


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True, eq=False, order=False)
class Product:
    """A representation of an advised stack."""

    _LOG_HASHES: Set[Tuple[str, str, str]] = set()
    _NO_OBSERVATION_JUSTIFICATION: Dict[str, str] = {
        "link": jl("no_observations"),
        "message": "No issues spotted for this stack based on Thoth's database",
        "type": "INFO",
    }

    # This project is "advised project" and does not need to be exactly the same as the one stated in context.
    project = attr.ib(type=Project, kw_only=True)
    score = attr.ib(type=float, kw_only=True)
    justification = attr.ib(type=List[Dict[str, str]], kw_only=True)
    advised_runtime_environment = attr.ib(type=Optional[RuntimeEnvironment], default=None, kw_only=True)
    advised_manifest_changes = attr.ib(type=List[List[Dict[str, Any]]], kw_only=True, default=attr.Factory(list))
    _context = attr.ib(type=Context, kw_only=True)

    @classmethod
    def from_final_state(cls, *, context: Context, state: State) -> "Product":
        """Instantiate advised stack from final state produced by adviser's pipeline."""
        assert state.is_final(), "Instantiating product from a non-final state"

        package_versions_locked = []
        for package_tuple in state.resolved_dependencies.values():
            package_version: PackageVersion = context.get_package_version(package_tuple, graceful=False)

            # Fill package hashes before instantiating the final product.
            if not package_version.hashes:
                # We can re-use already existing package-version - in that case it already keeps hashes from
                # a previous product instantiation.
                hashes = context.graph.get_python_package_hashes_sha256(*package_tuple)
                package_version.hashes = ["sha256:" + h for h in hashes]

                if not package_version.hashes:
                    log_once(_LOGGER, cls._LOG_HASHES, package_tuple, "No hashes found for package %r", package_tuple)

            direct_dependency = context.project.pipfile.packages.packages.get(package_version.name)
            if direct_dependency:
                # If the given package is a direct dependency, reuse markers stated by the user.
                package_version.markers = direct_dependency.markers
            else:
                # Fill environment markers by checking dependencies that introduced this dependency.
                # We do it only if we have no hashes - if hashes are present, the environment marker was
                # already picked (can be set to None if no marker is present).
                # For direct dependencies, dependents can return an empty set (if dependency is not
                # shared with other dependencies) and marker is propagated from PackageVersion registered in
                # Context.register_package_version.
                dependents_tuples = context.dependents[package_tuple[0]][package_tuple]

                # Marker depends based on the stack that was resolved. Do not change package_version directly,
                # rather clone it and used a cloned version not to clash with environment markers.
                environment_markers = []
                for dependent_tuple in dependents_tuples:
                    try:
                        marker = context.graph.get_python_environment_marker(
                            *dependent_tuple[0],
                            dependency_name=package_tuple[0],
                            dependency_version=package_tuple[1],
                            os_name=dependent_tuple[1],
                            os_version=dependent_tuple[2],
                            python_version=dependent_tuple[3],
                        )
                    except NotFoundError:
                        # This can happen if we do resolution that is agnostic to runtime
                        # environment. In that case a dependency introduced in one runtime
                        # environment does not need to co-exist in another runtime environment considering
                        # marker evaluation result.
                        continue

                    if marker and marker not in environment_markers:
                        environment_markers.append(marker)
                    elif not marker:
                        # One or multiple dependencies require this dependency to be always present, clear any
                        # environment markers.
                        environment_markers.clear()
                        break

                if environment_markers:
                    if len(environment_markers) > 1:
                        markers = " or ".join(f"({m})" for m in environment_markers)
                    else:
                        markers = environment_markers[0]

                    package_version = attr.evolve(
                        package_version,
                        markers=markers,
                    )

            package_versions_locked.append(package_version)

        advised_project = Project.from_package_versions(
            packages=list(context.project.iter_dependencies(with_devel=True)),
            packages_locked=package_versions_locked,
            meta=context.project.pipfile.meta,
            runtime_environment=context.project.runtime_environment,
        )

        # Keep thoth section untouched.
        advised_project.pipfile.thoth = context.project.pipfile.thoth

        justification_metadata: List[Dict[str, Any]] = []
        metadata = os.getenv("THOTH_ADVISER_METADATA")
        if metadata:
            try:
                metadata_content = json.loads(metadata)
                justification_metadata = (metadata_content.get("thoth.adviser") or {}).get("justification") or []
            except Exception:
                _LOGGER.exception("Failed to parse adviser metadata")

        justification = justification_metadata + state.justification
        if not justification:
            justification.append(cls._NO_OBSERVATION_JUSTIFICATION)

        return cls(
            project=advised_project,
            score=state.score,
            justification=justification,
            advised_runtime_environment=state.advised_runtime_environment,
            advised_manifest_changes=state.advised_manifest_changes,
            context=context,
        )

    @staticmethod
    def _construct_dependency_graph(context: Context, pipfile_lock: PipfileLock) -> Dict[str, Any]:
        """Construct dependency graph for the given Pipfile.lock."""
        nodes: List[str] = []
        nodes_idx: Dict[Tuple[str, str, str], int] = {}
        for package_version in pipfile_lock.packages.packages.values():
            package_version_tuple = package_version.to_tuple()
            nodes.append(package_version_tuple)
            nodes_idx[package_version_tuple] = len(nodes_idx)

        edges = []
        for src_idx, package_version_tuple in enumerate(nodes):
            dependencies = context.dependencies.get(package_version_tuple[0], {}).get(package_version_tuple)
            if not dependencies:
                continue

            for dependency in dependencies:
                dst_idx = nodes_idx.get(dependency)
                if dst_idx is not None:
                    edges.append([src_idx, dst_idx])

        # Discard version and index url as package name is good enough to locate nodes.
        return {"nodes": [i[0] for i in nodes], "edges": edges}

    def to_dict(self) -> Dict[str, Any]:
        """Convert this instance into a dictionary."""
        advised_runtime_environment = None
        if self.advised_runtime_environment:
            advised_runtime_environment = self.advised_runtime_environment.to_dict()

        return {
            "project": self.project.to_dict(keep_thoth_section=True),
            "dependency_graph": self._construct_dependency_graph(self._context, self.project.pipfile_lock),
            "score": self.score,
            "justification": self.justification,
            "advised_runtime_environment": advised_runtime_environment,
            "advised_manifest_changes": self.advised_manifest_changes,
        }
