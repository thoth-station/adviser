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

"""Test removing pre-releases based on Pipfile configuration in Thoth section."""

import itertools

import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import SelectiveCutPreReleasesSieve
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.python import Project

from ..base import AdviserUnitTestCase


class TestSelectiveCutPreReleasesSieve(AdviserUnitTestCase):
    """Test removing pre-releases based on Pipfile configuration in Thoth section."""

    UNIT_TESTED = SelectiveCutPreReleasesSieve

    _CASE_GLOBAL_DISALLOWED_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = false

[thoth.allow_prereleases]
tensorflow = true
flask = false
"""

    _CASE_GLOBAL_DISALLOWED_EMPTY_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = false
"""

    _CASE_GLOBAL_ALLOWED_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = true

[thoth.allow_prereleases]
tensorflow = true
flask = false
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
        builder_context.project = Project.from_strings(self._CASE_GLOBAL_DISALLOWED_PIPFILE)

        assert builder_context.is_adviser_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [
            {
                "package_name": None,
                "allow_prereleases": {
                    "tensorflow": True,
                    "flask": False,
                },
            }
        ]

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project = Project.from_strings(self._CASE_GLOBAL_DISALLOWED_PIPFILE)
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
            [_CASE_GLOBAL_ALLOWED_PIPFILE, _CASE_GLOBAL_DISALLOWED_EMPTY_PIPFILE],
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
        builder_context.project = Project.from_strings(self._CASE_GLOBAL_ALLOWED_PIPFILE)

        assert builder_context.is_adviser_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    @pytest.mark.parametrize("package_name,package_version", [("tensorflow", "2.4.0rc1"), ("flask", "1.0")])
    def test_remove_pre_releases_disallowed_noop(
        self, context: Context, package_name: str, package_version: str
    ) -> None:
        """Test NOT removing dependencies based on pre-release configuration."""
        pv = PackageVersion(
            name=package_name,
            version=f"=={package_version}",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        project = Project.from_strings(self._CASE_GLOBAL_DISALLOWED_PIPFILE)
        context.project = project
        sieve = self.UNIT_TESTED()
        sieve.update_configuration({"package_name": None, "allow_prereleases": project.pipfile.thoth.allow_prereleases})

        assert not context.stack_info
        with self.UNIT_TESTED.assigned_context(context):
            assert list(sieve.run(p for p in [pv])) == [pv]

        assert not context.stack_info, "No stack information should be provided"

    @pytest.mark.parametrize(
        "package_name,package_version",
        [
            ("flask", "1.0dev0"),  # Disabled explicitly.
            ("numpy", "1.0dev0"),  # Disabled implicitly.
        ],
    )
    def test_pre_releases_disallowed_removal(self, context: Context, package_name: str, package_version: str) -> None:
        """Test no removals if pre-releases are allowed."""
        pv = PackageVersion(
            name=package_name,
            version=f"=={package_version}",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        project = Project.from_strings(self._CASE_GLOBAL_DISALLOWED_PIPFILE)
        context.project = project
        sieve = self.UNIT_TESTED()
        sieve.update_configuration({"package_name": None, "allow_prereleases": project.pipfile.thoth.allow_prereleases})

        assert not context.stack_info
        with self.UNIT_TESTED.assigned_context(context):
            assert list(sieve.run(p for p in [pv])) == []

        assert len(context.stack_info) == 1
        assert self.verify_justification_schema(context.stack_info)
