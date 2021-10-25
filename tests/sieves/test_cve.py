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

"""Test filtering based on a CVE."""

import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import CveSieve
from thoth.common import get_justification_link as jl
from thoth.python import PackageVersion
from thoth.python import Source

from ..base import AdviserUnitTestCase


class TestCveSieve(AdviserUnitTestCase):
    """Test filtering based on a CVE."""

    UNIT_TESTED = CveSieve

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
        builder_context.recommendation_type = RecommendationType.SECURITY
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize(
        "recommendation_type",
        [
            RecommendationType.LATEST,
            RecommendationType.STABLE,
            RecommendationType.PERFORMANCE,
            RecommendationType.TESTING,
        ],
    )
    def test_should_include_recommendation_type(
        self, builder_context: PipelineBuilderContext, recommendation_type: RecommendationType
    ):
        """Check not including the given pipeline unit for recommendations other than SECURITY."""
        builder_context.recommendation_type = recommendation_type
        builder_context.decision_type = None
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_cve_sieve(self, context: Context) -> None:
        """Make sure a CVE filters out packages."""
        context.graph.should_receive("get_python_cve_records_all").with_args(
            package_name="flask", package_version="0.12.0"
        ).and_return([self._FLASK_CVE])

        context.graph.should_receive("get_python_cve_records_all").with_args(
            package_name="flask", package_version="1.0.0"
        ).and_return([])

        pv1 = PackageVersion(
            name="flask",
            version="==0.12.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        pv2 = PackageVersion(
            name="flask",
            version="==1.0.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        assert not context.stack_info

        context.recommendation_type = RecommendationType.SECURITY

        with self.UNIT_TESTED.assigned_context(context):
            unit = self.UNIT_TESTED()
            result = list(unit.run((pv for pv in (pv1, pv2))))

        assert result is not None
        assert result == [pv2]
        assert context.stack_info == [
            {
                "link": jl("cve"),
                "message": "Skipping including package ('flask', '0.12.0', "
                "'https://pypi.org/simple') as a CVE 'CVE-ID' was found",
                "type": "WARNING",
            }
        ]
        assert self.verify_justification_schema(context.stack_info)
