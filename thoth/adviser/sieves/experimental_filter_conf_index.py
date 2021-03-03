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

"""A sieve to filter out packages coming from other indexes than the ones configured."""

import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion
from voluptuous import Schema
from voluptuous import Required

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class FilterConfiguredIndexSieve(Sieve):
    """A sieve to filter out packages coming from other indexes than the ones configured."""

    CONFIGURATION_DEFAULT = {"package_name": None, "allowed_indexes": None}
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): None, Required("allowed_indexes"): {str}})
    _JUSTIFICATION_LINK = jl("index_conf")

    packages_seen = attr.ib(type=Set[Tuple[str, str, str]], default=attr.Factory(set), init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Enable this pipeline unit if the adjustment is enabled."""
        if not builder_context.is_included(cls) and builder_context.project.pipfile.thoth.disable_index_adjustment:
            allowed_indexes = set()
            for source in builder_context.project.pipfile.meta.sources.values():
                allowed_indexes.add(source.url)

            yield {
                "package_name": None,
                "allowed_indexes": allowed_indexes,
            }
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize this unit before each run."""
        self.packages_seen.clear()
        super().pre_run()

    def to_dict(self) -> Dict[str, Any]:
        """Turn this pipeline step into its dictionary representation, override to have unit JSON serializable."""
        configuration = {}

        for key, value in self.configuration.items():
            configuration[key] = value if not isinstance(value, set) else sorted(value)

        return {"name": self.__class__.__name__, "configuration": configuration, "unit_run": self.unit_run}

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Cut-off packages that are not coming from an allowed index."""
        for package_version in package_versions:
            if package_version.index.url not in self.configuration["allowed_indexes"]:
                package_tuple = package_version.to_tuple()

                if package_tuple not in self.packages_seen:
                    self.packages_seen.add(package_tuple)
                    msg = f"Removing package {package_tuple} as it does not use enabled index"
                    _LOGGER.warning("%s - see %s", msg, self._JUSTIFICATION_LINK)
                    self.context.stack_info.append(
                        {
                            "type": "WARNING",
                            "message": msg,
                            "link": self._JUSTIFICATION_LINK,
                        }
                    )

                continue

            yield package_version
