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

"""Representation of an advised stack."""

import logging
from typing import Any
from typing import Optional
from typing import Dict
from typing import List

import attr

from thoth.common import RuntimeEnvironment
from thoth.python import Project
from thoth.python import PackageVersion
from thoth.storages import GraphDatabase

from .context import Context
from .state import State


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True, eq=False, order=False)
class Product:
    """A representation of an advised stack."""

    project = attr.ib(type=Project)
    score = attr.ib(type=float)
    justification = attr.ib(type=List[Dict[str, str]])
    advised_runtime_environment = attr.ib(
        type=Optional[RuntimeEnvironment], default=None
    )

    @classmethod
    def from_final_state(
        cls, *, graph: GraphDatabase, project: Project, context: Context, state: State
    ) -> "Product":
        """Instantiate advised stack from final state produced by adviser's pipeline."""
        assert state.is_final(), "Instantiating product from a non-final state"

        package_versions_locked = []
        for package_tuple in state.resolved_dependencies.values():
            package_version: PackageVersion = context.get_package_version(
                package_tuple, graceful=False
            )

            # Fill package hashes before instantiating the final product.
            if not package_version.hashes:
                # We can re-use already existing package-version - in that case it already keeps hashes from
                # a previous product instantiation.
                hashes = graph.get_python_package_hashes_sha256(*package_tuple)
                package_version.hashes = ["sha256:" + h for h in hashes]

                if not package_version.hashes:
                    _LOGGER.warning("No hashes found for package %r", package_tuple)

            package_versions_locked.append(package_version)

        advised_project = Project.from_package_versions(
            packages=list(project.iter_dependencies(with_devel=True)),
            packages_locked=package_versions_locked,
        )

        return cls(
            project=advised_project,
            score=state.score,
            justification=state.justification,
            advised_runtime_environment=state.advised_runtime_environment,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert this instance into a dictionary."""
        advised_runtime_environment = None
        if self.advised_runtime_environment:
            advised_runtime_environment = self.advised_runtime_environment.to_dict()

        return {
            "project": self.project.to_dict(),
            "score": self.score,
            "justification": self.justification,
            "advised_runtime_environment": advised_runtime_environment,
        }
