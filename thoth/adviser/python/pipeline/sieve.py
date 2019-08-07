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

"""A base class for implementing sieves to filter out direct dependencies."""

import abc

import attr

from .unit_base import PipelineUnitBase
from .sieve_context import SieveContext


@attr.s(slots=True)
class Sieve(PipelineUnitBase, metaclass=abc.ABCMeta):
    """Filter out direct dependencies based on the given criteria."""

    @abc.abstractmethod
    def run(self, sieve_context: SieveContext) -> None:
        """Filter out package versions based on sieve implementation."""
        # Even though this class derives from PipelineUnitBase, the run method has a different
        # signature - this should be fixed.
        raise NotImplementedError
