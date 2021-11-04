#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019-2021 Kevin Postlehtwait, Fridolin Pokorny
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

"""Filter out stacks which have require non-existent ABI symbols in Thoth's s2i base image."""

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

from ..sieve import Sieve

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class ThothS2IAbiCompatibilitySieve(Sieve):
    """Remove packages if the Thoth's s2i image being used doesn't have necessary ABI."""

    _THOTH_S2I_PREFIX = "quay.io/thoth-station/"
    CONFIGURATION_DEFAULT = {"package_name": None}
    image_symbols = attr.ib(type=Set[str], factory=set, init=False)
    _messages_logged = attr.ib(type=Set[Tuple[str, str, str]], factory=set, init=False)

    _LINK = jl("abi_missing")
    _LINK_NO_ABI = jl("no_abi")
    _LINK_BAD_IMAGE = jl("bad_base_image")

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register if the base image provided is Thoth's s2i."""
        base_image = builder_context.project.runtime_environment.base_image
        if not builder_context.is_included(cls) and base_image and base_image.startswith(cls._THOTH_S2I_PREFIX):
            yield {}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Initialize image_symbols."""
        base_image = self.context.project.runtime_environment.base_image
        parsed_base_image = self.get_base_image(base_image, raise_on_error=False)
        if parsed_base_image is None:
            error_msg = (
                f"Cannot determine Thoth s2i version information from {base_image}, "
                "recommendations specific for ABI used will not be taken into account"
            )
            _LOGGER.warning("%s - see %s", error_msg, self._LINK_BAD_IMAGE)
            self.context.stack_info.append(
                {
                    "type": "WARNING",
                    "message": error_msg,
                    "link": self._LINK_BAD_IMAGE,
                }
            )
            self.image_symbols = set()
            super().pre_run()
            return

        thoth_s2i_image_name, thoth_s2i_image_version = parsed_base_image
        self.image_symbols = set(
            self.context.graph.get_thoth_s2i_analyzed_image_symbols_all(
                thoth_s2i_image_name=thoth_s2i_image_name,
                thoth_s2i_image_version=thoth_s2i_image_version,
                is_external=False,
            )
        )
        if not self.image_symbols:
            message = f"No ABI symbols found for {thoth_s2i_image_name!r} in version {thoth_s2i_image_version!r}"
            _LOGGER.warning("%s - see %s", message, self._LINK_NO_ABI)
            self.context.stack_info.append({"type": "WARNING", "message": message, "link": self._LINK_NO_ABI})

        self._messages_logged.clear()
        _LOGGER.debug("Analyzed image has the following symbols: %r", self.image_symbols)
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """If package requires non-present symbols remove it."""
        if not self.image_symbols:
            # No image symbols or the version was not provided, the warning is produced in pre_run method.
            yield from package_versions
            return None

        for pkg_vers in package_versions:
            package_symbols = set(
                self.context.graph.get_python_package_required_symbols(
                    package_name=pkg_vers.name,
                    package_version=pkg_vers.locked_version,
                    index_url=pkg_vers.index.url,
                )
            )

            # Shortcut if package requires no symbols
            if not package_symbols:
                yield pkg_vers
                continue

            missing_symbols = package_symbols - self.image_symbols
            if not missing_symbols:
                yield pkg_vers
            else:
                # Log removed package
                package_tuple = pkg_vers.to_tuple()
                if package_tuple not in self._messages_logged:
                    message = f"Package {package_tuple} was removed due to missing ABI symbols in the environment"
                    _LOGGER.warning("%s - see %s", message, self._LINK)
                    self._messages_logged.add(package_tuple)
                    _LOGGER.debug("The following symbols are not present: %r", missing_symbols)

                continue
