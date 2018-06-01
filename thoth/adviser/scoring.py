#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import logging

from .enums import Ecosystem

_LOGGER = logging.getLogger(__name__)


def score_package_version(package_name: str,
                          package_version: str,
                          ecosystem: Ecosystem,
                          runtime_environment: str) -> bool:
    """Decide whether the given package should be included in the software stack."""
    # TODO: Check JanusGraph for stored observations
    return True
