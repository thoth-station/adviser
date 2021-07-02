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

"""Test filtering out Python packages already present in the base image."""

from typing import Optional

import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.sieves import ThothS2IPackagesSieve
from thoth.python import PackageVersion
from thoth.python import Source

from ..base import AdviserUnitTestCase


class TestThothS2IPackagesSieve(AdviserUnitTestCase):
    """Test filtering out packages based on packages present in S2I."""

    UNIT_TESTED = ThothS2IPackagesSieve

    _EXAMPLE_PYTHON_PACKAGES_PRESENT = [
        # S2I packages
        {
            "location": "/opt/app-root/lib/python3.8/site-packages",
            "package_name": "jupyterhub",
            "package_version": "1.4.1",
        },
        {
            "location": "/opt/app-root/lib/python3.8/site-packages",
            "package_name": "wheel",
            "package_version": "0.36.2",
        },
        {
            "location": "/opt/app-root/lib/python3.8/site-packages",
            "package_name": "tensorflow",
            "package_version": "2.5.0",
        },
        {
            "location": "/opt/app-root/lib/python3.8/site-packages",
            "package_name": "numpy",
            "package_version": "1.21.0",
        },
        # System packages
        {
            "location": "/usr/lib64/python3.6/site-packages",
            "package_name": "gpg",
            "package_version": "1.13.1",
        },
        {
            "location": "/usr/lib/python3.6/site-packages",
            "package_name": "requests",
            "package_version": "2.20.0",
        },
    ]

    @pytest.mark.skip(reason="Default configuration is adjusted")
    def test_default_configuration(self) -> None:
        """Skip as default configuration is adjusted."""

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.LATEST

        builder_context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0"

        builder_context.graph.should_receive("get_last_analysis_document_id").with_args(
            "quay.io/thoth-station/s2i-thoth-ubi8-py38", "1.0.0", is_external=False
        ).and_return("package-extract-foo").once()

        # Return only one package as the test tests for one inclusion.
        builder_context.graph.should_receive("get_python_package_version_all").with_args(
            "package-extract-foo"
        ).and_return([self._EXAMPLE_PYTHON_PACKAGES_PRESENT[0]]).once()

        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize(
        "base_image",
        [
            None,
            "fedora:32",
            "quay.io/thoth-station/s2i-thoth-ubi8-py38",  # No version.
        ],
    )
    def test_no_should_include(self, base_image: Optional[str], builder_context: PipelineBuilderContext) -> None:
        """Test not including this pipeline unit."""
        builder_context.project.runtime_environment.base_image = base_image
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test including this pipeline unit."""
        builder_context.project.runtime_environment.base_image = "quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0"

        builder_context.graph.should_receive("get_last_analysis_document_id").with_args(
            "quay.io/thoth-station/s2i-thoth-ubi8-py38", "1.0.0", is_external=False
        ).and_return("package-extract-foo").once()

        builder_context.graph.should_receive("get_python_package_version_all").with_args(
            "package-extract-foo"
        ).and_return(self._EXAMPLE_PYTHON_PACKAGES_PRESENT).once()

        assert list(self.UNIT_TESTED.should_include(builder_context)) == [
            {
                "package_name": "jupyterhub",
                "package_version": "1.4.1",
            },
            {
                "package_name": "wheel",
                "package_version": "0.36.2",
            },
            {
                "package_name": "tensorflow",
                "package_version": "2.5.0",
            },
            {
                "package_name": "numpy",
                "package_version": "1.21.0",
            },
        ]

    def test_sieve(self, context: Context) -> None:
        """Test removing Python packages present in the base image."""
        pypi = Source("https://pypi.org/simple")
        pv1 = PackageVersion(name="tensorflow", version="==2.5.0", index=pypi, develop=False)
        pv2 = PackageVersion(name="tensorflow", version="==2.4.0", index=pypi, develop=False)
        pv3 = PackageVersion(name="tensorflow", version="==2.3.0", index=pypi, develop=False)

        package_versions = [pv1, pv2, pv3]

        unit = self.UNIT_TESTED()
        unit.update_configuration({"package_name": pv2.name, "package_version": pv2.locked_version})
        unit.pre_run()

        with unit.assigned_context(context):
            assert list(unit.run((pv for pv in package_versions))) == [pv2]
