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

"""A prescription step implementing skipping a package in a dependency graph."""

import logging

import attr
from thoth.python import PackageVersion
from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required

from .step import StepPrescription
from .schema import PRESCRIPTION_SKIP_PACKAGE_STEP_RUN_SCHEMA
from .schema import PRESCRIPTION_SKIP_PACKAGE_STEP_MATCH_ENTRY_SCHEMA

from ...exceptions import SkipPackage
from ...state import State

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SkipPackageStepPrescription(StepPrescription):
    """Skip package prescription step unit implementation."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): SchemaAny(str, None),
            Required("match"): PRESCRIPTION_SKIP_PACKAGE_STEP_MATCH_ENTRY_SCHEMA,
            Required("multi_package_resolution"): bool,
            Required("run"): SchemaAny(PRESCRIPTION_SKIP_PACKAGE_STEP_RUN_SCHEMA, None),
            Required("prescription"): Schema({"run": bool}),
        }
    )

    def run(self, state: State, package_version: PackageVersion) -> None:
        """Run main entry-point for steps to skip packages."""
        _, locked_version, index_url = package_version.to_strict_tuple_locked()
        if not self._index_url_check(self._index_url, index_url):
            return None

        if self._specifier and locked_version not in self._specifier:
            return None

        if self._develop is not None and package_version.develop != self._develop:
            return None

        if not self._run_state_with_initiator(state, package_version):
            return None

        try:
            self._run_base()
        finally:
            self._configuration["prescription"]["run"] = True

        raise SkipPackage
