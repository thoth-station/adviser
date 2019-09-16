#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

"""Implementation of steps used in stack generators pipeline."""


from .buildtime_error import BuildtimeErrorFiltering
from .cve import CvePenalization
from .limit_latest_versions import LimitLatestVersions
from .observation_reduction import ObservationReduction
from .prereleases import CutPreReleases
from .restrict_indexes import RestrictIndexes
from .runtime_error import RuntimeErrorFiltering
from .score_cutoff import ScoreCutoff
from .semver_sort import SemverSort
from .toolchain import CutToolchain
from .unreachable import CutUnreachable
from .unsolved import CutUnsolved
