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


_NONEMPTY_STRING = All(str, Length(min=1))
_NONEMPTY_LIST_OF_NONEMPTY_STRINGS = All([_NONEMPTY_STRING], Length(min=1))
_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE = All([_NONEMPTY_STRING, None], Length(min=1))
_NONEMPTY_LIST_OF_INTEGERS_WITH_NONE = All([int, None], Length(min=1))


def _with_not(entity: object) -> Schema:
    """Add possibility to provide 'not' in the given configuration entity."""
    return Schema(Any(entity, Schema({"not": entity})))


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
                        Optional("gpu_models"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
                    }
                )
            ],
            Length(min=1),
        ),
        Optional("python_versions"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("cuda_versions"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("platforms"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("openblas_versions"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("openmpi_versions"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("cudnn_versions"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("mkl_versions"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
        Optional("base_images"): _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),
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


JUSTIFICATION_SCHEMA = STACK_INFO_SCHEMA


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
        Required("name"): Optional(_NONEMPTY_STRING),
        Optional("locked_version"): Optional(_locked_version),
        Optional("index_url"): Optional(_NONEMPTY_STRING),
    }
)


def _specifier_set(v: object) -> None:
    """Validate a specifier set."""
    if not isinstance(v, str):
        raise Invalid(f"Value {v!r} is not valid version specifier (example: '<1.0>=0.5')")
    try:
        SpecifierSet(v)
    except InvalidSpecifier as exc:
        raise Invalid(str(exc))


PACKAGE_VERSION_SCHEMA = Schema(
    {
        Optional("name"): Optional(_NONEMPTY_STRING),
        Optional("version"): _specifier_set,
        Optional("index_url"): Optional(_NONEMPTY_STRING),
    }
)


PACKAGE_VERSION_REQUIRED_NAME_SCHEMA = Schema(
    {
        Required("name"): _NONEMPTY_STRING,
        Optional("version"): _specifier_set,
        Optional("index_url"): Optional(_NONEMPTY_STRING),
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
        Optional("state"): Schema({Optional("resolved_dependencies"): [PACKAGE_VERSION_SCHEMA]}),
    }
)

PRESCRIPTION_STEP_RUN_SCHEMA = Schema(
    {
        Optional("score"): Optional(float),
        Optional("justification"): [JUSTIFICATION_SCHEMA],
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
    {Required("state"): Schema({Required("resolved_dependencies"): [PACKAGE_VERSION_SCHEMA]})}
)

PRESCRIPTION_WRAP_RUN_SCHEMA = Schema(
    {
        Optional("not_acceptable"): _NONEMPTY_STRING,
        Optional("eager_stop_pipeline"): _NONEMPTY_STRING,
        Optional("justification"): [JUSTIFICATION_SCHEMA],
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

PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_RUN_ENTRY_SCHEMA = Schema(
    {
        Required("package_version"): PACKAGE_VERSION_REQUIRED_NAME_SCHEMA,
        Required("organization"): _NONEMPTY_STRING,
        Optional("tag_version_prefix"): _NONEMPTY_STRING,
        Required("repository"): _NONEMPTY_STRING,
    }
)

PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_RUN_ENTRIES_SCHEMA = All(
    [PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_RUN_ENTRY_SCHEMA], Length(min=1)
)

PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_SCHEMA = Schema(
    {
        Required("type"): "wrap.GitHubReleaseNotes",
        Required("run"): Schema({"release_notes": PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_RUN_ENTRIES_SCHEMA}),
        **_UNIT_SCHEMA_BASE_DICT,
    }
)

#
# Prescription.
#

PRESCRIPTION_SPEC_UNITS_SCHEMA = Schema(
    {
        Optional("boots"): [PRESCRIPTION_BOOT_SCHEMA],
        Optional("sieves"): [Any(PRESCRIPTION_SIEVE_SCHEMA, PRESCRIPTION_SKIP_PACKAGE_SIEVE_SCHEMA)],
        Optional("steps"): [PRESCRIPTION_STEP_SCHEMA],
        Optional("pseudonyms"): [PRESCRIPTION_PSEUDONYM_SCHEMA],
        Optional("strides"): [PRESCRIPTION_STRIDE_SCHEMA],
        Optional("wraps"): [Any(PRESCRIPTION_GITHUB_RELEASE_NOTES_WRAP_SCHEMA, PRESCRIPTION_WRAP_SCHEMA)],
    }
)

PRESCRIPTION_SPEC_SCHEMA = Schema(
    {
        Required("release"): _NONEMPTY_STRING,
        Required("name"): _NONEMPTY_STRING,
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
