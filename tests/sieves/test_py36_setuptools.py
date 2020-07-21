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

"""Test sieve to filter out old setuptools that do not work with Python 3.6."""

import flexmock
import pytest

from thoth.adviser.enums import DecisionType
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import Py36SetuptoolsSieve
from thoth.python import PackageVersion
from thoth.python import Source

from ..base import AdviserTestCase


class TestPy36SetuptoolsSieve(AdviserTestCase):
    """Test sieve to filter out old setuptools that do not work with Python 3.6."""

    @pytest.mark.parametrize(
        "recommendation_type,decision_type",
        [
            (RecommendationType.STABLE, None),
            (RecommendationType.TESTING, None),
            (None, DecisionType.RANDOM),
            (None, DecisionType.ALL),
        ],
    )
    def test_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        decision_type: DecisionType,
    ) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = decision_type
        builder_context.recommendation_type = recommendation_type
        builder_context.project.runtime_environment.python_version = "3.6"

        assert builder_context.is_adviser_pipeline() or builder_context.is_dependency_monkey_pipeline()
        assert Py36SetuptoolsSieve.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "recommendation_type,decision_type,python_version",
        [
            (RecommendationType.STABLE, None, "3.8"),
            (RecommendationType.TESTING, None, "3.9"),
            (None, DecisionType.RANDOM, "3.5"),
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
        assert Py36SetuptoolsSieve.should_include(builder_context) is None

    def test_filter(self) -> None:
        """Test filtering out setuptools that do not work with Python 3.6."""
        package_version = PackageVersion(
            name="setuptools", version="==14.2", develop=False, index=Source("https://pypi.org/simple"),
        )

        context = flexmock()
        with Py36SetuptoolsSieve.assigned_context(context):
            unit = Py36SetuptoolsSieve()
            assert list(unit.run(p for p in [package_version])) == []

    def test_no_filter(self) -> None:
        """Test not filtering packages that can be included."""
        pkg1 = PackageVersion(
            name="setuptools", version="==17.0", develop=False, index=Source("https://pypi.org/simple"),
        )
        pkg2 = PackageVersion(
            name="setuptools", version="==49.1.0", develop=False, index=Source("https://pypi.org/simple"),
        )
        pkg3 = PackageVersion(
            name="tensorflow", version="==2.2.0", develop=False, index=Source("https://thoth-station.ninja/simple"),
        )

        pkgs = [pkg1, pkg2, pkg3]

        context = flexmock()
        with Py36SetuptoolsSieve.assigned_context(context):
            unit = Py36SetuptoolsSieve()
            assert list(unit.run(p for p in pkgs)) == pkgs
