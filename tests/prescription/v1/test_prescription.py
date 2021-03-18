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

"""Test implementation of prescription handling."""

import pytest

from thoth.adviser.exceptions import PrescriptionSchemaError
from thoth.adviser.exceptions import PrescriptionDuplicateUnitNameError
from thoth.adviser.prescription import Prescription

from ...base import AdviserTestCase


class TestPrescription(AdviserTestCase):
    """Test implementation of prescription handling."""

    def test_load(self) -> None:
        """Test loading prescription."""
        prescription_path = str(self.data_dir / "prescriptions" / "basic.yaml")
        instance = Prescription.load(prescription_path)
        assert instance is not None
        assert list(instance.boots_dict) == ["prescription.BootUnit"]
        assert list(instance.pseudonyms_dict) == ["prescription.PseudonymUnit"]
        assert list(instance.sieves_dict) == ["prescription.SieveUnit"]
        assert list(instance.steps_dict) == ["prescription.StepUnit"]
        assert list(instance.strides_dict) == ["prescription.StrideUnit"]
        assert list(instance.wraps_dict) == ["prescription.WrapUnit"]

        assert [u.get_unit_name() for u in instance.iter_boot_units()] == ["prescription.BootUnit"]
        assert [u.get_unit_name() for u in instance.iter_pseudonym_units()] == ["prescription.PseudonymUnit"]
        assert [u.get_unit_name() for u in instance.iter_sieve_units()] == ["prescription.SieveUnit"]
        assert [u.get_unit_name() for u in instance.iter_step_units()] == ["prescription.StepUnit"]
        assert [u.get_unit_name() for u in instance.iter_stride_units()] == ["prescription.StrideUnit"]
        assert [u.get_unit_name() for u in instance.iter_wrap_units()] == ["prescription.WrapUnit"]

    def test_from_dict_validate_error(self) -> None:
        """Test raising an error if schema validation fails."""
        with pytest.raises(PrescriptionSchemaError):
            Prescription.from_dict({"foo": "bar"})

    def test_from_dict_duplicate_name_error(self) -> None:
        """Test raising duplicate error if unit names clash."""
        unit = {
            "name": "BootUnit",
            "type": "boot",
            "should_include": {"adviser_pipeline": True},
            "run": {"log": {"message": "Some text printed", "type": "INFO"}},
        }

        prescription = {
            "apiVersion": "thoth-station.ninja/v1",
            "kind": "prescription",
            "spec": {
                "release": "2021.03.30",
                "units": {
                    "boots": [unit, dict(unit)],
                },
            },
        }

        with pytest.raises(PrescriptionDuplicateUnitNameError):
            Prescription.from_dict(prescription)
