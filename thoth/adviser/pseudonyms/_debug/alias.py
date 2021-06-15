#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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

"""A pseudonym that introduces package aliases based on the supplied configuration."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from voluptuous import Any as SchemaAny
from voluptuous import Required
from voluptuous import Schema

from ...pseudonym import Pseudonym

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class AliasPseudonym(Pseudonym):
    """A pseudonym that introduces package aliases based on the supplied configuration."""

    CONFIGURATION_DEFAULT = {"package_name": None, "package_version": None, "index_url": None}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {
            Required("package_name"): str,
            Required("package_version"): SchemaAny(str, None),
            Required("index_url"): SchemaAny(str, None),
            Required("aliases"): Schema(
                [Schema({Required("package_name"): str, Required("package_version"): str, Required("index_url"): str})]
            ),
        }
    )

    @classmethod
    def should_include(cls, _: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register self, never."""
        yield from ()
        return None

    def run(self, package_version: PackageVersion) -> Generator[Tuple[str, str, str], None, None]:
        """Create alternatives to packages based on the configuration supplied."""
        if (
            self.configuration["package_version"] is not None
            and self.configuration["package_version"] != package_version.locked_version
        ):
            yield from ()
            return

        if self.configuration["index_url"] is not None and self.configuration["index_url"] != package_version.index.url:
            yield from ()
            return

        yield from ((i["package_name"], i["package_version"], i["index_url"]) for i in self.configuration["aliases"])
