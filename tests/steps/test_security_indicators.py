#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Kevin Postlethwait
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

"""Test Security Indicator step."""

import flexmock
import pytest

from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.steps import SecurityIndicatorStep
from thoth.adviser.exceptions import NotAcceptable
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages import GraphDatabase

from ..base import AdviserTestCase


class TestSecurityIndicatorStep(AdviserTestCase):
    """Test different aspects of si pipeline step."""

    _SECURITY_INFO_EXISTS = {
        "severity_high_confidence_high": 1,
        "severity_high_confidence_medium": 5,
        "severity_high_confidence_low": 3,
        "severity_medium_confidence_high": 2,
        "severity_medium_confidence_medium": 0,
        "severity_medium_confidence_low": 8,
        "severity_low_confidence_high": 21,
        "severity_low_confidence_medium": 6,
        "severity_low_confidence_low": 0,
        "number_of_lines_with_code_in_python_files": 692,
    }

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.STABLE, RecommendationType.SECURITY])
    def test_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType) -> None:
        """Test including this pipeline unit."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        assert builder_context.is_adviser_pipeline()
        assert SecurityIndicatorStep.should_include(builder_context) == {}

    @pytest.mark.parametrize(
        "recommendation_type", [RecommendationType.LATEST, RecommendationType.PERFORMANCE, RecommendationType.TESTING]
    )
    def test_no_include(self, builder_context: PipelineBuilderContext, recommendation_type,) -> None:
        """Test not including this pipeline unit step."""
        builder_context.decision_type = None
        builder_context.recommendation_type = recommendation_type
        assert SecurityIndicatorStep.should_include(builder_context) is None

    def test_security_indicator_scoring(self) -> None:
        """Make sure we do score security indicators when the info is available."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_si_aggregated_python_package_version").with_args(
            package_name="flask", package_version="0.12.0", index_url="https://pypi.org/simple"
        ).and_return(self._SECURITY_INFO_EXISTS).once()

        package_version = PackageVersion(
            name="flask", version="==0.12.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(graph=GraphDatabase())
        with SecurityIndicatorStep.assigned_context(context):
            step = SecurityIndicatorStep()
            result = step.run(None, package_version)

        assert result is not None
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], float)

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.SECURITY])
    def test_security_indicator_scoring_missing_secure(self, recommendation_type) -> None:
        """Make sure we don't accept package if si info is missing when recommendation is secure."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_si_aggregated_python_package_version").with_args(
            package_name="flask", package_version="0.12.0", index_url="https://pypi.org/simple"
        ).and_return(None).once()

        package_version = PackageVersion(
            name="flask", version="==0.12.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(graph=GraphDatabase())
        context.recommendation_type = recommendation_type
        with pytest.raises(NotAcceptable):
            with SecurityIndicatorStep.assigned_context(context):
                step = SecurityIndicatorStep()
                step.run(None, package_version)

    _FLASK_JUSTIFICATION = [
        {
            "type": "WARNING",
            "message": "flask===0.12.0 on https://pypi.org/simple has no gathered information regarding security.",
        }
    ]

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.STABLE])
    def test_security_indicator_scoring_missing_stable(self, recommendation_type) -> None:
        """Make sure package is kept even if no score exists for security indicators and add justification."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_si_aggregated_python_package_version").with_args(
            package_name="flask", package_version="0.12.0", index_url="https://pypi.org/simple"
        ).and_return(None).once()

        package_version = PackageVersion(
            name="flask", version="==0.12.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(graph=GraphDatabase())
        context.recommendation_type = recommendation_type
        with SecurityIndicatorStep.assigned_context(context):
            step = SecurityIndicatorStep()
            result = step.run(None, package_version)

        assert result is not None
        assert isinstance(result, tuple) and len(result) == 2
        assert result[0] == 0
        assert result[1] == self._FLASK_JUSTIFICATION
