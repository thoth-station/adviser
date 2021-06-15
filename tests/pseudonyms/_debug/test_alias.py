#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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

"""Test alias pseudonym."""

import pytest

from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.pseudonyms import AliasPseudonym
from thoth.adviser.context import Context
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestAliasPseudonym(AdviserUnitTestCase):
    """Test related to alias pseudonym used for including a generic alias in the resolution process."""

    UNIT_TESTED = AliasPseudonym

    @pytest.mark.skip(reason="This pipeline unit is never registered implicitly")
    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""

    @pytest.mark.skip(reason="The default configuration should not be used")
    def test_default_configuration(self) -> None:
        """Check default configuration available in the pipeline unit implementation."""

    @pytest.mark.skip(reason="Package name should be always provided explicitly")
    def test_provided_package_version(self) -> None:
        """Check providing package_name in the default pipeline configuration."""

    def test_no_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test including this pipeline unit, never."""
        builder_context.decision_type = None
        builder_context.recommendation_type = RecommendationType.STABLE
        assert builder_context.is_adviser_pipeline()
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    @pytest.mark.parametrize(
        "tf_version,index_url",
        [
            ("2.2.0", "https://pypi.org/simple"),
            (None, "https://pypi.org/simple"),
            ("2.2.0", None),
            (None, None),
        ],
    )
    def test_run_pseudonym(self, context: Context, tf_version: str, index_url: str) -> None:
        """Test adding a pseudonym for the given package."""
        unit = self.UNIT_TESTED()
        unit.update_configuration(
            {
                "package_name": "tensorflow",
                "package_version": tf_version,
                "index_url": index_url,
                "aliases": [
                    {
                        "package_name": "intel-tensorflow",
                        "package_version": "2.2.0",
                        "index_url": "https://pypi.org/simple",
                    },
                    {
                        "package_name": "tensorflow-gpu",
                        "package_version": "2.2.0",
                        "index_url": "https://pypi.org/simple",
                    },
                    {
                        "package_name": "tensorflow",
                        "package_version": "2.2.0",
                        "index_url": "https://thoth-station.ninja/simple",
                    },
                ],
            }
        )

        package_version = PackageVersion(
            name="tensorflow", version="==2.2.0", index=Source("https://pypi.org/simple"), develop=False
        )
        result = set(unit.run(package_version))
        assert len(result) == 3
        assert result == {
            ("intel-tensorflow", "2.2.0", "https://pypi.org/simple"),
            ("tensorflow-gpu", "2.2.0", "https://pypi.org/simple"),
            ("tensorflow", "2.2.0", "https://thoth-station.ninja/simple"),
        }

    @pytest.mark.parametrize(
        "pv_version,pv_index_url,conf_version,conf_index_url",
        [
            ("==1.1.1", "https://pypi.org/simple", "2.2.0", "https://pypi.org/simple"),  # No version match.
            ("==1.1.1", "https://pypi.org/simple", "2.2.0", None),  # No version match.
            (
                "==2.2.0",
                "https://thoth-station.ninja/simple",
                "2.2.0",
                "https://pypi.org/simple",
            ),  # No index url match.
            ("==2.2.0", "https://thoth-station.ninja/simple", None, "https://pypi.org/simple"),  # No index url match.
            ("==1.1.1", "https://thoth-station.ninja/simple", "2.2.0", "https://pypi.org/simple"),  # No match.
        ],
    )
    def test_run_noop(
        self, context: Context, pv_version: str, pv_index_url: str, conf_version: str, conf_index_url: str
    ) -> None:
        """Test not adding a pseudonym for the given package."""
        unit = self.UNIT_TESTED()
        unit.update_configuration(
            {
                "package_name": "tensorflow",
                "package_version": conf_version,
                "index_url": conf_index_url,
                "aliases": [
                    {
                        "package_name": "intel-tensorflow",
                        "package_version": "2.2.0",
                        "index_url": "https://pypi.org/simple",
                    },
                    {
                        "package_name": "tensorflow-gpu",
                        "package_version": "2.2.0",
                        "index_url": "https://pypi.org/simple",
                    },
                    {
                        "package_name": "tensorflow",
                        "package_version": "2.2.0",
                        "index_url": "https://thoth-station.ninja/simple",
                    },
                ],
            }
        )

        package_version = PackageVersion(
            name="tensorflow", version=pv_version, index=Source(pv_index_url), develop=False
        )
        result = list(unit.run(package_version))
        assert len(result) == 0
