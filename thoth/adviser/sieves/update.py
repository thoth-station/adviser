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

"""A sieve for filtering out Python packages that are not part of a new release.

This pipeline unit is registered only if adviser was requested to run to check a new
package release. The pipeline unit filters out all the packages except for the one that
should be included in the stack (the newly released) to check whether there is a stack
with the released package that is better than the one used with an older release.
"""

import os
import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

import attr
import json
from thoth.common import get_justification_link as jl
from thoth.adviser.enums import RecommendationType
from thoth.python import PackageVersion
from voluptuous import Required
from voluptuous import Schema

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PackageUpdateSieve(Sieve):
    """A sieve for filtering out Python packages that are not part of a new release."""

    CONFIGURATION_DEFAULT = {"package_name": None, "package_version": None, "index_url": None}
    CONFIGURATION_SCHEMA: Schema = Schema(
        {Required("package_name"): str, Required("package_version"): str, Required("index_url"): str}
    )
    _JUSTIFICATION_LINK = jl("update")
    _PACKAGE_UPDATE = os.getenv("THOTH_ADVISER_DEPLOYMENT_PACKAGE_UPDATE")

    _messages_logged = attr.ib(type=Set[Tuple[str, str, str]], factory=set, init=False)
    _package_update = attr.ib(type=Optional[Tuple[str, str, str]], init=False, default=None)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Include pipeline sieve."""
        if cls._PACKAGE_UPDATE and not builder_context.is_included(cls):
            package_update_dict = json.loads(cls._PACKAGE_UPDATE)

            if builder_context.recommendation_type != RecommendationType.LATEST:
                _LOGGER.warning(
                    "Registering %s sieve pipeline unit when not recommending latest, this error is not critical ...",
                    cls.__name__,
                )

            yield package_update_dict
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._messages_logged.clear()
        self._package_update = (
            self.configuration["package_name"],
            self.configuration["package_version"],
            self.configuration["index_url"],
        )
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Filter out packages that are old releases."""
        for package_version in package_versions:
            package_tuple = package_version.to_tuple()

            if package_tuple != self._package_update:
                if package_tuple not in self._messages_logged:
                    self._messages_logged.add(package_tuple)
                    message = f"Removing package {package_tuple} as advising on a new release"
                    _LOGGER.warning("%s - see %s", message, self._JUSTIFICATION_LINK)
                    self.context.stack_info.append(
                        {
                            "type": "WARNING",
                            "message": message,
                            "link": self._JUSTIFICATION_LINK,
                            "package_name": package_version.name,
                        }
                    )

                continue

            yield package_version
