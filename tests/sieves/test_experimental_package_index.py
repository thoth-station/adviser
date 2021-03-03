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

"""Test sieve which filters out packages based on index configuration."""

import itertools

import pytest

from thoth.adviser.context import Context
from thoth.adviser.sieves import PackageIndexConfigurationSieve
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.python import Project

from ..base import AdviserUnitTestCase


class TestPackageIndexConfigurationSieve(AdviserUnitTestCase):
    """Test filtering out packages based on index configuration."""

    UNIT_TESTED = PackageIndexConfigurationSieve

    _CASE_DEFAULT = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"
"""

    _CASE_ENABLED = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[[source]]
url = "https://thoth-station.ninja/simple"
verify_ssl = true
name = "thoth"

[packages]
tensorflow = {version="*", index="thoth"}
flask = "*"

[thoth]
disable_index_adjustment = true
"""

    @pytest.mark.parametrize(
        "recommendation_type",
        [
            RecommendationType.STABLE,
            RecommendationType.PERFORMANCE,
            RecommendationType.SECURITY,
            RecommendationType.LATEST,
            RecommendationType.TESTING,
        ],
    )
    def test_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
    ) -> None:
        """Test including this pipeline unit."""
        builder_context.recommendation_type = recommendation_type
        builder_context.project = Project.from_strings(self._CASE_ENABLED)

        assert builder_context.is_adviser_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [
            {
                "package_name": "tensorflow",
                "index_url": "https://thoth-station.ninja/simple",
            }
        ]

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project = Project.from_strings(self._CASE_ENABLED)
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.skip(reason="The pipeline unit configuration is specific to Pipfile configuration")
    def test_default_configuration(self, builder_context: PipelineBuilderContext) -> None:
        """Test the default configuration."""

    @pytest.mark.parametrize(
        "recommendation_type,case",
        itertools.product(
            [
                RecommendationType.STABLE,
                RecommendationType.PERFORMANCE,
                RecommendationType.SECURITY,
                RecommendationType.LATEST,
                RecommendationType.TESTING,
            ],
            [_CASE_DEFAULT],
        ),
    )
    def test_not_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
        case: str,
    ) -> None:
        """Test not including this pipeline unit."""
        builder_context.recommendation_type = recommendation_type
        builder_context.project = Project.from_strings(case)

        assert builder_context.is_adviser_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_filter_index_url(self, context: Context) -> None:
        """Test NOT removing dependencies based on pre-release configuration."""
        pv = PackageVersion(
            name="tensorflow",
            version="==2.4.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        context.project = Project.from_strings(self._CASE_ENABLED)
        sieve = self.UNIT_TESTED()
        sieve.update_configuration(
            {"package_name": "tensorflow", "index_url": context.project.pipfile.packages["tensorflow"].index.url}
        )

        assert not context.stack_info
        with self.UNIT_TESTED.assigned_context(context):
            assert list(sieve.run(p for p in [pv])) == []

        assert len(context.stack_info) == 1
        assert self.verify_justification_schema(context.stack_info)

    def test_no_filter_index_url(self, context: Context) -> None:
        """Test no removals if pre-releases are allowed."""
        project = Project.from_strings(self._CASE_ENABLED)
        source = project.pipfile.packages["tensorflow"].index

        pv = PackageVersion(
            name="tensorflow",
            version="==2.4.0",
            index=source,
            develop=False,
        )

        context.project = project
        sieve = self.UNIT_TESTED()
        sieve.update_configuration({"package_name": "tensorflow", "index_url": source.url})

        assert not context.stack_info
        with self.UNIT_TESTED.assigned_context(context):
            assert list(sieve.run(p for p in [pv])) == [pv]

        assert not context.stack_info, "No justification should be provided"
