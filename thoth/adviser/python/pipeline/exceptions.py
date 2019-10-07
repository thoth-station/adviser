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

"""Exceptions hierarchy used inside stack generation pipeline.

These exceptions should not be propagated outside of pipeline module.
"""


class PipelineExceptionBase(Exception):
    """An exception raised inside stack generator pipeline."""


class StrideRemoveStack(PipelineExceptionBase):
    """Raised from within a stride if the given stack should be removed."""


class CannotRemovePackage(PipelineExceptionBase):
    """Raised if the given package cannot be removed from paths due to dependencies."""


class PackageNotFound(PipelineExceptionBase):
    """Raised if the given package cannot be found (mostly internal error)."""


class NotAICoERelease(PipelineExceptionBase):
    """Raised if the given package is not AICoE release."""


class NotResolvedError(PipelineExceptionBase):
    """Raised if trying to run stack generation pipeline without fully resolved dependency.

    As produced stacks should be fully resolved, packages which are not resolved yet should be filtered
    out in the pipeline units.
    """
