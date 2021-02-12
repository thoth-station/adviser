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

"""Test removing legacy versions from the resolution process."""

from thoth.adviser.context import Context
from thoth.adviser.sieves import LegacyVersionSieve
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.python import Source
from thoth.python import PackageVersion

from ..base import AdviserUnitTestCase


class TestLegacyVersionSieve(AdviserUnitTestCase):
    """Test removing legacy versions from the resolution process."""

    UNIT_TESTED = LegacyVersionSieve

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)
        self.verify_multiple_should_include(builder_context)

    def test_include(
        self,
        builder_context: PipelineBuilderContext,
    ) -> None:
        """Test including this pipeline unit."""
        builder_context.recommendation_type = RecommendationType.LATEST
        assert builder_context.is_adviser_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

    def test_remove_legacy_version_noop(self, context: Context) -> None:
        """Test not removing not legacy versions."""
        pv1 = PackageVersion(
            name="flask",
            version="==0.0dev0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        pv2 = PackageVersion(
            name="tensorflow",
            version="==2.0.0rc0",
            index=pv1.index,
            develop=False,
        )

        with self.UNIT_TESTED.assigned_context(context):
            sieve = self.UNIT_TESTED()
            assert list(sieve.run(p for p in [pv1, pv2])) == [pv1, pv2]

    def test_remove_legacy_version(self, context: Context) -> None:
        """Test removing legacy versions."""
        pv1 = PackageVersion(
            name="flask",
            version="==foo",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        with self.UNIT_TESTED.assigned_context(context):
            sieve = self.UNIT_TESTED()
            assert list(sieve.run(p for p in [pv1])) == []
