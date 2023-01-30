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
import pickle
import yaml
from itertools import chain

from collections import OrderedDict, defaultdict
from collections import deque
from typing import Any
from typing import List
from typing import Tuple
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING

from voluptuous.humanize import humanize_error
import voluptuous
import attr

from ...exceptions import InternalError
from ...exceptions import PrescriptionSchemaError
from .add_package_step import AddPackageStepPrescription
from .boot import BootPrescription
from .gh_release_notes import GHReleaseNotesWrapPrescription
from .group import GroupStepPrescription
from .pseudonym import PseudonymPrescription
from .schema import PRESCRIPTION_SCHEMA
from .sieve import SievePrescription
from .skip_package_sieve import SkipPackageSievePrescription
from .skip_package_step import SkipPackageStepPrescription
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

    _PRESCRIPTION_METADATA_FILE = "_prescription_metadata.yaml"
    _PRESCRIPTION_DEFAULT_NAME = "UNKNOWN"
    _PRESCRIPTION_DEFAULT_RELEASE = "UNKNOWN"
    _VALIDATE_PRESCRIPTION_SCHEMA = bool(int(os.getenv("THOTH_ADVISER_VALIDATE_PRESCRIPTION_SCHEMA", 1)))

    prescriptions = attr.ib(type=List[Tuple[str, str]], kw_only=True, default=attr.Factory(list))

    boots_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    pseudonyms_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    sieves_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    steps_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    strides_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    wraps_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))

    @property
    def units(self) -> Generator[Dict[str, Any], None, None]:
        """Iterate over units."""
        yield from chain(
            self.boots_dict.values(),
            self.pseudonyms_dict.values(),
            self.sieves_dict.values(),
            self.steps_dict.values(),
            self.strides_dict.values(),
            self.wraps_dict.values(),
        )

    @classmethod
    def validate(cls, prescriptions: Iterable[str], any_error_fatal: bool = True) -> "Prescription":
        """Validate the given prescription."""
        _LOGGER.debug("Validating prescriptions schema")

        prescription_instance = cls.load(prescriptions, any_error_fatal)

        # Drop any metadata associated to save space.
        for unit in prescription_instance.units:
            unit.pop("metadata", None)

        return prescription_instance

    @classmethod
    def from_dict(
        cls,
        prescription: Dict[str, Any],
        *,
        prescription_instance: Optional["Prescription"] = None,
        prescription_name: str,
        prescription_release: str,
    ) -> "Prescription":
        """Instantiate prescription from a dictionary representation.

        If an instance is provided, a safe merge will be performed.
        """
        try:
            PRESCRIPTION_SCHEMA(prescription)
        except voluptuous.error.Invalid as exc:
            raise PrescriptionSchemaError(humanize_error(prescription, exc))

        unit_types = set(prescription["units"].keys())
        prescriptions = []
        if prescription_instance:

            unit_types.update(
                unit_name[: -len("_dict")]
                for unit_name in dir(prescription_instance)
                if (unit_name.endswith("s_dict") and getattr(prescription_instance, unit_name))
            )
            prescription["units"] = defaultdict(list, prescription["units"])
            for unit_type in unit_types:
                prescription["units"][unit_type] += [
                    {"name": name[len(prescription_name) + 1 :], **v}
                    # Slice off f"{prescription_name}."
                    for name, v in getattr(prescription_instance, f"{unit_type}_dict").items()
                ]

        if prescription_instance:
            # Adjust release info at the end once successful.
            prescription_meta = (prescription_name, prescription_release)
            if prescription_meta not in prescription_instance.prescriptions:
                prescription_instance.prescriptions.append(prescription_meta)
            prescriptions = prescription_instance.prescriptions
        else:
            prescriptions = [prescription_meta]

        return cls(
            **{
                f"{unit_type}_dict": {
                    f"{prescription_name}.{values['name']}": dict(
                        values, **{"name": f"{prescription_name}.{values['name']}"}
                    )
                    for values in prescription["units"][unit_type]
                }
                for unit_type in prescription["units"].keys()
            },
            prescriptions=prescriptions,
        )

    def is_empty(self) -> bool:
        """Check if no prescription units are loaded."""
        return (
            not self.boots_dict
            and not self.pseudonyms_dict
            and not self.sieves_dict
            and not self.steps_dict
            and not self.strides_dict
            and not self.wraps_dict
        )

    @classmethod
    def load(cls, prescriptions: Iterable[str], any_error_fatal: bool = True) -> "Prescription":
        """Load prescription from files or from their YAML representation."""
        queue = deque([(p, cls._PRESCRIPTION_DEFAULT_NAME, cls._PRESCRIPTION_DEFAULT_RELEASE) for p in prescriptions])
        prescription_instance = Prescription()

        while queue:
            prescription, prescription_name, prescription_release = queue.popleft()

            if os.path.isfile(prescription):
                if prescription.endswith((".yaml", ".yml")):
                    _LOGGER.debug("Loading prescriptions from %r", prescription)
                    with open(prescription, "r") as config_file:
                        try:
                            prescription_instance = cls.from_dict(
                                yaml.load(config_file, Loader=yaml.CLoader),
                                prescription_instance=prescription_instance,
                                prescription_name=prescription_name,
                                prescription_release=prescription_release,
                            )
                        except Exception as e:
                            if any_error_fatal:
                                _LOGGER.error("Failed to load prescription from %r", prescription)
                                raise
                            else:
                                _LOGGER.error("%s is invalid:\n%s", prescription, str(e))
                elif prescription.endswith(".pickle"):
                    _LOGGER.debug("Loading prescriptions from %r", prescription)
                    with open(prescription, "rb") as fp:
                        prescription_instance = pickle.load(fp)

                    for prescription_info in prescription_instance.prescriptions:
                        _LOGGER.info(
                            "Loaded prescriptions %r in version %r", prescription_info[0], prescription_info[1]
                        )
                else:
                    _LOGGER.debug("Skipping file %r: not a YAML nor Pickle file", prescription)
                    continue

            elif os.path.isdir(prescription):
                prescription_metadata_file_path = os.path.join(prescription, cls._PRESCRIPTION_METADATA_FILE)
                if os.path.isfile(prescription_metadata_file_path):
                    with open(prescription_metadata_file_path) as f:
                        _LOGGER.debug("Loading prescription metadata file %r", prescription_metadata_file_path)
                        metadata = yaml.safe_load(f)

                        prescription_name = metadata.get("prescription", {}).get("name", cls._PRESCRIPTION_DEFAULT_NAME)
                        if prescription_name == cls._PRESCRIPTION_DEFAULT_NAME:
                            _LOGGER.warning("No prescription name parsed from %r", prescription_metadata_file_path)

                        prescription_release = metadata.get("prescription", {}).get(
                            "release", cls._PRESCRIPTION_DEFAULT_RELEASE
                        )
                        if prescription_release == cls._PRESCRIPTION_DEFAULT_RELEASE:
                            _LOGGER.warning("No prescription release parsed from %r", prescription_metadata_file_path)

                        _LOGGER.info("Using prescriptions %r release %r", prescription_name, prescription_release)

                for file_ in os.listdir(prescription):
                    if file_ == cls._PRESCRIPTION_METADATA_FILE:
                        continue

                    if file_.startswith("."):
                        _LOGGER.debug("Skipping hidden file or directory %r", file_)
                        continue

                    queue.append((os.path.join(prescription, file_), prescription_name, prescription_release))
            else:
                # Passed using string.
                prescription_instance = cls.from_dict(
                    yaml.safe_load(prescription),
                    prescription_instance=prescription_instance,
                    prescription_name=prescription_name,
                    prescription_release=prescription_release,
                )

        if prescription_instance.is_empty():
            raise InternalError("No prescription loaded")

        return prescription_instance

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
        for prescription in self.sieves_dict.values():
            if prescription["type"] == "sieve":
                SievePrescription.set_prescription(prescription)
                yield SievePrescription
            elif prescription["type"] == "sieve.SkipPackage":
                SkipPackageSievePrescription.set_prescription(prescription)
                yield SkipPackageSievePrescription
            else:
                raise ValueError(f"Unknown sieve pipeline unit type: {prescription['type']!r}")

    def iter_step_units(self) -> Generator[Type["StepType"], None, None]:
        """Iterate over prescription step units registered in the prescription supplied."""
        for prescription in self.steps_dict.values():
            if prescription["type"] == "step":
                StepPrescription.set_prescription(prescription)
                yield StepPrescription
            elif prescription["type"] == "step.SkipPackage":
                SkipPackageStepPrescription.set_prescription(prescription)
                yield SkipPackageStepPrescription
            elif prescription["type"] == "step.AddPackage":
                AddPackageStepPrescription.set_prescription(prescription)
                yield AddPackageStepPrescription
            elif prescription["type"] == "step.Group":
                GroupStepPrescription.set_prescription(prescription)
                yield GroupStepPrescription
            else:
                raise ValueError(f"Unknown step pipeline unit type: {prescription['type']!r}")

    def iter_stride_units(self) -> Generator[Type["StrideType"], None, None]:
        """Iterate over prescription stride units registered in the prescription supplied."""
        return self._iter_units(StridePrescription, self.strides_dict)

    def iter_wrap_units(self) -> Generator[Type["WrapType"], None, None]:
        """Iterate over prescription stride units registered in the prescription supplied."""
        for prescription in self.wraps_dict.values():
            if prescription["type"] == "wrap":
                WrapPrescription.set_prescription(prescription)
                yield WrapPrescription
            elif prescription["type"] == "wrap.GHReleaseNotes":
                GHReleaseNotesWrapPrescription.set_prescription(prescription)
                yield GHReleaseNotesWrapPrescription
            else:
                raise ValueError(f"Unknown wrap pipeline unit type: {prescription['type']!r}")
