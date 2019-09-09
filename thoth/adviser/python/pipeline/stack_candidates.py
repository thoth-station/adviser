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

"""Wrapper for transparent manipulation with stack candidates."""


import os
import logging
from typing import Generator
from typing import List
from typing import Tuple
from typing import Dict
from heapq import heappushpop
from heapq import heappush
from heapq import heappop

import attr

from thoth.python import Project
from thoth.python import PackageVersion
from thoth.storages import GraphDatabase

from .stride_context import StrideContext
from .product import PipelineProduct


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class StackCandidates:
    """A wrapper for stack candidates."""

    input_project = attr.ib(type=Project)
    direct_dependencies_map = attr.ib(
        type=Dict[str, Dict[str, Dict[str, PackageVersion]]], default=attr.Factory(dict)
    )
    transitive_dependencies_map = attr.ib(
        type=Dict[str, Dict[str, Dict[str, PackageVersion]]], default=attr.Factory(dict)
    )
    count = attr.ib(type=int, default=None)
    _stack_candidates = attr.ib(
        type=List[Tuple[float, List[Tuple[str, str, str]]]], default=attr.Factory(list)
    )

    def add(self, stride_context: StrideContext) -> None:
        """Add the given stack candidate to candidate listing."""
        # We add length of heapq to tuple to make sure items pop'ed out first are the ones
        # first inserted if score matches. This requires insertion first and generation later on (do not mix
        # calls) - this is preserved in our case.
        heap_item = (
            (stride_context.score, len(self._stack_candidates)),
            stride_context.justification,
            stride_context.stack_candidate,
        )
        if self.count is not None and len(self._stack_candidates) == self.count:
            heappushpop(self._stack_candidates, heap_item)
            return

        heappush(self._stack_candidates, heap_item)

    def get_package_version_tuple(self, package_tuple: tuple) -> PackageVersion:
        """Get package version from the dependencies map based on tuple provided."""
        try:
            return self.transitive_dependencies_map[package_tuple]
        except KeyError:
            return self.direct_dependencies_map[package_tuple]

    def generate_pipeline_products(self, graph: GraphDatabase) -> Generator[PipelineProduct, None, None]:
        """Generate projects in stack candidates.

        All the candidates are discarded after calling this function.
        """
        while self._stack_candidates:
            heap_item = heappop(self._stack_candidates)
            sort_key, justification, stack_candidate = heap_item
            score = sort_key[0]
            package_versions_locked = [
                self.get_package_version_tuple(package_tuple)
                for package_tuple in stack_candidate
            ]

            # Print out packages if user requested so.
            if bool(os.getenv("THOTH_ADVISER_SHOW_PACKAGES", 0)):
                _LOGGER.info("Packages forming found stack (score: %f):", score)
                for item in stack_candidate:
                    _LOGGER.info("    %r", item)

            project = Project.from_package_versions(
                packages=self.input_project.iter_dependencies(with_devel=True),
                packages_locked=package_versions_locked,
                meta=self.input_project.pipfile.meta,
            )

            yield PipelineProduct(
                project=project, score=score, justification=justification, graph=graph
            )
