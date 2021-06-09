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

"""Tests related to filtering out Python packages that are not part of a new release."""

import json

import pytest
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import PackageUpdateSieve
from thoth.adviser.context import Context
from thoth.common import get_justification_link as jl
from thoth.python import Source
from thoth.python import PackageVersion

from ..base import AdviserUnitTestCase


class TestPackageUpdateSieve(AdviserUnitTestCase):
    """Tests related to filtering out Python packages that are not part of a new release."""

    UNIT_TESTED = PackageUpdateSieve
    _PACKAGE_UPDATE_DICT = {
        "package_name": "tensorflow",
        "package_version": "2.5.0",
        "index_url": "https://pypi.org/simple",
    }

    @pytest.mark.skip(
        reason="Skip default configuration as default is not considered valid and needs further adjustments"
    )
    def test_default_configuration(self) -> None:
        """Skip testing default configuration."""

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.UNIT_TESTED._PACKAGE_UPDATE = json.dumps(self._PACKAGE_UPDATE_DICT)

        try:
            builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)
            self.verify_multiple_should_include(builder_context)
        finally:
            self.UNIT_TESTED._PACKAGE_UPDATE = None

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test including this pipeline unit based on supplied package."""
        self.UNIT_TESTED._PACKAGE_UPDATE = json.dumps(self._PACKAGE_UPDATE_DICT)

        try:
            assert list(self.UNIT_TESTED.should_include(builder_context)) == [self._PACKAGE_UPDATE_DICT]
        finally:
            self.UNIT_TESTED._PACKAGE_UPDATE = None

    def test_should_include_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test NOT including this pipeline unit when no package is supplied."""
        assert self.UNIT_TESTED._PACKAGE_UPDATE is None

        try:
            assert list(self.UNIT_TESTED.should_include(builder_context)) == []
        finally:
            self.UNIT_TESTED._PACKAGE_UPDATE = None

    def test_sieve(self, context: Context) -> None:
        """Test removing packages that are not part of an update."""
        pypi = Source("https://pypi.org/simple")
        pv0 = PackageVersion(name="tensorflow", version="==2.5.0", index=pypi, develop=False)
        pv1 = PackageVersion(name="tensorflow", version="==2.4.0", index=pypi, develop=False)
        pv2 = PackageVersion(name="tensorflow", version="==2.3.0", index=pypi, develop=False)

        assert not context.stack_info

        self.UNIT_TESTED._PACKAGE_UPDATE = json.dumps(self._PACKAGE_UPDATE_DICT)
        try:
            unit = self.UNIT_TESTED()
            unit.update_configuration(self._PACKAGE_UPDATE_DICT)

            unit.pre_run()
            with self.UNIT_TESTED.assigned_context(context):
                assert list(unit.run(pv for pv in (pv0, pv1, pv2))) == [pv0]
        finally:
            self.UNIT_TESTED._PACKAGE_UPDATE = None

        assert context.stack_info == [
            {
                "link": jl("update"),
                "message": "Removing package ('tensorflow', '2.4.0', "
                "'https://pypi.org/simple') as advising on a new release",
                "package_name": "tensorflow",
                "type": "WARNING",
            },
            {
                "link": jl("update"),
                "message": "Removing package ('tensorflow', '2.3.0', "
                "'https://pypi.org/simple') as advising on a new release",
                "package_name": "tensorflow",
                "type": "WARNING",
            },
        ]
