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

"""Exception hierarchy used in the whole adviser implementation."""

from typing import Any
from typing import List


class AdviserException(Exception):
    """A base adviser exception in adviser's exception hierarchy."""


class NotAcceptable(AdviserException):
    """An exception raised during stack generation when the given  action would produce un-acceptable solution."""


class PipfileParseError(AdviserException):
    """An exception raised on invalid Pipfile or Pipfile.lock."""


class InternalError(AdviserException):
    """An exception raised on bugs in the code base."""


class UnsupportedConfiguration(AdviserException):
    """An exception raised on unsupported configuration by recommendation engine."""


class NotFound(AdviserException):
    """An exception raised if the given resource was not found."""


class VersionIdentifierError(AdviserException):
    """An exception raised if the given version identifier is not a semver identifier."""


class UnableLock(AdviserException):
    """Raised if it is unable to lock dependencies given the set of constraints."""


class CannotProduceStack(AdviserException):
    """Raised if adviser or dependency monkey cannot produce stack."""


class NoHistoryKept(AdviserException):
    """Raised if a user asks for history, but history was not kept (e.g. temperature function history in annealing)."""


class AdviserPipelineException(AdviserException):
    """A base class for implementing pipeline specific exceptions."""


class EagerStopPipeline(AdviserPipelineException):
    """Raised to signalize premature end of pipeline."""


class PipelineUnitError(AdviserPipelineException):
    """An exception raised when there is an error during pipeline run, unexpectedly."""


class BootError(PipelineUnitError):
    """An exception raised when pipeline boot unit fails unexpectedly."""


class SieveError(PipelineUnitError):
    """An exception raised when pipeline sieve unit fails unexpectedly."""


class StepError(PipelineUnitError):
    """An exception raised when pipeline step unit fails unexpectedly."""


class StrideError(PipelineUnitError):
    """An exception raised when pipeline stride unit fails unexpectedly."""


class WrapError(PipelineUnitError):
    """An exception raised when pipeline stride unit fails unexpectedly."""


class UnresolvedDependencies(AdviserException):
    """An exception raised if dependencies were not resolved and cannot produce stack."""

    __slots__ = ["unresolved"]

    def __init__(self, *args: Any, unresolved: List[str]) -> None:
        """Capture unresolved dependencies in this exception."""
        super().__init__(*args)
        self.unresolved = unresolved
