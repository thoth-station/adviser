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

"""Implementation an adviser report capturing pipeline results and adviser parameters."""

import typing

import attr

from thoth.common import RuntimeEnvironment

from .pipeline.product import PipelineProduct


@attr.s(slots=True)
class AdviserReport:
    """Report for an adviser pipeline run."""

    products = attr.ib(type=typing.List[PipelineProduct])
    pipeline_configuration = attr.ib(type=dict)
    library_usage = attr.ib(type=dict)
    stack_info = attr.ib(type=typing.List[dict])
    advised_configuration = attr.ib(type=RuntimeEnvironment)

    was_oom_killed = attr.ib(type=bool)
    was_cpu_time_exhausted_killed = attr.ib(type=bool)

    @property
    def was_premature_killed(self) -> bool:
        """Check if pipeline was prematurely killed."""
        return self.was_oom_killed or self.was_cpu_time_exhausted_killed

    def to_dict(self):
        """Create a dict out of this report."""
        return attr.asdict(self)
