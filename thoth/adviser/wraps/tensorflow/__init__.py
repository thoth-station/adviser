#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Implementation of wraps used, specific for TensorFlow."""

from .tf_23_accuracy import TensorFlow23Accuracy
from .tf_23_dict_bug import TensorFlow23DictSummary
from .tf_38518 import TensorFlowMultipleProcessesGPUBug
from .tf_42475 import TensorFlowSlowKerasEmbedding
from .tf_intel import IntelTensorFlowWrap
from .tf_mkl_threads import MKLThreadsWrap

__all__ = [
    "TensorFlow23DictSummary",
    "TensorFlow23Accuracy",
    "IntelTensorFlowWrap",
    "MKLThreadsWrap",
    "TensorFlowMultipleProcessesGPUBug",
    "TensorFlowSlowKerasEmbedding",
]
