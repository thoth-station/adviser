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

from thoth.python import PackageVersion
from packaging.specifiers import SpecifierSet
from packaging.specifiers import InvalidSpecifier

from thoth.adviser.cpu_db import CPUDatabase
from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType


_NONEMPTY_STRING = All(str, Length(min=1))
_NONEMPTY_LIST_OF_NONEMPTY_STRINGS = All([_NONEMPTY_STRING], Length(min=1))
_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE = All([_NONEMPTY_STRING, None], Length(min=1))
_NONEMPTY_LIST_OF_INTEGERS_WITH_NONE = All([int, None], Length(min=1))


def _with_not(entity: object) -> Schema:
    """Add possibility to provide 'not' in the given configuration entity."""
    return Schema(Any(entity, Schema({"not": entity})))


def _specifier_set(v: object) -> None:
    """Validate a specifier set."""
    if not isinstance(v, str):
        raise Invalid(f"Value {v!r} is not valid version specifier (example: '<1.0,>=0.5')")
    try:
        SpecifierSet(v)
    except InvalidSpecifier as exc:
        raise Invalid(str(exc))


def _python_package_name(n: object) -> None:
    """Validate Python package name."""
    if not isinstance(n, str):
        raise Invalid(f"Value {n!r} is not a valid package name")

    try:
        normalized = PackageVersion.normalize_python_package_name(n)
    except Exception as exc:
        raise Invalid(f"Failed to parse Python package name {n!r}: {str(exc)}")
    else:
        if normalized != n:
            raise Invalid(f"Python package name {n!r} is not in a normalized form, normalized: {normalized!r}")


_RPM_PACKAGE_VERSION_SCHEMA = Schema(
    {
        Required("package_name"): _NONEMPTY_STRING,
        Optional("arch"): _NONEMPTY_STRING,
        Optional("epoch"): _NONEMPTY_STRING,
        Optional("package_identifier"): _NONEMPTY_STRING,
        Optional("package_version"): _NONEMPTY_STRING,
        Optional("release"): _NONEMPTY_STRING,
        Optional("src"): bool,
    }
)

_PYTHON_PACKAGE_VERSION_SCHEMA = Schema(
    {
        Required("name"): _python_package_name,
        Optional("version"): _specifier_set,
        Optional("location"): Any(_NONEMPTY_STRING, None),
    }
)

