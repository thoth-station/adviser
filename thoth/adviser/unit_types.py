#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""Types of units."""

from typing import Union

from .pseudonym import Pseudonym
from .boot import Boot
from .sieve import Sieve
from .step import Step
from .stride import Stride
from .wrap import Wrap
from .unit import Unit

from thoth.adviser.prescription.v1.boot import BootPrescription as BootPrescriptionV1
from thoth.adviser.prescription.v1.pseudonym import PseudonymPrescription as PseudonymPrescriptionV1
from thoth.adviser.prescription.v1.sieve import SievePrescription as SievePrescriptionV1
from thoth.adviser.prescription.v1.step import StepPrescription as StepPrescriptionV1
from thoth.adviser.prescription.v1.stride import StridePrescription as StridePrescriptionV1
from thoth.adviser.prescription.v1.unit import UnitPrescription as UnitPrescriptionV1
from thoth.adviser.prescription.v1.wrap import WrapPrescription as WrapPrescriptionV1


UnitType = Union[Unit, UnitPrescriptionV1]
BootType = Union[Boot, BootPrescriptionV1]
PseudonymType = Union[Pseudonym, PseudonymPrescriptionV1]
SieveType = Union[Sieve, SievePrescriptionV1]
StepType = Union[Step, StepPrescriptionV1]
StrideType = Union[Stride, StridePrescriptionV1]
WrapType = Union[Wrap, WrapPrescriptionV1]
