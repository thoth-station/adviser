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

"""Exception hierarchy used in the whole adviser implementation."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional


class AdviserException(Exception):  # noqa: N818
    """A base adviser exception in adviser's exception hierarchy."""


class NotAcceptable(AdviserException):  # noqa: N818
    """An exception raised during stack generation when the given action would produce un-acceptable solution."""


class SkipPackage(AdviserException):  # noqa: N818
    """An exception raised during stack generation when the given package should be skipped in the stack."""


class ParseBaseImageError(AdviserException):
    """An exception raised when parsing base image fails."""


class PipfileParseError(AdviserException):
    """An exception raised on invalid Pipfile or Pipfile.lock."""


class InternalError(AdviserException):
    """An exception raised on bugs in the code base."""


class UnsupportedConfiguration(AdviserException):  # noqa: N818
    """An exception raised on unsupported configuration by recommendation engine."""


class NotFound(AdviserException):  # noqa: N818
    """An exception raised if the given resource was not found."""


class VersionIdentifierError(AdviserException):
    """An exception raised if the given version identifier is not a semver identifier."""


class UnableLock(AdviserException):  # noqa: N818
    """Raised if it is unable to lock dependencies given the set of constraints."""


class NoHistoryKept(AdviserException):  # noqa: N818
    """Raised if a user asks for history, but history was not kept (e.g. temperature function history in annealing)."""


class AdviserPipelineException(AdviserException):  # noqa: N818
    """A base class for implementing pipeline specific exceptions."""


class EagerStopPipeline(AdviserPipelineException):  # noqa: N818
    """Raised to signalize premature end of pipeline."""


class PipelineUnitError(AdviserPipelineException):
    """An exception raised when there is an error during pipeline run, unexpectedly."""


class PipelineUnitConfigurationSchemaError(PipelineUnitError):
    """An exception raised when pipeline unit configuration does not match schema declared."""


class PrescriptionSchemaError(PipelineUnitError):
    """An exception raised when prescription schema is not valid."""


class PrescriptionDuplicateUnitNameError(PipelineUnitError):
    """An exception raised when multiple prescription units share name."""


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


class UnknownPipelineUnitError(PipelineUnitError):
    """An exception raised when an unknown pipeline unit is requested."""


class PipelineConfigurationError(PipelineUnitError):
    """An exception raised when a wrong pipeline unit configuration supplied.

    Or any error during configuration initialization.
    """


class AdviserRunException(AdviserException):  # noqa: N818
    """A base class for implementing exceptions occurred during an andviser run."""

    def to_dict(self) -> Optional[Dict[str, str]]:
        """Convert adviser exception to a dict representation which is shown to the user."""
        return None


class UnresolvedDependencies(AdviserRunException):  # noqa: N818
    """An exception raised if dependencies were not resolved and cannot produce stack."""

    __slots__ = ["unresolved", "stack_info"]

    def __init__(self, *args: Any, unresolved: List[str], stack_info: List[Dict[str, Any]]) -> None:
        """Capture unresolved dependencies in this exception."""
        super().__init__(*args)
        self.unresolved = unresolved
        self.stack_info = stack_info

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """Convert unresolved dependencies exception to the user."""
        return {
            "ERROR": "No dependencies found for "
            f"{', '.join(f'{dep!r}' for dep in self.unresolved)}: these "
            "dependencies were not yet analyzed in Thoth - "
            "visit https://tinyurl.com/thoth-unresolved to request analyses",
            "_ERROR_DETAILS": {
                "unresolved": self.unresolved,
            },
            "stack_info": self.stack_info,
        }


class CannotProduceStack(AdviserRunException):  # noqa: N818
    """Raised if there was not produced any result."""

    __slots__ = ["stack_info"]

    def __init__(self, *args: Any, stack_info: List[Dict[str, Any]]) -> None:
        """Instantiate the exception."""
        super().__init__(*args)
        self.stack_info: List[Dict[str, Any]] = stack_info

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """Convert exception to a dict representation for a user."""
        return {
            "ERROR": "No results were resolved, see logs for more info",
            "stack_info": self.stack_info,
        }


class UserLockFileError(AdviserRunException):
    """An exception raised when the supplied user stack has issues."""
