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

"""JSON schema for pipeline unit prescription in version v1."""

import re
from urllib.parse import urlparse

from voluptuous import All
from voluptuous import Any
from voluptuous import Invalid
from voluptuous import Length
from voluptuous import Optional
from voluptuous import Range
from voluptuous import Required
from voluptuous import Schema

from packaging.specifiers import SpecifierSet
from packaging.specifiers import InvalidSpecifier

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType


_MIN_NAME_LENGTH = 1

PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA = Schema(
    {
        Optional("times", default=1): All(int, Range(min=0, max=1)),
        Required("adviser_pipeline"): bool,
        Required("dependency_monkey_pipeline"): bool,
        Optional("dependencies"): Schema(
            {
                "boots": [str],
                "pseudonyms": [str],
                "sieves": [str],
                "steps": [str],
                "strides": [str],
                "wraps": [str],
            }
        ),
        Optional("recommendation_types"): list(map(str.lower, RecommendationType.__members__.keys())),
        Optional("decision_types"): list(map(str.lower, DecisionType.__members__.keys())),
        Optional("runtime_environment"): Schema(
            {
                Optional("operating_system"): Schema(
                    {
                        Optional("name"): str,
                        Optional("version"): str,
                    }
                ),
                Optional("hardware"): Schema(
                    {
                        Optional("cpu_family"): int,
                        Optional("cpu_model"): int,
                        Optional("gpu_model"): str,
                    }
                ),
                Optional("python_version"): str,
                Optional("cuda_version"): str,
                Optional("platform"): str,
                Optional("openblas_version"): str,
                Optional("openmpi_version"): str,
                Optional("cudnn_version"): str,
                Optional("mkl_version"): str,
                Optional("base_image"): str,
            }
        ),
    }
)

_UNIT_SCHEMA_BASE_DICT = {
    Required("name"): All(str, Length(min=_MIN_NAME_LENGTH)),
    Required("should_include"): PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA,
}


def _justification_link():
    """Validator for a justification link."""

    def validator(v: str):
        if v.startswith(("https://", "http://")):
            return urlparse("http://www.cwi.nl:80/%7Eguido/Python.html")
        else:
            return re.match(r"[a-z0-9_-]+", v)

    return validator


STACK_INFO_SCHEMA = Schema(
    {
        Required("type"): Any("WARNING", "INFO", "ERROR"),
        Required("message"): str,
        Required("link"): _justification_link(),
    }
)


JUSTIFICATION_SCHEMA = STACK_INFO_SCHEMA


_UNIT_RUN_SCHEMA_BASE_DICT = {
    Optional("stack_info"): [STACK_INFO_SCHEMA],
    Optional("log"): Schema(
        {
            Required("text"): All(str, Length(min=1)),
            Required("type"): Any("WARNING", "INFO", "ERROR"),
        }
    ),
}


def _locked_version():
    """Validator for a locked version."""

    def validator(v: str):
        if not isinstance(v, str) or not v.startswith("==") and not v.startswith("==="):
            raise Invalid(f"Value {v!r} is not valid locked version (example: '==1.0.0')")

    return validator


PACKAGE_VERSION_LOCKED_SCHEMA = Schema(
    {
        Required("name"): Optional(str),
        Required("locked_version"): _locked_version(),
        Required("index_url"): Optional(str),
    }
)


def _specifier_set():
    """Validator for a specifier set."""

    def validator(v):
        if not isinstance(v, str):
            raise Invalid(f"Value {v!r} is not valid version specifier (example: '<1.0>=0.5')")
        try:
            SpecifierSet(v)
        except InvalidSpecifier as exc:
            raise Invalid(str(exc))

    return validator


PACKAGE_VERSION_SCHEMA = Schema(
    {
        Optional("name"): Optional(str),
        Optional("version"): _specifier_set(),
        Optional("index_url"): Optional(str),
    }
)


PACKAGE_VERSION_REQUIRED_NAME_SCHEMA = Schema(
    {
        Required("name"): All(str, Length(min=1)),
        Optional("version"): _specifier_set(),
        Optional("index_url"): Optional(str),
    }
)

#
# Boot unit.
#

