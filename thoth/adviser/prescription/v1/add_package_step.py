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

"""A prescription step implementing adding a package to a dependency graph."""

import logging

import attr
from thoth.adviser.state import State
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages.exceptions import NotFoundError
from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required

from .step import StepPrescription
from .schema import PRESCRIPTION_ADD_PACKAGE_STEP_RUN_SCHEMA
from .schema import PRESCRIPTION_ADD_PACKAGE_STEP_MATCH_ENTRY_SCHEMA

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class AddPackageStepPrescription(StepPrescription):
    """Add package prescription step unit implementation."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): SchemaAny(str, None),
            Required("match"): PRESCRIPTION_ADD_PACKAGE_STEP_MATCH_ENTRY_SCHEMA,
            Required("multi_package_resolution"): bool,
            Required("run"): SchemaAny(PRESCRIPTION_ADD_PACKAGE_STEP_RUN_SCHEMA, None),
            Required("prescription"): Schema({"run": bool}),
        }
    )

    def run(self, state: State, package_version: PackageVersion) -> None:
        """Run main entry-point for steps to skip packages."""
        if not self._index_url_check(self._index_url, package_version.index.url):
            return None

        if self._specifier and package_version.locked_version not in self._specifier:
            return None

        if self._develop is not None and package_version.develop != self._develop:
            return None

        if not self._run_state_with_initiator(state, package_version):
            return None

        add_package_version = self.run_prescription["package_version"]
        add_package_version_name = add_package_version["name"]
        add_package_version_version = add_package_version["locked_version"][2:]
        add_package_version_index_url = add_package_version["index_url"]
        add_package_version_develop = add_package_version["develop"]

        add_package_version_tuple = (
            add_package_version_name,
            add_package_version_version,
            add_package_version_index_url,
        )

        resolved = state.resolved_dependencies.get(add_package_version_name)
        if resolved:
            if resolved == add_package_version_tuple:
                _LOGGER.debug(
                    "%s: Not adding package %r as it is already in the resolved listing",
                    self.get_unit_name(),
                    add_package_version_tuple,
                )
            else:
                _LOGGER.debug(
                    "%s: Not adding package %r as another package %r is already present in the resolved listing",
                    self.get_unit_name(),
                    add_package_version_tuple,
                    resolved,
                )

            return None

        runtime_env = self.context.project.runtime_environment
        py_ver = runtime_env.python_version.replace(".", "")
        # XXX: this could be moved to thoth-common
        solver_name = f"solver-{runtime_env.operating_system.name}-{runtime_env.operating_system.version}-py{py_ver}"
        if not self.context.graph.python_package_version_exists(
            add_package_version_name,
            add_package_version_version,
            add_package_version_index_url,
            solver_name=solver_name,
        ):
            _LOGGER.debug(
                "%s: Not adding package %r as the given package was not solved by %r",
                self.get_unit_name(),
                add_package_version_tuple,
                solver_name,
            )
            return None

        try:
            if not self.context.graph.is_python_package_index_enabled(add_package_version_index_url):
                _LOGGER.debug(
                    "%s: Not adding package %r as index %r is not enabled",
                    self.get_unit_name(),
                    add_package_version_tuple,
                    add_package_version_index_url,
                )
                return None
        except NotFoundError:
            _LOGGER.debug(
                "%s: Not adding package %r as index %r is not known to the resolver",
                self.get_unit_name(),
                add_package_version_tuple,
                add_package_version_index_url,
            )
            return None

        try:
            self._run_base()
        finally:
            self._configuration["prescription"]["run"] = True

        pv = PackageVersion(
            name=add_package_version_name,
            version=add_package_version["locked_version"],
            index=Source(add_package_version_index_url),
            develop=add_package_version_develop,
        )
        self.context.register_package_version(pv)
        state.add_unresolved_dependency(add_package_version_tuple)
