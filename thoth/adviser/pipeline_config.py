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

"""A base class for implementing sieves."""

from itertools import chain
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Union

import attr

from .boot import Boot
from .dm_report import DependencyMonkeyReport
from .exceptions import PipelineUnitError
from .pseudonym import Pseudonym
from .sieve import Sieve
from .step import Step
from .stride import Stride
from .wrap import Wrap

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .unit import Unit
    from .report import Report
    from .unit_types import BootType
    from .unit_types import PseudonymType
    from .unit_types import SieveType
    from .unit_types import StepType
    from .unit_types import StrideType
    from .unit_types import WrapType


@attr.s(slots=True)
class PipelineConfig:
    """A configuration of a pipeline for dependency-monkey and for adviser."""

    _boots = attr.ib(type=Dict[Optional[str], List["BootType"]], factory=dict, kw_only=True)
    _pseudonyms = attr.ib(type=Dict[str, List["PseudonymType"]], factory=dict, kw_only=True)
    _sieves = attr.ib(type=Dict[Optional[str], List["SieveType"]], factory=dict, kw_only=True)
    _steps = attr.ib(type=Dict[Optional[str], List["StepType"]], factory=dict, kw_only=True)
    _strides = attr.ib(type=Dict[Optional[str], List["StrideType"]], factory=dict, kw_only=True)
    _wraps = attr.ib(type=Dict[Optional[str], List["WrapType"]], factory=dict, kw_only=True)

    @property
    def boots(self) -> List["BootType"]:
        """Get all boots."""
        return list(chain(*self._boots.values()))

    @property
    def boots_dict(self) -> Dict[Optional[str], List["BootType"]]:
        """Get boots as a dictionary mapping."""
        return self._boots

    @property
    def pseudonyms(self) -> List["PseudonymType"]:
        """Get all pseudonyms."""
        return list(chain(*self._pseudonyms.values()))

    @property
    def pseudonyms_dict(self) -> Dict[str, List["PseudonymType"]]:
        """Get pseudonyms as a dictionary mapping."""
        return self._pseudonyms

    @property
    def sieves(self) -> List["SieveType"]:
        """Get all sieves."""
        return list(chain(*self._sieves.values()))

    @property
    def sieves_dict(self) -> Dict[Optional[str], List["SieveType"]]:
        """Get sieves as a dictionary mapping."""
        return self._sieves

    @property
    def steps(self) -> List["StepType"]:
        """Get all steps."""
        return list(chain(*self._steps.values()))

    @property
    def steps_dict(self) -> Dict[Optional[str], List["StepType"]]:
        """Get steps as a dictionary mapping."""
        return self._steps

    @property
    def strides(self) -> List["StrideType"]:
        """Get all strides."""
        return list(chain(*self._strides.values()))

    @property
    def strides_dict(self) -> Dict[Optional[str], List["StrideType"]]:
        """Get strides as a dictionary mapping."""
        return self._strides

    @property
    def wraps(self) -> List["WrapType"]:
        """Get all wraps."""
        return list(chain(*self._wraps.values()))

    @property
    def wraps_dict(self) -> Dict[Optional[str], List["WrapType"]]:
        """Get wraps as a dictionary mapping."""
        return self._wraps

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return this pipeline configuration in a dict representation."""
        return {
            "boots": [boot.to_dict() for boot in self.boots],
            "pseudonyms": [pseudonym.to_dict() for pseudonym in self.pseudonyms],
            "sieves": [sieve.to_dict() for sieve in self.sieves],
            "steps": [step.to_dict() for step in self.steps],
            "strides": [stride.to_dict() for stride in self.strides],
            "wraps": [wrap.to_dict() for wrap in self.wraps],
        }

    def iter_units(self):
        # type:('PipelineConfig') -> Generator[Unit, None, None]
        """Iterate over units present in the configuration."""
        yield from chain(self.boots, self.pseudonyms, self.sieves, self.steps, self.strides, self.wraps)

    def iter_units_reversed(self):
        # type:('PipelineConfig') -> Generator[Unit, None, None]
        """Iterate over units present in the configuration in a reversed order."""
        yield from reversed(self.wraps)
        yield from reversed(self.strides)
        yield from reversed(self.steps)
        yield from reversed(self.sieves)
        yield from reversed(self.pseudonyms)
        yield from reversed(self.boots)

    def call_pre_run(self) -> None:
        """Call pre-run method on all units registered in this configuration."""
        for unit in self.iter_units():
            try:
                unit.pre_run()
            except Exception as exc:
                raise PipelineUnitError(f"Failed to run pre_run method on unit {unit.name!r}: {str(exc)}") from exc

    def call_post_run(self) -> None:
        """Call post-run method on all units registered in this configuration."""
        for unit in self.iter_units_reversed():
            try:
                unit.post_run()
            except Exception as exc:
                raise PipelineUnitError(f"Failed to run post_run method on unit {unit.name!r}: {str(exc)}") from exc

    def call_post_run_report(self, report):
        # type:('PipelineConfig', Union[Report, DependencyMonkeyReport]) -> None
        """Call post-run method when report is generated."""
        for unit in self.iter_units_reversed():
            try:
                unit.post_run_report(report)
            except Exception as exc:
                raise PipelineUnitError(
                    f"Failed to run pre_run_report method on unit {unit.name!r}: {str(exc)}"
                ) from exc
