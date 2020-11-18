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

"""Test sieve to filter out Pandas>=1.2 on Python 3.6."""

import flexmock
import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import PandasPy36Sieve
from thoth.adviser.context import Context
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestPandasPy36Sieve(AdviserUnitTestCase):
    """Test sieve to filter out Pandas>=1.2 on Python 3.6."""

    UNIT_TESTED = PandasPy36Sieve

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        builder_context.project.runtime_environment.python_version = "3.6"
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize(
        "recommendation_type",
        [
            RecommendationType.STABLE,
            RecommendationType.PERFORMANCE,
            RecommendationType.SECURITY,
        ],
    )
    def test_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
    ) -> None:
        """Test including this pipeline unit."""
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.python_version = "3.6"

        assert builder_context.is_adviser_pipeline()
        assert PandasPy36Sieve.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,python_version",
        [
            (RecommendationType.TESTING, None, "3.6"),
            (RecommendationType.LATEST, None, "3.6"),
            (None, DecisionType.RANDOM, "3.6"),
            (RecommendationType.STABLE, None, "3.9"),
            (RecommendationType.PERFORMANCE, None, "3.8"),
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
        python_version: str,
    ) -> None:
        """Test not including this pipeline unit step."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.python_version = python_version
        assert PandasPy36Sieve.should_include(builder_context) is None

    @pytest.mark.parametrize("pandas_version", ["1.2.0", "2.0.0"])
    def test_run(self, context: Context, pandas_version: str) -> None:
        """Test filtering out Pandas that dropped Python 3.6 support."""
        package_version = PackageVersion(
            name="pandas",
            version=f"=={pandas_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        unit = PandasPy36Sieve()
        unit.pre_run()
        with PandasPy36Sieve.assigned_context(context):
            assert unit._message_logged is False
            assert list(unit.run(p for p in [package_version])) == []
            assert unit._message_logged is True

    def test_no_filter(self) -> None:
        """Test not filtering packages that can be included."""
        pkg1 = PackageVersion(
            name="pandas",
            version="==1.1.2",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )
        pkg2 = PackageVersion(
            name="pandas",
            version="==1.0.0",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )
        pkg3 = PackageVersion(
            name="pandas",
            version="==0.24.2",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        pkgs = [pkg1, pkg2, pkg3]

        context = flexmock()
        unit = PandasPy36Sieve()
        unit.pre_run()
        with PandasPy36Sieve.assigned_context(context):
            assert unit._message_logged is False
            assert list(unit.run(p for p in pkgs)) == pkgs
            assert unit._message_logged is False
