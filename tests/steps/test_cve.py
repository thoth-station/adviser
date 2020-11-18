#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

import flexmock
import pytest

from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import NotAcceptable
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
        "advisory": "flask version Before 0.12.3 contains a CWE-20: Improper Input Validation "
        "vulnerability in flask that can result in Large amount of memory usage "
        "possibly leading to denial of service.",
        "cve_name": "CVE-2018-1000656",
        "version_range": "<0.12.3",
        "cve_id": "pyup.io-36388",
    }

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.SECURITY
        self.verify_multiple_should_include(builder_context)

    def test_cve_penalization(self) -> None:
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

        context = flexmock(graph=GraphDatabase(), recommendation_type=RecommendationType.TESTING)
        with CvePenalizationStep.assigned_context(context):
            step = CvePenalizationStep()
            result = step.run(None, package_version)

        assert result is not None
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], float)
        assert result[0] == 1 * CvePenalizationStep.CONFIGURATION_DEFAULT["cve_penalization"]
        assert isinstance(result[1], list)
        assert result[1] == [self._FLASK_CVE]
        assert self.verify_justification_schema(result[1])

    def test_no_cve_record(self) -> None:
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

        context = flexmock(graph=GraphDatabase())
        with CvePenalizationStep.assigned_context(context):
            step = CvePenalizationStep()
            result = step.run(None, package_version)

        assert result is None

    def test_cve_not_acceptable(self) -> None:
        """Test raising an exception if a secure software stack should be resolved."""
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

        context = flexmock(graph=GraphDatabase(), recommendation_type=RecommendationType.SECURITY)
        step = CvePenalizationStep()
        with CvePenalizationStep.assigned_context(context):
            assert not step._messages_logged
            with pytest.raises(NotAcceptable):
                step.run(None, package_version)

        assert len(step._messages_logged) == 1
        assert ("flask", "0.12.0", "https://pypi.org/simple") in step._messages_logged
