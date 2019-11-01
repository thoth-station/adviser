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
from typing import Dict
from typing import List

import attr

from thoth.storages import GraphDatabase
from thoth.python import Project

from .context import Context
from .state import State


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True, eq=False, order=False)
class Product:
    """A representation of an advised stack."""

    project = attr.ib(type=Project)
    score = attr.ib(type=float)
    justification = attr.ib(type=List[Dict[str, str]])

    @classmethod
    def from_final_state(
        cls, *, graph: GraphDatabase, project: Project, context: Context, state: State
    ) -> "Product":
        """Instantiate advised stack from final state produced by adviser's pipeline."""
        package_versions_locked = []
        for package_tuple in state.resolved_dependencies.values():
            package_version = context.get_package_version(package_tuple)

            # Fill package hashes before instantiating the final product.
            package_version.hashes = graph.get_python_package_hashes_sha256(
                *package_tuple
            )
            if not package_version.hashes:
                _LOGGER.warning("No hashes found for package %r", package_tuple)

            package_versions_locked.append(package_version)

        # TODO: advised runtime environment
        advised_project = Project.from_package_versions(
            packages=list(project.iter_dependencies(with_devel=True)),
            packages_locked=package_versions_locked,
        )

        return cls(
            project=advised_project,
            score=state.score,
            justification=state.justification,
        )

    def __lt__(self, other: "Product") -> bool:
        """Compare two products based on the score."""
        return self.score < other.score

    def to_dict(self) -> Dict[str, Any]:
        """Convert this instance into a dictionary."""
        return {
            "project": self.project.to_dict(),
            "score": self.score,
            "justification": self.justification,
        }
