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

"""Penalize stacks with a CVE."""

import logging

from ..stride import Stride
from ..stride_context import StrideContext
from ..units import get_cve_records

_LOGGER = logging.getLogger(__name__)


class CveScoring(Stride):
    """Penalization based on CVE being present in stack."""

    PARAMETERS_DEFAULT = {"cve_penalization": -0.2}

    def run(self, stride_context: StrideContext) -> None:
        """Score stacks with a CVE in a negative way."""
        for package_tuple in stride_context.stack_candidate:
            cve_records = get_cve_records(self.graph, package_tuple)
            for cve_record in cve_records:
                _LOGGER.debug("Found a CVE for %r", package_tuple)
                cve_record.update(
                    {
                        "type": "WARNING",
                        "justification": f"Found a CVE for package {package_tuple[0]} in version {package_tuple[1]}",
                    }
                )
                stride_context.adjust_score(
                    self.parameters["cve_penalization"], justification=[cve_record]
                )
