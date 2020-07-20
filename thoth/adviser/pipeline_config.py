#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""A base class for implementing sieves."""

from itertools import chain
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Union

import attr

from .boot import Boot
from .dm_report import DependencyMonkeyReport
from .exceptions import PipelineUnitError
from .sieve import Sieve
from .step import Step
from .stride import Stride
from .wrap import Wrap

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .unit import Unit
    from .report import Report


@attr.s(slots=True)
class PipelineConfig:
    """A configuration of a pipeline for dependency-monkey and for adviser."""

    boots = attr.ib(type=List[Boot], default=attr.Factory(list))
    sieves = attr.ib(type=List[Sieve], default=attr.Factory(list))
    steps = attr.ib(type=List[Step], default=attr.Factory(list))
    strides = attr.ib(type=List[Stride], default=attr.Factory(list))
    wraps = attr.ib(type=List[Wrap], default=attr.Factory(list))

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return this pipeline configuration in a dict representation."""
        return {
            "boots": [boot.to_dict() for boot in self.boots],
            "sieves": [sieve.to_dict() for sieve in self.sieves],
            "steps": [step.to_dict() for step in self.steps],
            "strides": [stride.to_dict() for stride in self.strides],
            "wraps": [wrap.to_dict() for wrap in self.wraps],
        }

    def iter_units(self):
        # type:('PipelineConfig') -> Generator[Unit, None, None]
        """Iterate over units present in the configuration."""
        yield from chain(self.boots, self.sieves, self.steps, self.strides, self.wraps)

    def iter_units_reversed(self):
        # type:('PipelineConfig') -> Generator[Unit, None, None]
        """Iterate over units present in the configuration in a reversed order."""
        yield from reversed(self.wraps)
        yield from reversed(self.strides)
        yield from reversed(self.steps)
        yield from reversed(self.sieves)
        yield from reversed(self.boots)

    def call_pre_run(self) -> None:
        """Call pre-run method on all units registered in this configuration."""
        for unit in self.iter_units():
            try:
                unit.pre_run()
            except Exception as exc:
                raise PipelineUnitError(
                    "Failed to run pre_run method on unit %r: %s", unit.__class__.__name__, str(exc),
                ) from exc

    def call_post_run(self) -> None:
        """Call post-run method on all units registered in this configuration."""
        for unit in self.iter_units_reversed():
            try:
                unit.post_run()
            except Exception as exc:
                raise PipelineUnitError(
                    "Failed to run post_run method on unit %r: %s", unit.__class__.__name__, str(exc),
                ) from exc

    def call_post_run_report(self, report):
        # type:('PipelineConfig', Union[Report, DependencyMonkeyReport]) -> None
        """Call post-run method when report is generated."""
        for unit in self.iter_units_reversed():
            try:
                unit.post_run_report(report)
            except Exception as exc:
                raise PipelineUnitError(
                    "Failed to run pre_run_report method on unit %r: %s", unit.__class__.__name__, str(exc),
                ) from exc
