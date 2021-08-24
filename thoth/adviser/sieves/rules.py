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

"""A sieve for filtering out Python packages that have rules assigned."""

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
from voluptuous import Any as SchemaAny
from voluptuous import Required
from voluptuous import Schema

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class SolverRulesSieve(Sieve):
    """A sieve for filtering out Python packages that have rules assigned."""

    CONFIGURATION_DEFAULT = {"package_name": None}
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): SchemaAny(str, None)})
    _JUSTIFICATION_LINK = jl("rules")

    _messages_logged = attr.ib(type=Set[Tuple[str, str, str]], factory=set, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Include pipeline sieve."""
        if not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._messages_logged.clear()
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out packages that have rules assigned."""
        for package_version in package_versions:
            package_tuple = package_version.to_tuple()

            solver_rules = (
                # Rules specific to index.
                self.context.graph.get_python_package_version_solver_rules_all(
                    package_version.name,
                    package_version.locked_version,
                    package_version.index.url,
                )
                +
                # Rules agnostic to index.
                self.context.graph.get_python_package_version_solver_rules_all(
                    package_version.name,
                    package_version.locked_version,
                )
            )

            if solver_rules:
                if package_tuple not in self._messages_logged:
                    for solver_rule in solver_rules:
                        self._messages_logged.add(package_tuple)
                        message = f"Removing package {package_tuple} based on solver rule configured: {solver_rule}"
                        _LOGGER.debug("%s - see %s", message, self._JUSTIFICATION_LINK)
                        self.context.stack_info.append(
                            {
                                "type": "WARNING",
                                "message": message,
                                "link": self._JUSTIFICATION_LINK,
                            }
                        )

                continue

            yield package_version
