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

"""A sieve to filter out packages based on index configuration."""

import logging
from typing import Dict
from typing import Any
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from voluptuous import Schema
from voluptuous import Required

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PackageIndexConfigurationSieve(Sieve):
    """A sieve to filter out packages based on index configuration."""

    CONFIGURATION_DEFAULT = {"package_name": None, "index_url": None}
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): str, Required("index_url"): str})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register for each package."""
        if not builder_context.is_included(cls) and builder_context.project.pipfile.thoth.disable_index_adjustment:
            for package_version in builder_context.project.iter_dependencies(with_devel=True):
                if package_version.index:
                    yield {
                        "package_name": package_version.name,
                        "index_url": package_version.index.url,
                    }

            return None

        yield from ()
        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Cut-off pre-releases if project does not explicitly allows them."""
        for package_version in package_versions:
            if package_version.index.url != self.configuration["index_url"]:
                _LOGGER.warning(
                    "Skipping package %r as it does not used configured index %r",
                    package_version.to_tuple(),
                    self.configuration["index_url"],
                )
                continue

            yield package_version
