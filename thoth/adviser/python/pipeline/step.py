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

"""Implementation a base class for a step in stack generation pipeline."""

import abc
import logging

import attr

from .step_context import StepContext
from .unit_base import PipelineUnitBase

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Step(PipelineUnitBase, metaclass=abc.ABCMeta):
    """A step in a stack generation pipeline."""

    @abc.abstractmethod
    def run(self, step_context: StepContext) -> None:
        """Entrypoint for a stack pipeline step."""
