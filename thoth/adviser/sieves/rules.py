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

    _rules_logged = attr.ib(type=Set[int], factory=set, init=False)
    _messages_logged = attr.ib(type=Set[Tuple[int, str, str, str]], factory=set, init=False)

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
        self._rules_logged.clear()
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

            if not solver_rules:
                yield package_version
                continue

            for solver_rule in solver_rules:
                rule_id, version_range, index_url, description = solver_rule

                message_logged_entry: Tuple[int, str, str, str] = (
                    rule_id,
                    package_tuple[0],
                    package_tuple[1],
                    package_tuple[2],
                )
                if message_logged_entry not in self._messages_logged:
                    self._messages_logged.add(message_logged_entry)
                    _LOGGER.warning(
                        "Removing package %r based on solver rule configured: %s",
                        package_tuple,
                        description,
                    )

                if rule_id in self._rules_logged:
                    continue

                self._rules_logged.add(rule_id)

                message = f"Removing package {package_tuple[0]!r}"
                message += f" in versions {version_range!r}" if version_range else " in all versions"
                message += f" from index {index_url!r}" if index_url else " from all registered indexes"
                message += f" based on rule: {description}"
                self.context.stack_info.append(
                    {
                        "type": "WARNING",
                        "message": message,
                        "link": self._JUSTIFICATION_LINK,
                    }
                )
