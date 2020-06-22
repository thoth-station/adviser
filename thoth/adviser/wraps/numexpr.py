#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""A wrap that suggests to use NumExpr for NumPy array optimizations."""

from typing import TYPE_CHECKING

from ..state import State
from ..wrap import Wrap

if TYPE_CHECKING:
    from ..pipeline_builder import PipelineBuilderContext


class NumExprWrap(Wrap):
    """A wrap that suggests using NumExpr library if NumPy is used."""

    _JUSTIFICATION = [
        {
            "type": "INFO",
            "message": "Consider using NumExpr library to speed up numerical NumPy array operations.",
        }
    ]

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext"):
        """Include this wrap in adviser if numpy is used but no numexpr usage is detected."""
        if (
            not builder_context.is_included(cls)
            and builder_context.is_adviser_pipeline()
            and "numpy" in builder_context.project.pipfile.packages.packages
            and "numexpr" not in builder_context.project.pipfile.packages.packages
        ):
            return {}

        return None

    def run(self, state: State) -> None:
        """Suggest using NumExpr if NumPy is used."""
        state.add_justification(self._JUSTIFICATION)
