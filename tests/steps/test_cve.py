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

"""Test scoring (penalization) based on a CVE."""

from flexmock import flexmock
import pytest

from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.steps import CvePenalizationStep
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages import GraphDatabase

from ..base import AdviserUnitTestCase


class TestCvePenalizationStep(AdviserUnitTestCase):
    """Test scoring (penalization) based on a CVE."""

    UNIT_TESTED = CvePenalizationStep

    _CASE_CANDIDATES = [
        ("flask", "0.12.0", "https://pypi.org/simple"),
        ("click", "2.0", "https://pypi.org/simple"),
        ("pyyaml", "3.12", "https://pypi.org/simple"),
    ]

    _FLASK_CVE = {
        "details": "flask version Before 0.12.3 contains a CWE-20: Improper Input Validation "
        "vulnerability in flask that can result in Large amount of memory usage "
        "possibly leading to denial of service.",
        "cve_id": "CVE-ID",
        "aggregated_at": "2021-06-02T08:23:17.11783Z",
    }

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.SECURITY])
    def test_no_include(self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType):
        """Check not including the given pipeline unit for recommendation type SECURITY."""
        builder_context.recommendation_type = recommendation_type
        builder_context.decision_type = None
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    @pytest.mark.parametrize(
        "recommendation_type",
        [
            RecommendationType.LATEST,
            RecommendationType.TESTING,
            RecommendationType.STABLE,
            RecommendationType.PERFORMANCE,
        ],
    )
    def test_should_include_recommendation_type(
        self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType
    ):
        """Check inclusion for various recommendation types."""
        builder_context.recommendation_type = recommendation_type
        builder_context.decision_type = None
        if recommendation_type in (RecommendationType.LATEST, RecommendationType.TESTING):
            assert list(self.UNIT_TESTED.should_include(builder_context)) == [{"cve_penalization": 0.0}]
        else:
            assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.PERFORMANCE, RecommendationType.STABLE])
    def test_cve_penalization(self, recommendation_type: RecommendationType) -> None:
        """Make sure a CVE affects stack score."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records_all").with_args(
            package_name="flask", package_version="0.12.0"
        ).and_return([self._FLASK_CVE]).once()

        package_version = PackageVersion(
            name="flask",
            version="==0.12.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        context = flexmock(graph=GraphDatabase(), recommendation_type=recommendation_type)
        with CvePenalizationStep.assigned_context(context):
            step = CvePenalizationStep()
            result = step.run(None, package_version)

        assert result is not None
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], float)
        assert result[0] == 1 * CvePenalizationStep.CONFIGURATION_DEFAULT["cve_penalization"]
        assert isinstance(result[1], list)
        assert result[1] == [
            {
                "link": "https://thoth-station.ninja/j/cve",
                "message": "Package  ('flask', '0.12.0', 'https://pypi.org/simple') has a CVE 'CVE-ID'",
                "advisory": "flask version Before 0.12.3 contains a CWE-20: Improper Input Validation "
                "vulnerability in flask that can result in Large amount of memory usage "
                "possibly leading to denial of service.",
                "package_name": "flask",
                "type": "WARNING",
            }
        ]
        assert self.verify_justification_schema(result[1])

    @pytest.mark.parametrize("recommendation_type", [RecommendationType.LATEST, RecommendationType.TESTING])
    def test_cve_no_penalization(self, recommendation_type: RecommendationType) -> None:
        """Make sure score penalization is not done for testing and latest recommendation types."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records_all").with_args(
            package_name="flask", package_version="0.12.0"
        ).and_return([self._FLASK_CVE]).once()

        package_version = PackageVersion(
            name="flask",
            version="==0.12.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        context = flexmock(graph=GraphDatabase(), recommendation_type=recommendation_type, stack_info=[])
        with CvePenalizationStep.assigned_context(context):
            step = CvePenalizationStep()
            result = step.run(None, package_version)

        assert result is not None
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], float)
        assert result[0] == 0.0
        assert isinstance(result[1], list)
        assert result[1] == [
            {
                "link": "https://thoth-station.ninja/j/cve",
                "message": "Package  ('flask', '0.12.0', 'https://pypi.org/simple') has a CVE 'CVE-ID'",
                "advisory": "flask version Before 0.12.3 contains a CWE-20: Improper Input Validation "
                "vulnerability in flask that can result in Large amount of memory usage "
                "possibly leading to denial of service.",
                "package_name": "flask",
                "type": "WARNING",
            }
        ]
        assert self.verify_justification_schema(result[1])

    @pytest.mark.parametrize("recommendation_type", RecommendationType.__members__.values())
    def test_no_cve_record(self, recommendation_type: RecommendationType) -> None:
        """Make sure no CVEs do not affect CVE scoring."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records_all").with_args(
            package_name="flask", package_version="0.12.0"
        ).and_return([]).once()

        package_version = PackageVersion(
            name="flask",
            version="==0.12.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        context = flexmock(graph=GraphDatabase(), recommendation_type=recommendation_type)
        with CvePenalizationStep.assigned_context(context):
            step = CvePenalizationStep()
            result = step.run(None, package_version)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == 0.0
        assert result[1] == [
            {
                "link": "https://thoth-station.ninja/j/no_cve",
                "message": "No known CVE known for 'flask' in version '0.12.0'",
                "package_name": "flask",
                "type": "INFO",
            }
        ]
