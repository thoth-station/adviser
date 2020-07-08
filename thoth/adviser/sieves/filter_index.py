#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""A sieve to filter out packages based on Python package index configured."""

import logging
from typing import Optional
from typing import Dict
from typing import Any
from typing import Generator
from typing import TYPE_CHECKING

import attr
from thoth.python import PackageVersion
from voluptuous import Required
from voluptuous import Schema

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class FilterIndexSieve(Sieve):
    """A sieve to filter out packages based on Python package index configured.

    The filtering is done based on configuration supplied - per package-version. The sieve is
    configured using the following pipeline configuration entry:
      {
        "package_name": "tensorflow",
        "index_url": [
          "https://pypi.org/simple",
          "https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple/"
        ]
      }
    """

    CONFIGURATION_DEFAULT = {"package_name": None, "index_url": None}
    CONFIGURATION_SCHEMA = Schema({Required("package_name"): str, Required("index_url"): [str],})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Register self, never."""
        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out packages based on Python package index configured for the given package."""
        for package_version in package_versions:
            if package_version.name != self.configuration["package_name"]:
                yield package_version

            if package_version.index.url not in self.configuration["index_url"]:
                _LOGGER.warning(
                    "Removing package %r in version %r as index used %r does not conform to any supplied %r",
                    package_version.name,
                    package_version.version,
                    package_version.index.url,
                    self.configuration["index_url"],
                )
                continue

            yield package_version
