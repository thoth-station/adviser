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

"""A sieve unit representatives used for testing.."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import TYPE_CHECKING
from thoth.python import PackageVersion

from thoth.adviser.sieve import Sieve
from voluptuous import Optional as SchemaOptional
from voluptuous import Required
from voluptuous import Schema

if TYPE_CHECKING:
    from thoth.adviser.pipeline_builder import PipelineBuilderContext


class Sieve1(Sieve):
    """A testing sieve implementation."""

    CONFIGURATION_DEFAULT = {"flying_circus": 1969, "package_name": "tensorflow"}
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): str, Required("flying_circus"): str})

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if this pipeline unit should be included in the pipeline configuration."""
        yield from ()
        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Run noop method."""
        return package_versions


class Sieve2(Sieve):
    """A testing sieve implementation."""

    CONFIGURATION_DEFAULT = {"date": "2015-09-15", "package_name": "selinon"}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {Required("package_name"): str, Required("date"): str, SchemaOptional("foo"): str}
    )

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if this pipeline unit should be included in the pipeline configuration."""
        yield from ()
        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Run noop method."""
        return package_versions


__all__ = ["Sieve1", "Sieve2"]
