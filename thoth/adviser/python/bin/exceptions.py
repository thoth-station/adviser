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


"""Exceptions that can happen in libdependency_graph implementation."""


class DependencyGraphException(Exception):
    """A base class for dependency graph exception hierarchy."""


class PrematureStreamEndError(DependencyGraphException):
    """An exception raised if the stack stream was closed prematurely.

    This can happen for example due to OOM, which can kill stack producer. In that case we would like to
    report to user what we have computed so far.
    """
