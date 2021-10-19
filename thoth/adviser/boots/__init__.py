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

"""Boot units implemented in adviser."""

from .fully_specified_environment import FullySpecifiedEnvironment
from .gpu import GPUBoot
from .labels import LabelsBoot
from .pipfile_hash import PipfileHashBoot
from .platform import PlatformBoot
from .prescription_release import PrescriptionReleaseBoot
from .python_version import PythonVersionBoot
from .environment_info import EnvironmentInfoBoot
from .rhel_version import RHELVersionBoot
from .solved_software_environment import SolvedSoftwareEnvironmentBoot
from .solvers_configured import SolversConfiguredBoot
from .thoth_s2i import ThothS2IBoot
from .thoth_s2i_info import ThothS2IInfoBoot
from .ubi import UbiBoot

# from ._debug import MemTraceBoot


# Relative ordering of units is relevant, as the order specifies order
# in which the asked to be registered - any dependencies between them
# can be mentioned here.
__all__ = [
    # "MemTraceBoot",
    "LabelsBoot",
    "PipfileHashBoot",  # Should be placed before any changes to the input.
    "GPUBoot",  # Should be placed before any GPU specific pipeline unit.
    "ThothS2IBoot",
    "ThothS2IInfoBoot",
    "UbiBoot",
    "PythonVersionBoot",
    "EnvironmentInfoBoot",
    "SolvedSoftwareEnvironmentBoot",
    "SolversConfiguredBoot",  # Should be placed after SolvedSoftwareEnvironmentBoot.
    "RHELVersionBoot",
    "PlatformBoot",
    "PrescriptionReleaseBoot",
    "FullySpecifiedEnvironment",
    "SolvedSoftwareEnvironmentBoot",
]
