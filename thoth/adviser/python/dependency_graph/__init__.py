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

"""Implementation of dependency graphs for Thoth's adviser.

There are currently implemented two main dependency graphs which serve two different purposes:

 * dependency graph adaptation - this dependency graph can perform changes to dependency
                                 graph - score or remove certain pacakges, by scoring there is meant
                                 adjusting precedence of packages so that they are produced sooner in
                                 dependency graph walker
 * dependency graph walker - actually performs walking, in other words generating a sequence of resolved
                             software stacks
"""

from .adaptation import CannotRemovePackage
from .adaptation import DependencyGraphAdaptationException
from .adaptation import DependencyGraph as DependencyGraphAdaptation
from .adaptation import PackageNotFound
from .adaptation import RemoveMultiplePackages
from .adaptation import DependencyGraphTransaction
from .walking import DependenciesCountOverflow
from .walking import DependencyGraph as DependencyGraphWalker
from .walking import DependencyGraphWalkerException
from .walking import NoDependenciesError
from .walking import PrematureStreamEndError
