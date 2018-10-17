#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
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

"""Exceptions used within thoth-adviser package."""


class ThothAdviserException(Exception):
    """A base exception for this package."""


class PipfileParseError(ThothAdviserException):
    """An exception raised on invalid Pipfile or Pipfile.lock."""


class InternalError(ThothAdviserException):
    """An exception raised on bugs in the code base."""


class UnsupportedConfiguration(ThothAdviserException):
    """An exception raised on unsupported configuration by recommendation engine."""


class NotFound(ThothAdviserException):
    """An exception raised if the given resource was not found."""


class VersionIdentifierError(ThothAdviserException):
    """An exception raised if the given version identifier is not a semver identifier."""