PRESCRIPTION_UNIT_SHOULD_INCLUDE_RUNTIME_ENVIRONMENTS_SCHEMA = Schema(
    {
        Optional("operating_systems"): [
            Schema(
                {
                    Optional("name"): _NONEMPTY_STRING,
                    Optional("version"): _NONEMPTY_STRING,
                }
            )
        ],
        Optional("hardware"): All(
            [
                Schema(
                    {
                        Optional("cpu_families"): _with_not(_NONEMPTY_LIST_OF_INTEGERS_WITH_NONE),
                        Optional("cpu_models"): _with_not(_NONEMPTY_LIST_OF_INTEGERS_WITH_NONE),
                        Optional("cpu_flags"): _with_not(All(CPUDatabase.get_known_flags(), Length(min=1))),
                        Optional("gpu_models"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
                    }
                )
            ],
            Length(min=1),
        ),
        Optional("python_version"): Any(_specifier_set, None),
        Optional("cuda_version"): Any(_specifier_set, None),
        Optional("platforms"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("openblas_version"): Any(_specifier_set, None),
        Optional("openmpi_version"): Any(_specifier_set, None),
        Optional("cudnn_version"): Any(_specifier_set, None),
        Optional("mkl_version"): Any(_specifier_set, None),
        Optional("base_images"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("abi"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS),
        Optional("rpm_packages"): _with_not(All([_RPM_PACKAGE_VERSION_SCHEMA], Length(min=1))),
        Optional("python_packages"): _with_not(All([_PYTHON_PACKAGE_VERSION_SCHEMA], Length(min=1))),
    }
)


def _library_usage(v: object) -> None:
    if not isinstance(v, dict):
        raise Invalid(f"Expected a dictionary describing library usage, got: {v}")

    if not v:
        raise Invalid(f"Got empty library usage: {v}")

    for k, v in v.items():
        if not isinstance(k, str):
            raise Invalid(f"Unknown key representing package name in library usage: {k}")

        if not k:
            raise Invalid("Empty key representing package name in library usage")

        # A list of library calls.
        _NONEMPTY_LIST_OF_NONEMPTY_STRINGS(v)


def _labels(v: object) -> None:
    if not isinstance(v, dict):
        raise Invalid(f"Expected a dictionary describing labels, got {v}")

    for val in v.values():
        if not isinstance(val, str):
            raise Invalid(f"Expected a non-empty string for label value, got {type(val)} instead: {val!r}")

        _NONEMPTY_STRING(val)


PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA = Schema(
    {
        Optional("times", default=1): All(int, Range(min=0, max=1)),
        Optional("adviser_pipeline"): bool,
        Optional("dependency_monkey_pipeline"): bool,
        Optional("labels"): _labels,
        Optional("dependencies"): Schema(
            {
                Optional("boots"): _NONEMPTY_LIST_OF_NONEMPTY_STRINGS,
                Optional("pseudonyms"): _NONEMPTY_LIST_OF_NONEMPTY_STRINGS,
                Optional("sieves"): _NONEMPTY_LIST_OF_NONEMPTY_STRINGS,
                Optional("steps"): _NONEMPTY_LIST_OF_NONEMPTY_STRINGS,
                Optional("strides"): _NONEMPTY_LIST_OF_NONEMPTY_STRINGS,
                Optional("wraps"): _NONEMPTY_LIST_OF_NONEMPTY_STRINGS,
            }
        ),
        Optional("recommendation_types"): _with_not(
            All(list(map(str.lower, RecommendationType.__members__.keys())), Length(min=1))
        ),
        Optional("decision_types"): _with_not(
            All(list(map(str.lower, DecisionType.__members__.keys())), Length(min=1))
        ),
        Optional("runtime_environments"): PRESCRIPTION_UNIT_SHOULD_INCLUDE_RUNTIME_ENVIRONMENTS_SCHEMA,
        Optional("library_usage"): _library_usage,
        Optional("authenticated"): bool,
    }
)

_UNIT_SCHEMA_BASE_DICT = {
    Required("name"): _NONEMPTY_STRING,
    Required("should_include"): PRESCRIPTION_UNIT_SHOULD_INCLUDE_SCHEMA,
}


def _justification_link(v: str) -> None:
    """Validate justification link."""
    if v.startswith(("https://", "http://")):
        try:
            urlparse(v)
        except Exception as exc:
            raise Invalid(f"Failed to validate URL: {str(exc)}")
    else:
        matched = re.fullmatch(r"[a-z0-9_-]+", v)
        if not matched:
            raise Invalid(f"Failed to validate base justification link {v!r}")

    return None


STACK_INFO_SCHEMA = Schema(
    {
        Required("type"): Any("WARNING", "INFO", "ERROR"),
        Required("message"): _NONEMPTY_STRING,
        Required("link"): _justification_link,
    }
)


JUSTIFICATION_SCHEMA = Schema(
    {
        Required("type"): Any("WARNING", "INFO", "ERROR"),
        Required("message"): _NONEMPTY_STRING,
        Required("link"): _justification_link,
        Optional("package_name"): _python_package_name,
        Optional("advisory"): _NONEMPTY_STRING,
        Optional("cve_id"): _NONEMPTY_STRING,
        Optional("cve_name"): _NONEMPTY_STRING,
        Optional("version_range"): _specifier_set,
    }
)


_UNIT_RUN_SCHEMA_BASE_DICT = {
    Optional("stack_info"): [STACK_INFO_SCHEMA],
    Optional("log"): Schema(
        {
            Required("message"): _NONEMPTY_STRING,
            Required("type"): Any("WARNING", "INFO", "ERROR"),
        }
    ),
}


def _locked_version(v: object) -> None:
    """Validate locked version."""
    if v is not None and (not isinstance(v, str) or not v.startswith("==") and not v.startswith("===")):
        raise Invalid(f"Value {v!r} is not valid locked version (example: '==1.0.0')")


PACKAGE_VERSION_LOCKED_SCHEMA = Schema(
    {
        Required("name"): Optional(_python_package_name),
        Optional("locked_version"): Optional(_locked_version),
        Optional("index_url"): Optional(_NONEMPTY_STRING),
    }
)


PACKAGE_VERSION_SCHEMA = Schema(
    {
        Optional("name"): Optional(_python_package_name),
        Optional("version"): _specifier_set,
        Optional("index_url"): Optional(Any(_NONEMPTY_STRING, {"not": _NONEMPTY_STRING})),
        Optional("develop"): bool,
    }
)


PACKAGE_VERSION_REQUIRED_NAME_SCHEMA = Schema(
    {
        Required("name"): _python_package_name,
        Optional("version"): _specifier_set,
        Optional("index_url"): Optional(Any(_NONEMPTY_STRING, {"not": _NONEMPTY_STRING})),
        Optional("develop"): bool,
    }
)

#
# Boot unit.
#

PRESCRIPTION_BOOT_MATCH_ENTRY_SCHEMA = Schema({"package_name": Optional(_NONEMPTY_STRING)})

PRESCRIPTION_BOOT_RUN_SCHEMA = Schema(
    {
        Optional("not_acceptable"): _NONEMPTY_STRING,
        Optional("eager_stop_pipeline"): _NONEMPTY_STRING,
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_BOOT_SCHEMA = Schema(
    {
        Optional("match"): Any(
            All([PRESCRIPTION_BOOT_MATCH_ENTRY_SCHEMA], Length(min=1)), PRESCRIPTION_BOOT_MATCH_ENTRY_SCHEMA
        ),
        Required("run"): PRESCRIPTION_BOOT_RUN_SCHEMA,
        Required("type"): "boot",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Pseudonym unit.
#

PRESCRIPTION_PSEUDONYM_MATCH_ENTRY_SCHEMA = Schema({"package_version": PACKAGE_VERSION_REQUIRED_NAME_SCHEMA})

PRESCRIPTION_PSEUDONYM_RUN_SCHEMA = Schema(
    {
        Required("yield"): Schema(
            {
                Optional("yield_matched_version"): bool,
                "package_version": PACKAGE_VERSION_LOCKED_SCHEMA,
            }
        ),
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_PSEUDONYM_SCHEMA = Schema(
    {
        Required("match"): Any(
            All([PRESCRIPTION_PSEUDONYM_MATCH_ENTRY_SCHEMA], Length(min=1)),
            PRESCRIPTION_PSEUDONYM_MATCH_ENTRY_SCHEMA,
        ),
        Required("run"): PRESCRIPTION_PSEUDONYM_RUN_SCHEMA,
        Required("type"): "pseudonym",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Sieve unit.
#

PRESCRIPTION_SIEVE_MATCH_ENTRY_SCHEMA = Schema({"package_version": PACKAGE_VERSION_SCHEMA})

PRESCRIPTION_SIEVE_RUN_SCHEMA = Schema(
    {
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)


PRESCRIPTION_SIEVE_SCHEMA = Schema(
    {
        Required("match"): Any(
            All([PRESCRIPTION_SIEVE_MATCH_ENTRY_SCHEMA], Length(min=1)), PRESCRIPTION_SIEVE_MATCH_ENTRY_SCHEMA
        ),
        Optional("run"): PRESCRIPTION_SIEVE_RUN_SCHEMA,
        Required("type"): "sieve",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Skip package sieve.
#

PRESCRIPTION_SKIP_PACKAGE_SIEVE_RUN_ENTRY_SCHEMA = Schema(
    {
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_SKIP_PACKAGE_SIEVE_MATCH_ENTRY_SCHEMA = Schema(
    {
        Required("package_name"): Optional(_NONEMPTY_STRING),
    }
)

PRESCRIPTION_SKIP_PACKAGE_SIEVE_SCHEMA = Schema(
    {
        Required("match"): Any(
            All([PRESCRIPTION_SKIP_PACKAGE_SIEVE_MATCH_ENTRY_SCHEMA], Length(min=1)),
            PRESCRIPTION_SKIP_PACKAGE_SIEVE_MATCH_ENTRY_SCHEMA,
        ),
        Required("type"): "sieve.SkipPackage",
        Optional("run"): PRESCRIPTION_SKIP_PACKAGE_SIEVE_RUN_ENTRY_SCHEMA,
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Step unit.
#

PRESCRIPTION_STEP_MATCH_ENTRY_SCHEMA = Schema(
    {
        Required("package_version"): PACKAGE_VERSION_SCHEMA,
        Optional("state"): Schema(
            {
                Optional("resolved_dependencies"): All([PACKAGE_VERSION_REQUIRED_NAME_SCHEMA], Length(min=1)),
                Optional("package_version_from"): All([PACKAGE_VERSION_REQUIRED_NAME_SCHEMA], Length(min=1)),
                Optional("package_version_from_allow_other"): bool,
            }
        ),
    }
)

PRESCRIPTION_STEP_RUN_SCHEMA = Schema(
    {
        Optional("score"): Optional(float),
        Optional("justification"): All([JUSTIFICATION_SCHEMA], Length(min=1)),
        Optional("not_acceptable"): _NONEMPTY_STRING,
        Optional("eager_stop_pipeline"): _NONEMPTY_STRING,
        Optional("multi_package_resolution"): bool,
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_STEP_SCHEMA = Schema(
    {
        Required("match"): Any(
            All([PRESCRIPTION_STEP_MATCH_ENTRY_SCHEMA], Length(min=1)), PRESCRIPTION_STEP_MATCH_ENTRY_SCHEMA
        ),
        Required("run"): PRESCRIPTION_STEP_RUN_SCHEMA,
        Required("type"): "step",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)


#
# Skip package step unit.
#

PRESCRIPTION_SKIP_PACKAGE_STEP_MATCH_ENTRY_SCHEMA = PRESCRIPTION_STEP_MATCH_ENTRY_SCHEMA


PRESCRIPTION_SKIP_PACKAGE_STEP_RUN_SCHEMA = Schema(
    {
        Optional("multi_package_resolution"): bool,
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)


PRESCRIPTION_SKIP_PACKAGE_STEP_SCHEMA = Schema(
    {
        Required("match"): Any(
            PRESCRIPTION_SKIP_PACKAGE_STEP_MATCH_ENTRY_SCHEMA,
        ),
        Optional("run"): PRESCRIPTION_SKIP_PACKAGE_STEP_RUN_SCHEMA,
        Required("type"): "step.SkipPackage",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)


#
# Add package step unit.
#

PRESCRIPTION_ADD_PACKAGE_STEP_MATCH_ENTRY_SCHEMA = PRESCRIPTION_STEP_MATCH_ENTRY_SCHEMA


PRESCRIPTION_ADD_PACKAGE_STEP_RUN_SCHEMA = Schema(
    {
        Optional("multi_package_resolution"): bool,
        Required("package_version"): Schema(
            {
                Required("name"): _python_package_name,
                Required("locked_version"): _locked_version,
                Required("index_url"): _NONEMPTY_STRING,
                Required("develop"): bool,
            }
        ),
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)


PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA = Schema(
    {
        Required("match"): Any(
            All([PRESCRIPTION_ADD_PACKAGE_STEP_MATCH_ENTRY_SCHEMA], Length(min=1)),
            PRESCRIPTION_ADD_PACKAGE_STEP_MATCH_ENTRY_SCHEMA,
        ),
        Required("run"): PRESCRIPTION_ADD_PACKAGE_STEP_RUN_SCHEMA,
        Required("type"): "step.AddPackage",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)


#
# Stride unit.
#

PRESCRIPTION_STRIDE_MATCH_ENTRY_SCHEMA = Schema(
    {Required("state"): Schema({Required("resolved_dependencies"): [PACKAGE_VERSION_SCHEMA]})}
)

PRESCRIPTION_STRIDE_RUN_SCHEMA = Schema(
    {
        Optional("not_acceptable"): _NONEMPTY_STRING,
        Optional("eager_stop_pipeline"): _NONEMPTY_STRING,
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_STRIDE_SCHEMA = Schema(
    {
        Required("match"): Any(
            All([PRESCRIPTION_STRIDE_MATCH_ENTRY_SCHEMA], Length(min=1)), PRESCRIPTION_STRIDE_MATCH_ENTRY_SCHEMA
        ),
        Required("run"): PRESCRIPTION_STRIDE_RUN_SCHEMA,
        Required("type"): "stride",
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Wrap unit.
#

PRESCRIPTION_WRAP_MATCH_ENTRY_SCHEMA = Schema(
    {Optional("state"): Schema({Required("resolved_dependencies"): [PACKAGE_VERSION_SCHEMA]})}
)

PRESCRIPTION_WRAP_RUN_SCHEMA = Schema(
    {
        Optional("justification"): All([JUSTIFICATION_SCHEMA], Length(min=1)),
        Optional("advised_manifest_changes"): object,
        **_UNIT_RUN_SCHEMA_BASE_DICT,
    }
)

PRESCRIPTION_WRAP_SCHEMA = Schema(
    {
        Required("run"): PRESCRIPTION_WRAP_RUN_SCHEMA,
        Required("type"): "wrap",
        Optional("match"): Any(
            All([PRESCRIPTION_WRAP_MATCH_ENTRY_SCHEMA], Length(min=1)), PRESCRIPTION_WRAP_MATCH_ENTRY_SCHEMA
        ),
        **_UNIT_SCHEMA_BASE_DICT,
    }
)


#
# GitHub release notes wrap unit.
#

PRESCRIPTION_GH_RELEASE_NOTES_WRAP_MATCH_ENTRY_SCHEMA = Schema(
    {
        Required("state"): Schema(
            {
                Required("resolved_dependencies"): Any(
                    All([PACKAGE_VERSION_REQUIRED_NAME_SCHEMA], Length(min=1, max=1)),
                    PACKAGE_VERSION_REQUIRED_NAME_SCHEMA,
                )
            }
        )
    }
)

PRESCRIPTION_GH_RELEASE_NOTES_WRAP_RUN_ENTRY_SCHEMA = Schema(
    {
        Required("organization"): _NONEMPTY_STRING,
        Optional("tag_version_prefix"): _NONEMPTY_STRING,
        Required("repository"): _NONEMPTY_STRING,
    }
)


PRESCRIPTION_GH_RELEASE_NOTES_WRAP_RUN_ENTRIES_SCHEMA = Schema(
    {"release_notes": PRESCRIPTION_GH_RELEASE_NOTES_WRAP_RUN_ENTRY_SCHEMA}
)


PRESCRIPTION_GH_RELEASE_NOTES_WRAP_SCHEMA = Schema(
    {
        Required("type"): "wrap.GHReleaseNotes",
        Required("match"): Any(
            All([PRESCRIPTION_GH_RELEASE_NOTES_WRAP_MATCH_ENTRY_SCHEMA], Length(min=1)),
            PRESCRIPTION_GH_RELEASE_NOTES_WRAP_MATCH_ENTRY_SCHEMA,
        ),
        Required("run"): PRESCRIPTION_GH_RELEASE_NOTES_WRAP_RUN_ENTRIES_SCHEMA,
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Prescription.
#

PRESCRIPTION_UNITS_SCHEMA = Schema(
    {
        Optional("boots"): [PRESCRIPTION_BOOT_SCHEMA],
        Optional("sieves"): [Any(PRESCRIPTION_SIEVE_SCHEMA, PRESCRIPTION_SKIP_PACKAGE_SIEVE_SCHEMA)],
        Optional("steps"): [
            Any(PRESCRIPTION_STEP_SCHEMA, PRESCRIPTION_SKIP_PACKAGE_STEP_SCHEMA, PRESCRIPTION_ADD_PACKAGE_STEP_SCHEMA)
        ],
        Optional("pseudonyms"): [PRESCRIPTION_PSEUDONYM_SCHEMA],
        Optional("strides"): [PRESCRIPTION_STRIDE_SCHEMA],
        Optional("wraps"): [
            Any(
                PRESCRIPTION_WRAP_SCHEMA,
                PRESCRIPTION_GH_RELEASE_NOTES_WRAP_SCHEMA,
            )
        ],
    }
)

PRESCRIPTION_SCHEMA = Schema(
    {
        Required("units"): PRESCRIPTION_UNITS_SCHEMA,
    }
)
