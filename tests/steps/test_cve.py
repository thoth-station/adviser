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

from thoth.adviser.steps import CvePenalizationStep
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages import GraphDatabase

from ..base import AdviserTestCase


class TestCvePenalizationStep(AdviserTestCase):
    """Test scoring (penalization) based on a CVE."""

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

    def test_cve_penalization(self) -> None:
        """Make sure a CVE affects stack score."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records_all").with_args(
            package_name="flask", package_version="0.12.0"
        ).and_return([self._FLASK_CVE]).once()

        package_version = PackageVersion(
            name="flask", version="==0.12.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(graph=GraphDatabase())
        with CvePenalizationStep.assigned_context(context):
            step = CvePenalizationStep()
            result = step.run(None, package_version)

        assert result is not None
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], float)
        assert result[0] == 1 * CvePenalizationStep.CONFIGURATION_DEFAULT["cve_penalization"]
        assert isinstance(result[1], list)
        assert result[1] == [self._FLASK_CVE]

    def test_no_cve_record(self) -> None:
        """Make sure no CVEs do not affect CVE scoring."""
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records_all").with_args(
            package_name="flask", package_version="0.12.0"
        ).and_return([]).once()

        package_version = PackageVersion(
            name="flask", version="==0.12.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock(graph=GraphDatabase())
        with CvePenalizationStep.assigned_context(context):
            step = CvePenalizationStep()
            result = step.run(None, package_version)

        assert result is None
