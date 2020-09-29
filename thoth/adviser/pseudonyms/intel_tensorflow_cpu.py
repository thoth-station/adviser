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

"""A TensorFlow pseudonym."""

import logging

import attr

from .intel_tensorflow import IntelTensorFlowPseudonym

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class IntelTensorFlowCPUPseudonym(IntelTensorFlowPseudonym):
    """A TensorFlow pseudonym to map intel-tensorflow to tensorflow-cpu packages."""

    CONFIGURATION_DEFAULT = {"package_name": "tensorflow-cpu"}
