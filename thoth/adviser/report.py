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

"""A class for adviser's report - output of an adviser run."""

import heapq
import logging
import operator
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple

import attr

from .pipeline_config import PipelineConfig
from .product import Product


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Report:
    """A report stating output of an adviser run."""

    count = attr.ib(type=int, kw_only=True)
    pipeline = attr.ib(type=PipelineConfig, kw_only=True)
    _stack_info = attr.ib(
        type=Optional[List[Dict[str, Any]]], kw_only=True, default=None
    )
    _heapq = attr.ib(
        type=List[Tuple[Tuple[float, int], Product]],
        default=attr.Factory(list),
        kw_only=True,
    )
    _heapq_counter = attr.ib(type=int, default=0, kw_only=True)

    @property
    def stack_info(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieve stack info of this report."""
        return self._stack_info

    def set_stack_info(self, stack_info: List[Dict[str, Any]]) -> None:
        """Set stack information."""
        self._stack_info = stack_info

    def add_product(self, product: Product) -> None:
        """Add adviser pipeline product to report."""
        item = ((product.score, self._heapq_counter), product)
        self._heapq_counter -= 1

        if len(self._heapq) >= self.count:
            heapq.heappushpop(self._heapq, item)
        else:
            heapq.heappush(self._heapq, item)

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline report to a dict representation."""
        return {
            "pipeline": self.pipeline.to_dict(),
            "products": [product.to_dict() for product in self.iter_products()],
            "stack_info": self._stack_info,
        }

    def product_count(self) -> int:
        """Get number of products stored in the report."""
        return len(self._heapq)

    def iter_products(self) -> Generator[Product, None, None]:
        """Iterate over products stored in this report, respect their scores."""
        return (item[1] for item in self._heapq)

    def iter_products_sorted(
        self, reverse: bool = True
    ) -> Generator[Product, None, None]:
        """Iterate over products stored in this report, respect their scores."""
        return (
            item[1]
            for item in sorted(self._heapq, key=operator.itemgetter(0), reverse=reverse)
        )
