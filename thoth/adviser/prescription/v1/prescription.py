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

"""Implementation of a prescription abstraction."""

import logging
import os
import yaml
from collections import OrderedDict
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING

import attr

from ...exceptions import InternalError
from ...exceptions import PrescriptionDuplicateUnitNameError
from ...exceptions import PrescriptionSchemaError
from .schema import PRESCRIPTION_SCHEMA
from .boot import BootPrescription
from .pseudonym import PseudonymPrescription
from .sieve import SievePrescription
from .step import StepPrescription
from .stride import StridePrescription
from .wrap import WrapPrescription

if TYPE_CHECKING:
    from thoth.adviser.unit_types import UnitType  # noqa: F401
    from thoth.adviser.unit_types import BootType  # noqa: F401
    from thoth.adviser.unit_types import PseudonymType  # noqa: F401
    from thoth.adviser.unit_types import SieveType  # noqa: F401
    from thoth.adviser.unit_types import StepType  # noqa: F401
    from thoth.adviser.unit_types import StrideType  # noqa: F401
    from thoth.adviser.unit_types import WrapType  # noqa: F401


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Prescription:
    """Dynamically create pipeline units based on inscription."""

    _VALIDATE_PRESCRIPTION_SCHEMA = bool(int(os.getenv("THOTH_VALIDATE_PRESCRIPTION_SCHEMA", 1)))

    boots_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    pseudonyms_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    sieves_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    steps_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    strides_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    wraps_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))

    @classmethod
    def from_dict(
        cls, prescription: Dict[str, Any], *, prescription_instance: Optional["Prescription"] = None
    ) -> "Prescription":
        """Instantiate prescription from a dictionary representation.

        If an instance is provided, a safe merge will be performed.
        """
        if cls._VALIDATE_PRESCRIPTION_SCHEMA:
            _LOGGER.debug("Validating prescription schema")
            try:
                PRESCRIPTION_SCHEMA(prescription)
            except Exception as exc:
                _LOGGER.exception(
                    "Failed to validate schema for prescription: %s",
                    str(exc),
                )
                raise PrescriptionSchemaError(str(exc))

        _LOGGER.info("Using v1 prescription release %r", prescription["spec"]["release"])

        boots_dict = prescription_instance.boots_dict if prescription_instance is not None else OrderedDict()
        for boot_spec in prescription["spec"]["units"].get("boots") or []:
            name = f"prescription.{boot_spec['name']}"
            boot_spec["name"] = name
            if name in boots_dict:
                raise PrescriptionDuplicateUnitNameError(f"Boot with name {name!r} is already present")
            boots_dict[boot_spec["name"]] = boot_spec

        pseudonyms_dict = prescription_instance.pseudonyms_dict if prescription_instance else OrderedDict()
        for pseudonym_spec in prescription["spec"]["units"].get("pseudonyms") or []:
            name = f"prescription.{pseudonym_spec['name']}"
            pseudonym_spec["name"] = name
            if name in pseudonyms_dict:
                raise PrescriptionDuplicateUnitNameError(f"Pseudonym with name {name!r} is already present")
            pseudonyms_dict[pseudonym_spec["name"]] = pseudonym_spec

        sieves_dict = prescription_instance.sieves_dict if prescription_instance else OrderedDict()
        for sieve_spec in prescription["spec"]["units"].get("sieves") or []:
            name = f"prescription.{sieve_spec['name']}"
            sieve_spec["name"] = name
            if name in sieves_dict:
                raise PrescriptionDuplicateUnitNameError(f"Sieve with name {name!r} is already present")
            sieves_dict[sieve_spec["name"]] = sieve_spec

        steps_dict = prescription_instance.steps_dict if prescription_instance else OrderedDict()
        for step_spec in prescription["spec"]["units"].get("steps") or []:
            name = f"prescription.{step_spec['name']}"
            step_spec["name"] = name
            steps_dict[step_spec["name"]] = step_spec

        strides_dict = prescription_instance.strides_dict if prescription_instance else OrderedDict()
        for stride_spec in prescription["spec"]["units"].get("strides") or []:
            name = f"prescription.{stride_spec['name']}"
            stride_spec["name"] = name
            if name in strides_dict:
                raise PrescriptionDuplicateUnitNameError(f"Stride with name {name!r} is already present")
            strides_dict[stride_spec["name"]] = stride_spec

        wraps_dict = prescription_instance.wraps_dict if prescription_instance else OrderedDict()
        for wrap_spec in prescription["spec"]["units"].get("strides") or []:
            name = f"prescription.{wrap_spec['name']}"
            wrap_spec["name"] = name
            if name in wraps_dict:
                raise PrescriptionDuplicateUnitNameError(f"Wrap with name {name!r} is already present")
            wraps_dict[wrap_spec["name"]] = wrap_spec

        if prescription_instance:
            return prescription_instance

        return cls(
            boots_dict=boots_dict,
            pseudonyms_dict=pseudonyms_dict,
            sieves_dict=sieves_dict,
            steps_dict=steps_dict,
            strides_dict=strides_dict,
            wraps_dict=wraps_dict,
        )

    @classmethod
    def load(cls, *prescriptions: str) -> "Prescription":
        """Load prescription from files or from their YAML representation."""
        instance = None

        for prescription in prescriptions:
            if os.path.isfile(prescription):
                _LOGGER.info("Loading prescription %r", prescription)
                with open(prescription, "r") as config_file:
                    instance = cls.from_dict(yaml.safe_load(config_file), prescription_instance=instance)
            else:
                # Passed using string.
                instance = cls.from_dict(yaml.safe_load(prescription), prescription_instance=instance)

        if instance is None:
            raise InternalError("No prescription loaded")

        return instance

    @staticmethod
    def _iter_units(unit_class: Type["UnitType"], units: Dict[str, Any]) -> Generator[Type["UnitType"], None, None]:
        """Iterate over units registered."""
        for prescription in units.values():
            unit_class.set_prescription(prescription)

            yield unit_class

    def iter_boot_units(self) -> Generator[Type["BootType"], None, None]:
        """Iterate over prescription boot units registered in the prescription supplied."""
        return self._iter_units(BootPrescription, self.boots_dict)

    def iter_pseudonym_units(self) -> Generator[Type["PseudonymType"], None, None]:
        """Iterate over prescription pseudonym units registered in the prescription supplied."""
        return self._iter_units(PseudonymPrescription, self.pseudonyms_dict)

    def iter_sieve_units(self) -> Generator[Type["SieveType"], None, None]:
        """Iterate over prescription sieve units registered in the prescription supplied."""
        return self._iter_units(SievePrescription, self.sieves_dict)

    def iter_step_units(self) -> Generator[Type["StepType"], None, None]:
        """Iterate over prescription step units registered in the prescription supplied."""
        return self._iter_units(StepPrescription, self.steps_dict)

    def iter_stride_units(self) -> Generator[Type["StrideType"], None, None]:
        """Iterate over prescription stride units registered in the prescription supplied."""
        return self._iter_units(StridePrescription, self.strides_dict)

    def iter_wrap_units(self) -> Generator[Type["WrapType"], None, None]:
        """Iterate over prescription stride units registered in the prescription supplied."""
        return self._iter_units(WrapPrescription, self.wraps_dict)
