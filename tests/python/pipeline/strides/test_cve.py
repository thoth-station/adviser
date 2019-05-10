#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

from thoth.adviser.python.pipeline import StrideContext
from thoth.adviser.python.pipeline.strides import CveScoring
from thoth.storages import GraphDatabase

from base import AdviserTestCase


class TestCveScoring(AdviserTestCase):
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

    _PYYAML_CVE = {
        "advisory": "In PyYAML before 4.1, the yaml.load() API could execute arbitrary code. In other words, "
        "yaml.safe_load is not used.",
        "cve_name": "CVE-2017-18342",
        "version_range": "<4.1,>3.05",
        "cve_id": "CVE-2017-18342",
    }

    def test_score_single(self):
        """Make sure a CVE affects stack score."""
        stride_context = StrideContext(self._CASE_CANDIDATES)
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.12.0"
        ).and_return([self._FLASK_CVE]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "click", "2.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "3.12"
        ).and_return([]).ordered()
        cve_scoring = CveScoring(
            graph=GraphDatabase(),
            project=None,
            library_usage=None,
        )
        cve_scoring.run(stride_context)
        assert (
            stride_context.score
            == 1 * CveScoring.PARAMETERS_DEFAULT["cve_penalization"]
        )
        assert self._FLASK_CVE in stride_context.justification

    def test_score_multi(self):
        """Make sure the more CVEs are found in stack, the bigger penalization is."""
        stride_context = StrideContext(self._CASE_CANDIDATES)
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.12.0"
        ).and_return([self._FLASK_CVE]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "click", "2.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "3.12"
        ).and_return([self._PYYAML_CVE]).ordered()
        cve_scoring = CveScoring(
            graph=GraphDatabase(),
            project=None,
            library_usage=None,
        )
        cve_scoring.run(stride_context)
        assert (
            stride_context.score
            == 2 * CveScoring.PARAMETERS_DEFAULT["cve_penalization"]
        )
        assert self._FLASK_CVE in stride_context.justification
        assert self._PYYAML_CVE in stride_context.justification

    def test_no_score(self):
        """Make sure no CVEs do not affect CVE scoring."""
        stride_context = StrideContext(self._CASE_CANDIDATES)
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.12.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "click", "2.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "3.12"
        ).and_return([]).ordered()
        cve_scoring = CveScoring(
            graph=GraphDatabase(),
            project=None,
            library_usage=None,
        )
        cve_scoring.run(stride_context)
        assert (
            stride_context.score
            == 0 * CveScoring.PARAMETERS_DEFAULT["cve_penalization"]
        )
