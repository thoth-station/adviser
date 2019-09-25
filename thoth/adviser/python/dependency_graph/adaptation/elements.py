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

"""Elements of dependency graph adaptation."""

import attr
from typing import Dict
from typing import Tuple
from typing import Union
from typing import Optional
from typing import Generator


@attr.s(slots=True)
class Node:
    """A node in constructed dependency graph."""

    package_tuple = attr.ib(type=Tuple[str, str, str])
    # A key to first dictionary is package name or None if an "edge" to direct dependency,
    # the subsequent key to next dictionary is a package tuple (package name, package version,
    # index url) which points to the edge.
    incoming_edges = attr.ib(
        type=Dict[Optional[str], Dict[Tuple[str, str, str], "Edge"]],
        default=attr.Factory(dict),
    )
    outgoing_edges = attr.ib(
        type=Dict[Optional[str], Dict[Tuple[str, str, str], "Edge"]],
        default=attr.Factory(dict),
    )

    @property
    def all_incoming_edges(self) -> Generator["Edge", None, None]:
        """Iterate over all incoming edges regardless of the source package."""
        for edges_dict in self.incoming_edges.values():
            for edge in edges_dict.values():
                yield edge

    @property
    def all_outgoing_edges(self) -> Generator["Edge", None, None]:
        """Iterate over all outgoing edges regardless of the destination package."""
        for edges_dict in self.outgoing_edges.values():
            for edge in edges_dict.values():
                yield edge

    @property
    def all_dependent_package_tuples(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over all package tuples which depend on this node."""
        for incoming_edge in self.all_incoming_edges:
            if incoming_edge.source:
                yield incoming_edge.source.package_tuple

    @property
    def all_dependency_package_tuples(
        self
    ) -> Generator[Tuple[str, str, str], None, None]:
        """Iterate over all packages which are dependencies for this node."""
        for outgoing_edge in self.all_outgoing_edges:
            yield outgoing_edge.target.package_tuple


@attr.s(slots=True)
class Edge:
    """An edge in dependency graph which is weighted (weight is score)."""

    source = attr.ib(type=Union[Node, None])
    target = attr.ib(type=Node)
    score = attr.ib(type=float, default=0.0)

    def get_edge_key(
        self
    ) -> Tuple[Union[Tuple[str, str, str], None], Tuple[str, str, str]]:
        """Get key which identifies edge."""
        return (
            self.source.package_tuple if self.source is not None else None,
            self.target.package_tuple,
        )
