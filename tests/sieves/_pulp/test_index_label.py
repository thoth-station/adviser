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

"""Test a sieve that provides only packages available on Operate First Pulp instance."""

from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import PulpIndexLabelSieve
from thoth.adviser.sieves._pulp import PULP_URL
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestPulpIndexLabelSieve(AdviserUnitTestCase):
    """Test a sieve that provides only packages available on Operate First Pulp instance."""

    UNIT_TESTED = PulpIndexLabelSieve

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(
            recommendation_type=RecommendationType.LATEST, labels={"opf-pulp-indexes": "solely"}
        )
        self.verify_multiple_should_include(builder_context)

    def test_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test not including this pipeline unit if the index=pulp label is not provided."""
        builder_context.labels.clear()
        self.UNIT_TESTED.should_include(builder_context)

    def test_run(self, context: Context) -> None:
        """Test filtering packages that are not hosted on Operate First Pulp."""
        tf_pypi = PackageVersion(
            name="tensorflow",
            version="==2.7.0",
            index=Source("https://pypi.org/simple"),
            develop=False,
        )

        tf_pulp = PackageVersion(
            name="tensorflow",
            version="==2.7.0",
            index=Source(f"{PULP_URL}simple"),
            develop=False,
        )

        with self.UNIT_TESTED.assigned_context(context):
            sieve = self.UNIT_TESTED()
            assert list(sieve.run(p for p in [tf_pypi, tf_pulp])) == [tf_pulp]
