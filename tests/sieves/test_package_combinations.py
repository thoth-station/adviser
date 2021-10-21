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

"""Test sieve for computing package combinations."""

import pytest

from thoth.adviser.context import Context
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import PackageCombinationsSieve
from thoth.python import Source
from thoth.python import PackageVersion

from ..base import AdviserUnitTestCase


class TestPackageCombinationsSieve(AdviserUnitTestCase):
    """Test sieve for computing package combinations."""

    UNIT_TESTED = PackageCombinationsSieve

    @pytest.mark.skip(reason="Package combinations sieve is never registered.")
    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""

    def test_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test obtaining default configuration."""
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_pre_run(self, context: Context) -> None:
        """Test initializing before each run."""
        unit = self.UNIT_TESTED()
        unit.update_configuration({"package_name": None, "package_combinations": ["flask", "werkzeug"]})
        unit._package_tuples_seen = {"flask": ("flask", "0.12", "https://pypi.org/simple")}
        unit._package_combinations = {"foo", "bar"}

        unit.pre_run()

        assert unit._package_combinations == {"flask", "werkzeug"}
        assert unit._package_tuples_seen == {}

    @pytest.mark.skip(reason="Call to pre_run tested below.")
    def test_super_pre_run(self, context: Context) -> None:
        """This test case is tested below."""

    def test_run(self) -> None:
        """Test computing package combinations."""
        pypi = Source("https://pypi.org/simple")
        pv0 = PackageVersion(
            name="flask",
            version="==1.0.0",
            index=pypi,
            develop=False,
        )
        pv1 = PackageVersion(
            name="flask",
            version="==0.12",
            index=pypi,
            develop=False,
        )
        pv2 = PackageVersion(
            name="pandas",
            version="==1.3.3",
            index=pypi,
            develop=False,
        )
        pv3 = PackageVersion(
            name="pandas",
            version="==1.0.0",
            index=pypi,
            develop=False,
        )

        unit = self.UNIT_TESTED()
        unit.update_configuration(
            {
                "package_name": None,
                "package_combinations": ["flask", "werkzeug"],
            }
        )
        unit.unit_run = True
        unit.pre_run()

        assert unit.unit_run is False, "Parent pre_run was probably not called"

        assert list(unit.run((pv for pv in (pv0,)))) == [pv0]
        assert list(unit.run((pv for pv in (pv1,)))) == [pv1]
        assert list(unit.run((pv for pv in (pv2,)))) == [pv2]
        assert list(unit.run((pv for pv in (pv3,)))) == []
        assert list(unit.run((pv for pv in (pv2,)))) == [pv2]
        assert list(unit.run((pv for pv in (pv1,)))) == [pv1]
        assert list(unit.run((pv for pv in (pv0,)))) == [pv0]

        assert unit._package_combinations == {"flask", "werkzeug"}
        assert unit._package_tuples_seen == {
            "pandas": pv2.to_tuple(),
        }
