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

"""A class for adviser's report - output of an adviser run."""

import heapq
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Optional

import attr
import matplotlib
from thoth.common import RuntimeEnvironment

from .pipeline_config import PipelineConfig
from .product import Product
from .plot import plot_history


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Report:
    """A report stating output of an adviser run."""

    count = attr.ib(type=int, kw_only=True)
    pipeline = attr.ib(type=PipelineConfig, kw_only=True)
    _advised_runtime_environment = attr.ib(
        type=RuntimeEnvironment, kw_only=True, default=None
    )
    _stack_info = attr.ib(
        type=Optional[List[Dict[str, Any]]], kw_only=True, default=None
    )
    _temperature_history = attr.ib(
        type=Optional[List[Tuple[float, bool, float, int]]], default=None, kw_only=True
    )
    _heapq = attr.ib(type=List[Product], default=attr.Factory(list), kw_only=True)

    def set_temperature_history(
        self, temperature_history: List[Tuple[float, bool, float, int]]
    ) -> None:
        """Mark the temperature history during annealing."""
        self._temperature_history = temperature_history

    def set_advised_runtime_environment(
        self, runtime_environment: RuntimeEnvironment
    ) -> None:
        """Mark advised runtime environment."""
        self._advised_runtime_environment = runtime_environment

    def set_stack_info(self, stack_info: List[Dict[str, Any]]) -> None:
        """Set stack information."""
        self._stack_info = stack_info

    def plot_history(
        self, output_file: Optional[str] = None
    ) -> matplotlib.figure.Figure:
        """Plot history of temperature function."""
        return plot_history(self._temperature_history, output_file)

    def add_product(self, product: Product) -> None:
        """Add adviser pipeline product to report."""
        if len(self._heapq) >= self.count:
            heapq.heappushpop(self._heapq, product)
        else:
            heapq.heappush(self._heapq, product)

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline report to a dict representation."""
        advised_runtime_environment = None
        if self._advised_runtime_environment:
            advised_runtime_environment = self._advised_runtime_environment.to_dict()

        return {
            "advised_runtime_environment": advised_runtime_environment,
            "pipeline": self.pipeline.to_dict(),
            "products": [product.to_dict() for product in self.iter_products()],
            "stack_info": self._stack_info,
        }

    def product_count(self) -> int:
        """Get number of products stored in the report."""
        return len(self._heapq)

    def iter_products(self) -> List[Product]:
        """Iterate over products stored in this report, respect their scores."""
        return sorted(self._heapq, key=lambda product: product.score, reverse=True)
