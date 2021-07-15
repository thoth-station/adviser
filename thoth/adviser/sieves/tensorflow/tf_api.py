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

"""Recommend a specific TensorFlow based on API usage."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Set
from typing import TYPE_CHECKING
import attr
import orjson
import logging
import os

from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion
from voluptuous import Any as SchemaAny
from voluptuous import Required
from voluptuous import Schema

from ...enums import RecommendationType
from ...sieve import Sieve


if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class TensorFlowAPISieve(Sieve):
    """A sieve that makes sure the right TensorFlow release is used based on user's API usage."""

    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): SchemaAny(str)})
    CONFIGURATION_DEFAULT = {"package_name": "tensorflow"}
    _LINK_API = jl("tf_api")
    _LINK_NO_API = jl("tf_no_api")

    _messages_logged = attr.ib(type=Set[str], factory=set, init=False)
    _no_api_logged = attr.ib(type=bool, default=False, init=False)
    _acceptable_releases = attr.ib(type=Optional[Set[str]], default=None, init=False)

    def pre_run(self) -> None:
        """Initialize this pipeline unit before each run."""
        self._messages_logged.clear()
        self._acceptable_releases = None
        self._no_api_logged = False
        super().pre_run()

    def _pre_compute_releases(self) -> None:
        """Pre-compute releases that match library usage supplied by the user."""
        with open(os.path.join(self._DATA_DIR, "tensorflow", "api.json"), "r") as api_file:
            known_api = orjson.loads(api_file.read())

        self._acceptable_releases = set()
        tf_api_used = set(
            i for i in ((self.context.library_usage.get("report") or {}).get("tensorflow") or [])  # type: ignore
        )
        for tf_version, tf_api in known_api.items():
            if tf_api_used.issubset(tf_api):
                self._acceptable_releases.add(tf_version)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register this pipeline unit for adviser library usage is provided."""
        if (
            builder_context.is_adviser_pipeline()
            and not builder_context.is_included(cls)
            and builder_context.library_usage
            and builder_context.recommendation_type not in (RecommendationType.LATEST, RecommendationType.TESTING)
            and "tensorflow" in (builder_context.library_usage.get("report") or {})
        ):
            yield {"package_name": "tensorflow"}
            yield {"package_name": "tensorflow-gpu"}
            yield {"package_name": "intel-tensorflow"}
            yield {"package_name": "tensorflow-cpu"}
            return None

        yield from ()
        return None

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """Use specific TensorFlow release based on library usage as supplied by the user."""
        if self._acceptable_releases is None:
            self._pre_compute_releases()

        if not self._acceptable_releases:
            if not self._no_api_logged:
                self._no_api_logged = True
                msg = "No TensorFlow symbols API found in the database that would match TensorFlow symbols used"
                _LOGGER.warning("%s - see %s", msg, self._LINK_NO_API)
                self.context.stack_info.append(
                    {
                        "type": "WARNING",
                        "message": msg,
                        "link": self._LINK_NO_API,
                    }
                )

            yield from package_versions
            return

        for package_version in package_versions:
            version = ".".join(map(str, package_version.semantic_version.release[:2]))
            if version in self._acceptable_releases:
                yield package_version
            elif version not in self._messages_logged:
                self._messages_logged.add(version)
                msg = (
                    f"Removing TensorFlow {package_version.to_tuple()!r} as it does not provide required symbols "
                    f"in the exposed API"
                )
                _LOGGER.warning("%s - see %s", msg, self._LINK_API)
                self.context.stack_info.append({"type": "WARNING", "message": msg, "link": self._LINK_API})
