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

"""A class for adviser's report - output of an adviser run."""

import os
import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import attr

from .pipeline_config import PipelineConfig
from .product import Product


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Report:
    """A report stating output of an adviser run."""

    products = attr.ib(type=List[Product], kw_only=True)
    pipeline = attr.ib(type=PipelineConfig, kw_only=True)
    resolver_iterations = attr.ib(type=int, kw_only=True, default=0)
    accepted_final_states_count = attr.ib(type=int, kw_only=True, default=0)
    discarded_final_states_count = attr.ib(type=int, kw_only=True, default=0)
    _stack_info = attr.ib(type=Optional[List[Dict[str, Any]]], kw_only=True, default=None)

    @property
    def stack_info(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieve stack info of this report."""
        return self._stack_info

    def set_stack_info(self, stack_info: List[Dict[str, Any]]) -> None:
        """Set stack information."""
        self._stack_info = stack_info

    def to_dict(self, *, verbose: bool = False) -> Dict[str, Any]:
        """Convert pipeline report to a dict representation."""
        stack_info: List[Dict[str, Any]] = []
        stack_info_metadata = os.getenv("THOTH_ADVISER_METADATA")
        if stack_info_metadata:
            try:
                stack_info = ((json.loads(stack_info_metadata).get("thoth.adviser") or {}).get("stack_info")) or []
            except Exception:
                _LOGGER.exception("Failed to load adviser metadata")

        return {
            "pipeline": self.pipeline.to_dict() if verbose else None,
            "products": [product.to_dict() for product in self.products],
            "stack_info": stack_info + (self._stack_info or []),
            "resolver_iterations": self.resolver_iterations,
            "accepted_final_states_count": self.accepted_final_states_count,
            "discarded_final_states_count": self.discarded_final_states_count,
        }
