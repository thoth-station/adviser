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

"""Test removing pre-releases in direct dependencies."""

from flexmock import flexmock
import pytest

from thoth.adviser.sieves import CutPreReleasesSieve
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.python import Source
from thoth.python import PackageVersion
from thoth.python import Project

from ..base import AdviserUnitTestCase


class TestCutPreReleasesSieve(AdviserUnitTestCase):
    """Test removing dependencies based on pre-releases configuration."""

    UNIT_TESTED = CutPreReleasesSieve

    _CASE_DISALLOWED_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[[source]]
url = "https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"
verify_ssl = true
name = "aicoe"

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = false
"""

    _CASE_ALLOWED_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[[source]]
url = "https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"
verify_ssl = true
name = "aicoe"

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = true
"""

    _CASE_SELECTIVE_PRERELEASES_ALLOWED_PIPFILE = """
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
        builder_context.project = Project.from_strings(self._CASE_DISALLOWED_PIPFILE)

        assert builder_context.is_adviser_pipeline()
        assert list(CutPreReleasesSieve.should_include(builder_context)) == [{}]

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
    def test_not_include(
        self,
        builder_context: PipelineBuilderContext,
        recommendation_type: RecommendationType,
    ) -> None:
        """Test not including this pipeline unit."""
        builder_context.recommendation_type = recommendation_type
        builder_context.project = Project.from_strings(self._CASE_ALLOWED_PIPFILE)

        assert builder_context.is_adviser_pipeline()
        assert list(CutPreReleasesSieve.should_include(builder_context)) == []

    def test_not_include_thoth_prereleases_allowed(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including this pipeline unit."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project = Project.from_strings(self._CASE_SELECTIVE_PRERELEASES_ALLOWED_PIPFILE)

        assert builder_context.is_adviser_pipeline()
        assert list(CutPreReleasesSieve.should_include(builder_context)) == []

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST
        builder_context.project = Project.from_strings(self._CASE_DISALLOWED_PIPFILE)
        self.verify_multiple_should_include(builder_context)

    def test_remove_pre_releases_disallowed_noop(self) -> None:
        """Test removing dependencies not hitting limit causes a noop."""
        tf_2_0_0 = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_DISALLOWED_PIPFILE))
        with CutPreReleasesSieve.assigned_context(context):
            sieve = CutPreReleasesSieve()
            assert list(sieve.run(p for p in [tf_2_0_0])) == [tf_2_0_0]

    def test_pre_releases_disallowed_removal(self) -> None:
        """Test no removals if pre-releases are allowed."""
        tf_2_0_0rc0 = PackageVersion(
            name="tensorflow",
            version="==2.0.0rc0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/os/fedora/30/jemalloc/simple/"),
            develop=False,
        )

        context = flexmock(project=Project.from_strings(self._CASE_DISALLOWED_PIPFILE))
        with CutPreReleasesSieve.assigned_context(context):
            sieve = CutPreReleasesSieve()
            assert list(sieve.run(p for p in [tf_2_0_0rc0])) == []
