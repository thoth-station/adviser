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

"""Implementation a base class for a stride types in stack generation pipeline."""

import abc
import logging

import attr

from .stride_context import StrideContext
from .unit_base import PipelineUnitBase

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SerialStride(PipelineUnitBase, metaclass=abc.ABCMeta):
    """A stride in a stack generation pipeline.

    This stride is executed in a serialized manner - meaning all strides which are
    considered as serial strides are executed one after another in the pipeline.
    """

    @abc.abstractmethod
    def run(self, stride_context: StrideContext) -> None:
        """Entrypoint for a serial stride in stack generation pipeline."""


@attr.s(slots=True)
class AsyncStride(PipelineUnitBase, metaclass=abc.ABCMeta):
    """A stride in a stack generation pipeline.

    This stride is executed as async stride - these type of strides are
    especially useful when querying knowledge base so that pipeline can benefit
    from asyncio.
    """

    @abc.abstractmethod
    async def run(self, stride_context: StrideContext) -> None:
        """Entrypoint for an async stride in stack generation pipeline."""
