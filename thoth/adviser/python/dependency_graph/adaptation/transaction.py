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

"""Transactional changes in dependency graph."""

import attr
from typing import List
from typing import Generator
from typing import Tuple
import logging

from .exceptions import TransactionExpired
from .elements import Node
from .elements import Edge

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class DependencyGraphTransaction:
    """A transaction on top of Dependency Graph keeping state."""

    dependency_graph = attr.ib()
    to_remove_edges = attr.ib(type=List[Edge], default=attr.Factory(list))
    to_remove_nodes = attr.ib(type=List[Node], default=attr.Factory(list))

    def commit(self) -> None:
        """Commit the given pending transaction."""
        if self.to_remove_edges is None:
            raise TransactionExpired("Transaction is not valid anymore")

        self.dependency_graph.perform_transaction(
            to_remove_edges=self.to_remove_edges, to_remove_nodes=self.to_remove_nodes
        )

        self.to_remove_edges = None
        self.to_remove_nodes = None

    def rollback(self) -> None:
        """Rollback the given pending transaction."""
        if self.to_remove_edges is None:
            raise TransactionExpired("Transaction is not valid anymore")

        self.to_remove_edges = None
        self.to_remove_edges = None

    def iter_package_tuples(self) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over package tuples which are about to be removed from dependency graph in this transaction."""
        for node in self.to_remove_nodes:
            yield node.package_tuple

    def __del__(self):
        """Destruct this object.

        Print warning to users of the recommendation engine in case of unclosed transactions.
        """
        if self.to_remove_edges is not None:
            _LOGGER.error("Transaction on dependency graph was not closed properly")

    def score_summary(self) -> float:
        """Compute summary for the score that will result in the current transaction."""
        result = 0.0
        for edge in self.to_remove_edges:
            result += edge.score

        return result

    def any_positive_score(self) -> bool:
        """Check if positive score will be affected in this transaction once committed."""
        return any(edge.score > 0 for edge in self.to_remove_edges)
