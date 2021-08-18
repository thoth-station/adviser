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

"""Handle caching of pipeline units."""

import functools
import logging
from typing import Any
from typing import Dict
from typing import Type
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
    from .unit import UnitPrescription  # noqa: F401
    from ...pipeline_builder import PipelineBuilderContext

    SHOULD_INCLUDE_FUNC_TYPE = Callable[[Type["UnitPrescription"], str, "PipelineBuilderContext", Dict[str, Any]], bool]

_LOGGER = logging.getLogger(__name__)


def should_include_cache(func: "SHOULD_INCLUDE_FUNC_TYPE") -> "SHOULD_INCLUDE_FUNC_TYPE":  # noqa: D202
    """Handle caching for parts of prescription units that do not change during pipeline construction."""

    @functools.wraps(func)
    def wrapped(
        cls: Type["UnitPrescription"],
        unit_name: str,
        pipeline_builder: "PipelineBuilderContext",
        should_include_dict: Dict[str, Any],
    ) -> bool:
        cached_result = cls.SHOULD_INCLUDE_CACHE.get(unit_name)
        if cached_result is not None:
            _LOGGER.debug(
                "%s: Using pre-cached result (%r) of should include prescription part", unit_name, cached_result
            )
            return cached_result

        result: bool = func(cls, unit_name, pipeline_builder, should_include_dict)
        cls.SHOULD_INCLUDE_CACHE[unit_name] = result
        return result

    return wrapped
