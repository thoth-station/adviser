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

"""A sieve for filtering out build time/installation errors of Python packages."""

import logging
import operator
from collections import defaultdict
from functools import partial
from typing import Any
from typing import Dict
from typing import DefaultDict
from typing import List
from typing import Generator
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion
from thoth.storages.exceptions import NotFoundError
from voluptuous import Any as SchemaAny
from voluptuous import Required
from voluptuous import Schema

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


def _default_dict_factory() -> DefaultDict[str, DefaultDict[str, List[str]]]:
    """Instantiate default dictionary mapping package name -> index URL -> list of versions."""
    return defaultdict(partial(defaultdict, list))  # type: ignore


@attr.s(slots=True)
class SolvedSieve(Sieve):
    """Filter out build time/installation errors of Python packages."""

    CONFIGURATION_DEFAULT = {"package_name": None, "without_error": True}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {Required("package_name"): SchemaAny(str, None), Required("without_error"): bool}
    )
    _JUSTIFICATION_LINK = jl("install_error")

    _messages_logged = attr.ib(type=Set[Tuple[str, str, str]], factory=set, init=False)
    _packages_filtered = attr.ib(
        factory=_default_dict_factory,
        init=False,
    )

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Include solved pipeline sieve for adviser or Dependency Monkey on pipeline creation."""
        if not builder_context.is_included(cls):
            yield {}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._messages_logged.clear()
        self._packages_filtered.clear()
        super().pre_run()

    def post_run(self) -> None:
        """Post-run method for wrapping up the work."""
        for package_name, package_items in sorted(self._packages_filtered.items(), key=operator.itemgetter(0)):
            for index_url, version in sorted(package_items.items(), key=operator.itemgetter(0)):
                self.context.stack_info.append(
                    {
                        "type": "WARNING",
                        "message": f"The following versions of {package_name!r} from {index_url!r} were "
                        "removed due to installation issues in the target environment: " + ", ".join(version),
                        "link": self._JUSTIFICATION_LINK,
                    }
                )

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out packages based on build time/installation issues.."""
        for package_version in package_versions:
            package_tuple = package_version.to_tuple()

            try:
                has_error = self.context.graph.has_python_solver_error(
                    package_version.name,
                    package_version.locked_version,
                    package_version.index.url,
                    os_name=self.context.project.runtime_environment.operating_system.name,
                    os_version=self.context.project.runtime_environment.operating_system.version,
                    python_version=self.context.project.runtime_environment.python_version,
                )
            except NotFoundError as exc:
                _LOGGER.debug(
                    "Removing package %r as it was not solved: %s",
                    package_tuple,
                    exc,
                )
                continue

            if has_error and self.configuration["without_error"]:
                if package_tuple not in self._messages_logged:
                    self._messages_logged.add(package_tuple)
                    message = (
                        f"Removing package {package_tuple} due to installation time error in the software environment"
                    )
                    _LOGGER.warning("%s - see %s", message, self._JUSTIFICATION_LINK)
                    self._packages_filtered[package_tuple[0]][package_tuple[2]].append(package_tuple[1])
                continue

            yield package_version
