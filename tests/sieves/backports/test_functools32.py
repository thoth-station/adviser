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

"""Test removing backport functools32 from dependencies."""

from typing import Optional

import pytest

from thoth.adviser.sieves import Functools32BackportSieve
from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.exceptions import SkipPackage

from ...base import AdviserTestCase

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.python import PackageVersion
from thoth.python import Source


class TestFunctools32BackportSieve(AdviserTestCase):
    """Test sieve removing functools32 backport."""

    @pytest.mark.parametrize(
        "python_version,recommendation_type,decision_type,develop",
        [
            ("3.7", RecommendationType.LATEST, None, False),
            ("3.8", None, DecisionType.RANDOM, True),
            ("3.9", RecommendationType.STABLE, None, False),
            ("3.5", RecommendationType.TESTING, None, True),
            ("3.2", None, DecisionType.ALL, False),
        ],
    )
    def test_should_include(
        self,
        builder_context: PipelineBuilderContext,
        python_version: str,
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
        develop: bool,
    ) -> None:
        """Test registering this unit."""
        builder_context.project.runtime_environment.python_version = python_version
        builder_context.recommendation_type = recommendation_type
        builder_context.decision_type = decision_type

        assert builder_context.is_dependency_monkey_pipeline() or builder_context.is_adviser_pipeline()
        assert Functools32BackportSieve.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "python_version,recommendation_type,decision_type,develop",
        [
            ("2.7", RecommendationType.LATEST, None, False),
            (None, RecommendationType.LATEST, None, False),
            ("3.1", None, DecisionType.RANDOM, True),
            ("3.0", RecommendationType.STABLE, None, False),
            ("2.6", RecommendationType.TESTING, None, True),
            ("3.1", None, DecisionType.ALL, False),
        ],
    )
    def test_no_include(
        self,
        builder_context: PipelineBuilderContext,
        python_version: Optional[str],
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
        develop: bool,
    ) -> None:
        """Test not including this unit."""
        builder_context.project.runtime_environment.python_version = python_version
        builder_context.recommendation_type = recommendation_type
        builder_context.decision_type = decision_type

        assert builder_context.is_dependency_monkey_pipeline() or builder_context.is_adviser_pipeline()
        assert Functools32BackportSieve.should_include(builder_context) is None

    def test_remove(self, context: Context) -> None:
        """Test removing functools32 dependency."""
        package_version = PackageVersion(
            name="functools32", version="==3.2.3-2", develop=False, index=Source("https://pypi.org/simple"),
        )

        unit = Functools32BackportSieve()
        with Functools32BackportSieve.assigned_context(context):
            with pytest.raises(SkipPackage):
                list(unit.run(pv for pv in (package_version,)))

            # Run twice to ensure only one entry is added to stack info.
            with pytest.raises(SkipPackage):
                list(unit.run(pv for pv in (package_version,)))

        assert len(context.stack_info) == 1
