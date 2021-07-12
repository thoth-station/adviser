#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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

"""A base class for implementing adviser's test cases."""

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
import os

from voluptuous import All
from voluptuous import Any as SchemaAny
from voluptuous import Invalid
from voluptuous import Length
from voluptuous import Optional as SchemaOptional
from voluptuous import Schema
import pytest

from thoth.adviser.boot import Boot
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.pseudonym import Pseudonym
from thoth.adviser.sieve import Sieve
from thoth.adviser.step import Step
from thoth.adviser.stride import Stride
from thoth.adviser.unit import Unit
from thoth.adviser.wrap import Wrap


class AdviserTestCaseException(Exception):  # noqa: N818
    """A base class for exceptions that can occur in the test suite."""


class AdviserJustificationSchemaError(AdviserTestCaseException):
    """An exception raised when the justification reported violates schema."""


class AdviserTestCase:
    """A base class for implementing adviser's test cases."""

    data_dir = Path(os.path.dirname(os.path.realpath(__file__))) / "data"

    JUSTIFICATION_SAMPLE_1 = [
        {"message": "Justification sample 1", "type": "WARNING", "link": "https://thoth-station.ninja"},
        {"message": "Justification sample 1", "type": "INFO", "link": "https://thoth-station.ninja"},
        {"message": "Justification sample 1", "type": "ERROR", "link": "https://thoth-station.ninja"},
    ]

    JUSTIFICATION_SAMPLE_2 = [
        {
            "message": "Justification sample 2",
            "type": "INFO",
            "link": "https://thoth-station.ninja",
            "advisory": "Bark!",
        },
    ]

    JUSTIFICATION_SAMPLE_3 = [
        {
            "message": "Justification sample 2",
            "type": "INFO",
            "link": "https://thoth-station.ninja",
            "package_name": "tensorflow",
            "version_range": "<2.3>=",
        },
    ]

    _JUSTIFICATION_SCHEMA = Schema(
        [
            {
                "message": All(str, Length(min=1)),
                "type": SchemaAny("INFO", "WARNING", "ERROR", "LATEST", "CVE"),
                "link": All(str, Length(min=1)),
                SchemaOptional("advisory"): All(str, Length(min=1)),
                SchemaOptional("cve_id"): All(str, Length(min=1)),
                SchemaOptional("cve_name"): All(str, Length(min=1)),
                SchemaOptional("package_name"): All(str, Length(min=1)),
                SchemaOptional("version_range"): All(str, Length(min=1)),
            }
        ]
    )

    @classmethod
    def verify_justification_schema(cls, justification: Optional[List[Dict[str, Any]]]) -> bool:
        """Verify the justification schema is correct."""
        if justification is None:
            return True

        try:
            cls._JUSTIFICATION_SCHEMA(justification)
        except Invalid as exc:
            raise AdviserJustificationSchemaError(exc.msg) from exc
        else:
            return True


class AdviserUnitTestCase(AdviserTestCase):
    """A base class for implementing pipeline unit specific test cases."""

    UNIT_TESTED: Optional[Unit] = None

    @classmethod
    def verify_multiple_should_include(cls, builder_context: PipelineBuilderContext) -> bool:
        """Check multiple should_include calls do not end in an infinite loop."""
        assert cls.UNIT_TESTED is not None, "No unit assigned for testing"
        pipeline_config = list(cls.UNIT_TESTED.should_include(builder_context))
        assert pipeline_config != [], "First call to should_include should be always non-empty generator"
        assert (
            len(pipeline_config) == 1
        ), "First call to should_include should return one config, adjust the test if it requires additional logic"

        unit = cls.UNIT_TESTED()
        unit.update_configuration(pipeline_config[0])

        builder_context.add_unit(unit)
        assert (
            list(cls.UNIT_TESTED.should_include(builder_context)) == []
        ), "Make sure the pipeline unit does not loop endlessly on multiple should_include calls"
        return True

    def test_verify_multiple_should_include(self, *args, **kwargs) -> bool:
        """Check multiple should_include calls do not end in an infinite loop."""
        # Construct a builder context that should always include a pipeline unit and pass
        # it to verify_multiple_should_include
        raise NotImplementedError(
            "Implement a test that makes sure multiple calls of should include do not loop endlessly"
        )

    def test_provided_unit_tested(self):
        """Check proper manipulation of the unit tested."""
        assert self.UNIT_TESTED is not None, "Unit tested not provided for the test base"
        assert issubclass(
            self.UNIT_TESTED, (Boot, Sieve, Pseudonym, Step, Stride, Wrap)
        ), f"Assigned unit for testing {self.UNIT_TESTED.__name__!r} does not inherit from any known pipeline unit type"

    def test_provided_package_version(self) -> None:
        """Test the unit provides package_name."""
        if self.UNIT_TESTED is None or not issubclass(self.UNIT_TESTED, (Pseudonym, Sieve, Step)):
            return pytest.skip("Unit does not type is not specific for any package version")

        unit = self.UNIT_TESTED()

        if isinstance(unit, Pseudonym):
            assert (
                isinstance(unit.configuration.get("package_name"), str) and len(unit.configuration["package_name"]) > 0
            ), (
                f"Pseudonym unit {self.UNIT_TESTED.__name__!r} does not provide required "
                "package_version configuration option"
            )
        else:
            assert (
                "package_name" in unit.configuration
            ), "It's a good practice to state package_name in the unit configuration"

            package_name = unit.configuration["package_name"]
            if package_name is not None:
                assert (
                    isinstance(package_name, str) and len(unit.configuration["package_name"]) > 0
                ), f"Unit {self.UNIT_TESTED.__name__!r} does not provide required package_version configuration option"

    def test_default_configuration(self) -> None:
        """Test instantiation the pipeline unit succeeds with default configuration."""
        unit_instance = self.UNIT_TESTED()
        unit_instance.update_configuration({})

    def test_super_pre_run(self, context: Context) -> None:
        """Make sure the pre-run method of the base is called."""
        if self.UNIT_TESTED is None or not issubclass(self.UNIT_TESTED, (Pseudonym, Sieve, Step)):
            return pytest.skip("Unit does not type is not specific for any package version")

        unit = self.UNIT_TESTED()

        assert unit.unit_run is False
        unit.unit_run = True

        with unit.assigned_context(context):
            unit.pre_run()

        assert (
            unit.unit_run is False
        ), "Unit flag unit_run not reset, is super().pre_run() called in sources when providing pre_run method!?"

    def test_default_multi_package_resolution(self) -> None:
        """Test presence of multi_package_resolution in unit default."""
        if self.UNIT_TESTED is None or not issubclass(self.UNIT_TESTED, Step):
            return pytest.skip("Only Step pipeline units should include multi_package_resolution option")

        assert (
            "multi_package_resolution" in self.UNIT_TESTED.CONFIGURATION_DEFAULT
        ), "Make sure the multi_package_resolution option is present in step unit default configuration"
        assert isinstance(self.UNIT_TESTED.CONFIGURATION_DEFAULT.get("multi_package_resolution"), bool)