PRESCRIPTION_BOOT_RUN_SCHEMA = Schema(
    {
        Optional("match"): Schema({"package_name": Optional(All(str, Length(min=1)))}),
        Optional("not_acceptable"): All(str, Length(min=1)),
        Optional("eager_stop_pipeline"): All(str, Length(min=1)),
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_BOOT_SCHEMA = Schema(
    {
        Required("run"): PRESCRIPTION_BOOT_RUN_SCHEMA,
        Required("type"): "boot",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Pseudonym unit.
#

PRESCRIPTION_PSEUDONYM_RUN_SCHEMA = Schema(
    {
        Required("match"): PACKAGE_VERSION_REQUIRED_NAME_SCHEMA,
        Required("yield"): PACKAGE_VERSION_LOCKED_SCHEMA,
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_PSEUDONYM_SCHEMA = Schema(
    {
        Required("run"): PRESCRIPTION_PSEUDONYM_RUN_SCHEMA,
        Required("type"): "pseudonym",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Sieve unit.
#

PRESCRIPTION_SIEVE_RUN_SCHEMA = Schema(
    {
        Required("match"): Schema({"package_version": PACKAGE_VERSION_SCHEMA}),
        Required("sieve_matched"): bool,
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)


PRESCRIPTION_SIEVE_SCHEMA = Schema(
    {
        Required("run"): PRESCRIPTION_SIEVE_RUN_SCHEMA,
        Required("type"): "sieve",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Step unit.
#

PRESCRIPTION_STEP_RUN_SCHEMA = Schema(
    {
        Required("match"): Schema(
            {
                Required("package_version"): PACKAGE_VERSION_SCHEMA,
                Optional("state"): Schema({Optional("resolved_dependencies"): [PACKAGE_VERSION_SCHEMA]}),
            }
        ),
        Optional("score"): Optional(float),
        Optional("justification"): [JUSTIFICATION_SCHEMA],
        Optional("not_acceptable"): All(str, Length(min=1)),
        Optional("eager_stop_pipeline"): All(str, Length(min=1)),
        Optional("multi_package_resolution"): bool,
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_STEP_SCHEMA = Schema(
    {
        Required("run"): PRESCRIPTION_STEP_RUN_SCHEMA,
        Optional("multi_package_resolution"): bool,
        Required("type"): "step",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Stride unit.
#

PRESCRIPTION_STRIDE_RUN_SCHEMA = Schema(
    {
        Optional("not_acceptable"): All(str, Length(min=1)),
        Optional("eager_stop_pipeline"): All(str, Length(min=1)),
        Optional("state"): Schema({Optional("resolved_dependencies"): [PACKAGE_VERSION_SCHEMA]}),
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_STRIDE_SCHEMA = Schema(
    {
        Required("run"): PRESCRIPTION_STRIDE_RUN_SCHEMA,
        Required("type"): "stride",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Wrap unit.
#

PRESCRIPTION_WRAP_RUN_SCHEMA = Schema(
    {
        Optional("not_acceptable"): All(str, Length(min=1)),
        Optional("eager_stop_pipeline"): All(str, Length(min=1)),
        Optional("justification"): [JUSTIFICATION_SCHEMA],
        Optional("state"): Schema({Optional("resolved_dependencies"): PACKAGE_VERSION_SCHEMA}),
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_WRAP_SCHEMA = Schema(
    {
        Required("run"): PRESCRIPTION_WRAP_RUN_SCHEMA,
        Required("type"): "wrap",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Prescription.
#

PRESCRIPTION_SPEC_UNITS_SCHEMA = Schema(
    {
        Required("boots"): [PRESCRIPTION_BOOT_SCHEMA],
        Required("sieves"): [PRESCRIPTION_SIEVE_SCHEMA],
        Required("steps"): [PRESCRIPTION_STEP_SCHEMA],
        Required("pseudonyms"): [PRESCRIPTION_PSEUDONYM_SCHEMA],
        Required("strides"): [PRESCRIPTION_STRIDE_SCHEMA],
        Required("wraps"): [PRESCRIPTION_WRAP_SCHEMA],
    }
)

PRESCRIPTION_SPEC_SCHEMA = Schema(
    {
        Required("units"): PRESCRIPTION_SPEC_UNITS_SCHEMA,
    }
)

PRESCRIPTION_SCHEMA = Schema(
    {
        Required("apiVersion"): "thoth-station.ninja/v1",
        Required("kind"): "prescription",
        Required("spec"): PRESCRIPTION_SPEC_SCHEMA,
    }
)
