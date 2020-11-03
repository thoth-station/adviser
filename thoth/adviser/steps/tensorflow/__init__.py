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

"""Implementation of steps used, specific for TensorFlow."""

from .tf_113_numpy import TensorFlow113NumPyStep
from .tf_114_gast import TensorFlow114GastStep
from .tf_21_h5py import TensorFlow21H5pyStep
from .tf_21_urllib3 import TensorFlow21Urllib3Step
from .tf_22_numpy import TensorFlow22NumPyStep
from .tf_22_prob import TensorFlow22ProbabilityStep
from .tf_avx2 import TensorFlowAVX2Step
from .tf_rm_scipy import TensorFlowRemoveSciPyStep


__all__ = [
    "TensorFlow113NumPyStep",
    "TensorFlow114GastStep",
    "TensorFlow21H5pyStep",
    "TensorFlow21Urllib3Step",
    "TensorFlow22NumPyStep",
    "TensorFlow22ProbabilityStep",
    "TensorFlowAVX2Step",
    "TensorFlowRemoveSciPyStep",
]
