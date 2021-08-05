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

"""A sieve that makes sure packages shipped inside an s2i container are reused.

An example can be a Jupyter Notebook image that has TensorFlow pre-installed. As
this image is supposed to be "supported", TensorFlow that is present should be
reused, rather than re-installed to another version.
"""

import logging
from typing import Any
from typing import Dict
from typing import Generator
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
class ThothS2IPackagesSieve(Sieve):
    """Remove packages that are already present in s2i image."""

    CONFIGURATION_DEFAULT = {"package_name": None}
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): str, Required("package_version"): str})

    _JUSTIFICATION = jl("s2i_packages")
    _THOTH_S2I_IMAGE_PREFIX = "quay.io/thoth-station/"
    _THOTH_S2I_PACKAGES_LOCATION_PREFIX = "/opt/app-root/"

    _message_logged = attr.ib(type=bool, init=False)

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Register if the base image provided is Thoth's s2i."""
        if builder_context.is_included(cls):
            yield from ()
            return None

        base_image = builder_context.project.runtime_environment.base_image
        if not base_image or not base_image.startswith(cls._THOTH_S2I_IMAGE_PREFIX):
            yield from ()
            return None

        base_image_parts = cls.get_base_image(base_image)
        if not base_image_parts:
            _LOGGER.debug(
                "Failed to parse base image parts from %r, any possible Python packages available in "
                "the image will not be considered",
                base_image,
            )
            yield from ()
            return None

        analysis_document_id = builder_context.graph.get_last_analysis_document_id(
            base_image_parts[0],
            base_image_parts[1],
            is_external=False,
        )

        python_packages = builder_context.graph.get_python_package_version_all(analysis_document_id)
        if not python_packages:
            _LOGGER.debug(
                "No Python packages found in %r, not considering any possible Python packages available in %r",
                analysis_document_id,
                base_image,
            )
            yield from ()
            return None

        for python_package in python_packages:
            if not python_package["location"].startswith(cls._THOTH_S2I_PACKAGES_LOCATION_PREFIX):
                continue

            _LOGGER.debug(
                "Taking into account package %r in version %r located in %r in the container image",
                python_package["package_name"],
                python_package["package_version"],
                python_package["location"],
            )
            yield {"package_name": python_package["package_name"], "package_version": python_package["package_version"]}

        return None

    def pre_run(self) -> None:
        """Initialize before running the pipeline unit."""
        self._message_logged = False
        super().pre_run()

    def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
        """If a package does not meet version already present in the base image, remove it."""
        for package_version in package_versions:
            if package_version.locked_version == self.configuration["package_version"]:
                yield package_version
                continue

            if not self._message_logged:
                self._message_logged = True

                message = (
                    f"Removing any possible versions of {self.configuration['package_name']} as "
                    f"the given package is already present in the base image "
                    f"in version {self.configuration['package_version']}"
                )
                _LOGGER.warning("%s - see %s", message, self._JUSTIFICATION)
                self.context.stack_info.append({"type": "WARNING", "message": message, "link": self._JUSTIFICATION})
