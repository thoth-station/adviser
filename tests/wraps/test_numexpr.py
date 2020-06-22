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

"""Test a wrap that suggests to use NumExpr for NumPy array optimizations."""

from thoth.adviser.state import State
from thoth.adviser.wraps import NumExprWrap
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.python import PackageVersion
from thoth.adviser.enums import RecommendationType

from ..base import AdviserTestCase


class TestNumExprWrap(AdviserTestCase):
    """Test the wrap suggesting NumExpr if NumPy is used."""

    def test_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test inclusion of this pipeline unit if NumPy is used."""
        builder_context.decision_type = None
        builder_context.recommendation_type = RecommendationType.LATEST
        assert builder_context.is_adviser_pipeline()

        builder_context.project.pipfile.packages.packages["numpy"] = PackageVersion(
            name="numpy",
            version='==1.19.0',
            develop=False
        )
        builder_context.project.pipfile.packages.packages.pop("numexpr", None)

        assert NumExprWrap.should_include(builder_context) == {}

    def test_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test no inclusion of this pipeline unit if NumPy is not used."""
        builder_context.decision_type = None
        builder_context.recommendation_type = RecommendationType.LATEST
        assert builder_context.is_adviser_pipeline()

        builder_context.project.pipfile.packages.packages.pop("numpy", None)
        assert NumExprWrap.should_include(builder_context) is None

    def test_no_include_numexpr(self, builder_context: PipelineBuilderContext) -> None:
        """Test no inclusion of this pipeline unit if NumExpr is already used."""
        builder_context.decision_type = None
        builder_context.recommendation_type = RecommendationType.STABLE
        assert builder_context.is_adviser_pipeline()

        builder_context.project.pipfile.packages["numpy"] = PackageVersion(
            name="numpy",
            version='==1.19.0',
            develop=False
        )
        builder_context.project.pipfile.packages["numexpr"] = PackageVersion(
            name="numexpr",
            version='==2.7.1',
            develop=False
        )
        assert NumExprWrap.should_include(builder_context) is None

    def test_run(self) -> None:
        """Test suggesting."""
        state = State()
        assert not state.justification

        unit = NumExprWrap()
        assert unit.run(state) is None

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message"}
        assert state.justification[0]["type"] == "INFO"
