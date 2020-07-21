#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""Boot units for backports to older Python versions."""

from .enum34 import Enum34BackportBoot
from .importlib_metadata import ImportlibMetadataBackportBoot
from .importlib_resources import ImportlibResourcesBackportBoot
from .mock import MockBackportBoot

__all__ = [
    "Enum34BackportBoot",
    "ImportlibMetadataBackportBoot",
    "ImportlibResourcesBackportBoot",
    "MockBackportBoot",
]
