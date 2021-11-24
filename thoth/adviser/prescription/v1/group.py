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

"""A base class for implementing group steps."""

import attr
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
import logging

from voluptuous import All
from voluptuous import Length
from voluptuous import Required
from voluptuous import Schema

from packaging.specifiers import SpecifierSet
from .schema import PACKAGE_VERSION_REQUIRED_NAME_SCHEMA
from .schema import PRESCRIPTION_GROUP_STEP_RUN_SCHEMA
from .step import StepPrescription

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class GroupStepPrescription(StepPrescription):
    """A base class for implementing group steps.

    The declarative interface triggers registration of multiple pipeline units for all the package versions
    stated. All the pipeline units have shared context to exchange shared information (ex. if stack_info was
    already added and so). This is an optimization to make sure the pipeline unit is run only if needed (based
    on package_name).
    """

    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): str,
            Required("match"): {
                Required("package_version"): PACKAGE_VERSION_REQUIRED_NAME_SCHEMA,
                Required("state"): Schema(
                    {Required("resolved_dependencies"): All([PACKAGE_VERSION_REQUIRED_NAME_SCHEMA], Length(min=1))}
                ),
            },
            Required("multi_package_resolution"): True,  # Required to match multiple packages.
            Required("run"): PRESCRIPTION_GROUP_STEP_RUN_SCHEMA,
            Required("prescription"): Schema({"run": bool}),
        }
    )

    _specifier = attr.ib(type=Optional[SpecifierSet], kw_only=True, init=False, default=None)
    _index_url = attr.ib(type=Optional[str], kw_only=True, init=False, default=None)
    _develop = attr.ib(type=Optional[bool], kw_only=True, init=False, default=None)

    @staticmethod
    def _yield_should_include(unit_prescription: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Yield for every entry stated in the match field."""
        match = unit_prescription["match"]
        run = unit_prescription["run"]
        prescription_conf = {"run": False}

        # The trick here is to construct resolved dependencies for all the combinations that can happen. If the
        # group step states two package versions named - "foo", "bar", there are created two units:
        #   - the first one matches "foo" and resolved dependencies state "bar"
        #   - the second one matches "bar" and resolved dependencies state "foo"
        # Similarly, if there are multiple packages stated.
        for match_entry in match if isinstance(match, list) else [match]:
            for idx, item in enumerate(match_entry["group"]):
                resolved_dependencies = []
                for other_idx, other_item in enumerate(match_entry["group"]):
                    if idx != other_idx:
                        resolved_dependencies.append(other_item["package_version"])

                package_version_dict = item["package_version"]
                yield {
                    "package_name": package_version_dict["name"],
                    "multi_package_resolution": True,
                    "match": {
                        "package_version": package_version_dict,
                        "state": {
                            "resolved_dependencies": resolved_dependencies,
                        },
                    },
                    "run": run,
                    "prescription": prescription_conf,
                }
