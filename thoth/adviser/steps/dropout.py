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

"""Perform a drop out of a new state expansion, randomly."""

import random

from typing import Any
from typing import Generator
from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict
from typing import TYPE_CHECKING
import logging

import attr
from thoth.python import PackageVersion
from voluptuous import Required
from voluptuous import Schema

from ..exceptions import NotAcceptable
from ..state import State
from ..step import Step


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class DropoutStep(Step):
    """A step that drops a state transition with a certain probability."""

    CONFIGURATION_DEFAULT = {"package_name": None, "probability": 0.9, "multi_package_resolution": False}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): None,
            Required("cve_penalization"): float,
            Required("multi_package_resolution"): False,
        }
    )

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Do not register the dropout step."""
        yield from ()
        return None

    def run(
        self, state: State, package_version: PackageVersion
    ) -> Optional[Tuple[Optional[float], Optional[List[Dict[str, str]]]]]:
        """Do not accept new state, randomly."""
        if random.random() >= self.configuration["probability"]:
            raise NotAcceptable

        return None
