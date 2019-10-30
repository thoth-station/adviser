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

"""A base class for implementing sieves."""

from typing import Any
from typing import Dict
from typing import List

from .boot import Boot
from .sieve import Sieve
from .step import Step
from .stride import Stride
from .wrap import Wrap

import attr


@attr.s(slots=True)
class PipelineConfig:
    """A configuration of a pipline for dependency-monkey and for adviser."""

    boots = attr.ib(type=List[Boot], default=attr.Factory(list))
    sieves = attr.ib(type=List[Sieve], default=attr.Factory(list))
    steps = attr.ib(type=List[Step], default=attr.Factory(list))
    strides = attr.ib(type=List[Stride], default=attr.Factory(list))
    wraps = attr.ib(type=List[Wrap], default=attr.Factory(list))

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return this pipeline configuration in a dict representation."""
        return {
            "boots": [boot.to_dict() for boot in self.boots],
            "sieves": [sieve.to_dict() for sieve in self.sieves],
            "steps": [step.to_dict() for step in self.steps],
            "strides": [stride.to_dict() for stride in self.strides],
            "wraps": [wrap.to_dict() for wrap in self.wraps],
        }
