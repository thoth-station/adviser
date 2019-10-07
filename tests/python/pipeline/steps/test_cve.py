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

"""Test preparing scoring of packages with and without CVEs."""

import operator
import flexmock

from thoth.python import PackageVersion
from thoth.python import Source

from thoth.adviser.python.pipeline.step_context import StepContext
from thoth.adviser.python.pipeline.steps import CvePenalization

from thoth.storages import GraphDatabase

from base import AdviserTestCase


class TestCvePenalization(AdviserTestCase):
    """Test preparing scoring of packages with and without CVEs."""

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

    @staticmethod
    def _get_prepared_step_context() -> StepContext:
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("flask", "0.12.0", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==0.12.0",
                index=source,
                develop=False,
            ),
            ("flask", "0.13.0", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==0.13.0",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("flask", "0.12.0", "https://pypi.org/simple"): [
                (("flask", "0.12.0", "https://pypi.org/simple"), ("click", "2.0", "https://pypi.org/simple")),
                (("click", "2.0", "https://pypi.org/simple"), ("pyyaml", "3.12", "https://pypi.org/simple")),
            ],
            ("flask", "0.13.0", "https://pypi.org/simple"): [
                (("flask", "0.13.0", "https://pypi.org/simple"), ("click", "2.0", "https://pypi.org/simple")),
                (("click", "2.0", "https://pypi.org/simple"), ("pyyaml", "3.12", "https://pypi.org/simple")),
                (("click", "2.0", "https://pypi.org/simple"), ("pyyaml", "4.0", "https://pypi.org/simple")),
            ],
        }

        return StepContext.from_paths(direct_dependencies, paths)

    def test_score_all(self):
        """Make sure a CVE affects stack score."""
        step_context = self._get_prepared_step_context()

        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.12.0"
        ).and_return([self._FLASK_CVE]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.13.0"
        ).and_return([self._FLASK_CVE]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "click", "2.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "3.12"
        ).and_return([self._PYYAML_CVE]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "4.0"
        ).and_return([self._PYYAML_CVE]).ordered()
        cve_scoring = CvePenalization(
            graph=GraphDatabase(),
            project=None,
            library_usage=None,
        )
        cve_scoring.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0),
        ))

        # All paths with Flask and CVE get penalized (all of them).
        assert list(pairs) == [
            (-0.2, (None, ('flask', '0.12.0', 'https://pypi.org/simple'))),
            (-0.2, (None, ('flask', '0.13.0', 'https://pypi.org/simple'))),
            (-0.2, (('click', '2.0', 'https://pypi.org/simple'),
                    ('pyyaml', '3.12', 'https://pypi.org/simple'))),
            (-0.2, (('click', '2.0', 'https://pypi.org/simple'),
                    ('pyyaml', '4.0', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.13.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple')))
        ]

        # All paths with Flask (direct dependency) get equally penalized.
        assert set(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == {
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("flask", "0.13.0", "https://pypi.org/simple"),
        }

    def test_score_some(self):
        """Make sure the more CVEs are found in stack, the bigger penalization is."""
        step_context = self._get_prepared_step_context()

        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.12.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.13.0"
        ).and_return([self._FLASK_CVE]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "click", "2.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "3.12"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "4.0"
        ).and_return([self._PYYAML_CVE]).ordered()
        cve_scoring = CvePenalization(
            graph=GraphDatabase(),
            project=None,
            library_usage=None,
        )
        cve_scoring.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0),
        ))

        # The path with Flask with CVE and with PyYAML with CVE gets penalized more.
        assert pairs == [
            (-0.2, (None, ('flask', '0.13.0', 'https://pypi.org/simple'))),
            (-0.2, (('click', '2.0', 'https://pypi.org/simple'),
                    ('pyyaml', '4.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12.0', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple'))),
            (0.0, (('click', '2.0', 'https://pypi.org/simple'),
                   ('pyyaml', '3.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.13.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple')))
        ]

        assert set(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == {
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("flask", "0.13.0", "https://pypi.org/simple"),
        }

    def test_no_score(self):
        """Make sure no CVEs do not affect CVE scoring."""
        step_context = self._get_prepared_step_context()

        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.12.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.13.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "click", "2.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "3.12"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "4.0"
        ).and_return([]).ordered()
        cve_scoring = CvePenalization(
            graph=GraphDatabase(),
            project=None,
            library_usage=None,
        )
        cve_scoring.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0),
        ))

        # Make sure paths are untouched.
        assert pairs == [
            (0.0, (None, ('flask', '0.12.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.13.0', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple'))),
            (0.0, (('click', '2.0', 'https://pypi.org/simple'),
                   ('pyyaml', '3.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.13.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple'))),
            (0.0, (('click', '2.0', 'https://pypi.org/simple'),
                   ('pyyaml', '4.0', 'https://pypi.org/simple')))
        ]

        assert set(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == {
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("flask", "0.13.0", "https://pypi.org/simple"),
        }

    def test_indirect(self):
        """Make sure sorting is done if an indirect dependency has issue."""
        step_context = self._get_prepared_step_context()

        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.12.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.13.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "click", "2.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "3.12"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "4.0"
        ).and_return([self._PYYAML_CVE]).ordered()
        cve_scoring = CvePenalization(
            graph=GraphDatabase(),
            project=None,
            library_usage=None,
        )
        cve_scoring.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0),
        ))

        assert pairs == [
            (-0.2, (('click', '2.0', 'https://pypi.org/simple'),
                    ('pyyaml', '4.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.13.0', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple'))),
            (0.0, (('click', '2.0', 'https://pypi.org/simple'),
                   ('pyyaml', '3.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.13.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple')))
        ]

        assert set(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == {
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("flask", "0.13.0", "https://pypi.org/simple"),
        }

    def test_direct(self):
        """Make sure direct dependencies are adjusted based on CVEs found."""
        step_context = self._get_prepared_step_context()

        flexmock(GraphDatabase)
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.12.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "flask", "0.13.0"
        ).and_return([self._FLASK_CVE]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "click", "2.0"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "3.12"
        ).and_return([]).ordered()
        GraphDatabase.should_receive("get_python_cve_records").with_args(
            "pyyaml", "4.0"
        ).and_return([]).ordered()
        cve_scoring = CvePenalization(
            graph=GraphDatabase(),
            project=None,
            library_usage=None,
        )
        cve_scoring.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0),
        ))

        assert pairs == [
            (-0.2, (None, ('flask', '0.13.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12.0', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple'))),
            (0.0, (('click', '2.0', 'https://pypi.org/simple'),
                   ('pyyaml', '3.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.13.0', 'https://pypi.org/simple'),
                   ('click', '2.0', 'https://pypi.org/simple'))),
            (0.0, (('click', '2.0', 'https://pypi.org/simple'),
                   ('pyyaml', '4.0', 'https://pypi.org/simple')))
        ]

        assert set(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == {
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("flask", "0.13.0", "https://pypi.org/simple"),
        }
