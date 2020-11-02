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

"""Implementation of steps used during resolution."""

from .aicoe import AICoEReleasesStep
from .cve import CvePenalizationStep
from .dropout import DropoutStep
from .security_indicators import SecurityIndicatorStep
from .tensorflow import TensorFlow21Urllib3Step
from .tensorflow import TensorFlow22ProbabilityStep
from .tensorflow import TensorFlowAVX2Step
from .tensorflow import TensorFlow113NumPyStep
from .tensorflow import TensorFlow114GastStep
from .tensorflow import TensorFlow22NumPyStep
from .tensorflow import TensorFlowRemoveSciPyStep
from .tensorflow import TensorFlow21H5pyStep

from ._debug import GenerateScoreStep
from ._debug import MockScoreStep
from ._debug import SetScoreStep


# Relative ordering of units is relevant, as the order specifies order
# in which the asked to be registered - any dependencies between them
# can be mentioned here.
__all__ = [
    "AICoEReleasesStep",
    "CvePenalizationStep",
    "DropoutStep",
    "SecurityIndicatorStep",
    "MockScoreStep",
    "SetScoreStep",
    "GenerateScoreStep",
    "TensorFlow21Urllib3Step",
    "TensorFlow21H5pyStep",
    "TensorFlow22ProbabilityStep",
    "TensorFlowAVX2Step",
    "TensorFlow113NumPyStep",
    "TensorFlow114GastStep",
    "TensorFlow22NumPyStep",
    "TensorFlowRemoveSciPyStep",
]
