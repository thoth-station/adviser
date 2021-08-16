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

"""A step prescription class implementing skipping a package in a dependency graph."""

import attr
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING
import logging

from voluptuous import Any as SchemaAny
from voluptuous import Schema
from voluptuous import Required
from thoth.python import PackageVersion

from thoth.adviser.state import State
from thoth.adviser.exceptions import SkipPackage
from .step import StepPrescription
from .schema import PRESCRIPTION_SKIP_PACKAGE_STEP_RUN_SCHEMA
from .schema import PRESCRIPTION_SKIP_PACKAGE_STEP_MATCH_ENTRY_SCHEMA

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SkipPackageStepPrescription(StepPrescription):
    """A step prescription class implementing skipping a package in a dependency graph."""

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): str,
            Required("multi_package_resolution"): bool,
            Required("run"): SchemaAny(PRESCRIPTION_SKIP_PACKAGE_STEP_RUN_SCHEMA, None),
            Required("match"): PRESCRIPTION_SKIP_PACKAGE_STEP_MATCH_ENTRY_SCHEMA,
        }
    )

    _logged = attr.ib(type=bool, default=False, init=False, kw_only=True)

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Run main entry-point for steps to skip a package."""
        if not self._index_url_check(self._index_url, package_version.index.url):
            return None

        if self._specifier and package_version.locked_version not in self._specifier:
            return None

        if self._develop is not None and package_version.develop != self._develop:
            return None

        # XXX: we might want to do more sophisticated logic here - it would be great to check
        # if the package removed was introduced only by an expected package and such

        if not self._run_state(state):
            return None

        self._run_base()

        raise SkipPackage(f"Package {package_version.to_tuple()} skipped based on prescription {self.get_unit_name()}")
