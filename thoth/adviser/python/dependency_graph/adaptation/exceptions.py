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

"""Exceptions hierarchy for dependency graph adaptation."""


class DependencyGraphAdaptationException(Exception):
    """A top-class exception in dependency graph hierarchy."""


class CannotRemovePackage(DependencyGraphAdaptationException):
    """Raised if the given package cannot be removed."""


class RemoveMultiplePackages(DependencyGraphAdaptationException):
    """Raised if requested to remove a single package but multiple would be removed."""


class PackageNotFound(DependencyGraphAdaptationException):
    """Raised if the given package cannot be removed."""


class TransactionExpired(DependencyGraphAdaptationException):
    """Raised if the given transaction has been committed or rolled back."""
