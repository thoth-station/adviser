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

"""Test adjustment of paths based on performance score."""

import operator
from typing import List
from typing import Tuple

import flexmock

from thoth.adviser.python.pipeline import StepContext
from thoth.common import RuntimeEnvironment
from thoth.adviser.python.pipeline.steps import PerformanceAdjustment
from thoth.adviser.isis import Isis

from thoth.python import PackageVersion
from thoth.python import Source
from thoth.python import Project
from thoth.storages import GraphDatabase

from base import AdviserTestCase


class TestPerformanceAdjustment(AdviserTestCase):
    """Test adjustment of paths based on performance score."""

    @staticmethod
    def _prepare_isis_and_graph(
        package_tuples: List[Tuple[str, str, str]],
        performance_impact: dict,
        avg_performance: float,
    ) -> Project:
        """Mock responses for Isis and GraphDatabase, return mocked project used in steps."""
        flexmock(Isis)
        Isis.should_receive("get_python_package_performance_impact_all").with_args(
            package_tuples,
        ).and_return(performance_impact)

        project = flexmock(
            name="project", runtime_environment=RuntimeEnvironment.from_dict({})
        )
        performance_args = set(
            package_tuple
            for package_tuple, score in performance_impact.items()
            if score > 0
        )

        flexmock(GraphDatabase)
        GraphDatabase.should_receive(
            "compute_python_package_version_avg_performance"
        ).with_args(
            performance_args,
            run_software_environment=project.runtime_environment.to_dict(without_none=True),
            hardware_specs=None,
        ).and_return(
            avg_performance
        )

        return project

    def test_direct_adjusted(self):
        """Test adjustment of direct dependencies on good perf score."""
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==0.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]

        paths = [
            [("flask", "0.12.0", "https://pypi.org/simple")],
            [
                ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                ("numpy", "2.0.0", "https://pypi.org/simple"),
            ],
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths)

        performance_impact = {
            ("flask", "0.12.0", "https://pypi.org/simple"): 1.0,
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): 0.0,
            ("numpy", "2.0.0", "https://pypi.org/simple"): 0,
        }
        project = self._prepare_isis_and_graph(
            list(performance_impact.keys()), performance_impact, 2.0
        )

        performance_adjustment = PerformanceAdjustment(
            graph=GraphDatabase(),
            project=project,
            library_usage=None,
        )
        performance_adjustment.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0)
        ))

        assert pairs == [
            (0.0, (None, ('tensorflow', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '2.0.0', 'https://pypi.org/simple'))),
            (2.0, (None, ('flask', '0.12.0', 'https://pypi.org/simple')))
        ]

        # Make sure Flask gets precedence in resolution.
        assert list(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == [
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("tensorflow", "2.0.0", "https://pypi.org/simple"),
        ]

    def test_transitive_adjusted(self):
        """Make sure transitive dependencies are adjusted, without affecting direct dependencies."""
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==0.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]

        paths = [
            [("flask", "0.12.0", "https://pypi.org/simple")],
            [
                ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                ("numpy", "2.0.0", "https://pypi.org/simple"),
            ],
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths)

        performance_impact = {
            ("flask", "0.12.0", "https://pypi.org/simple"): 1.0,
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): 1.0,
            ("numpy", "2.0.0", "https://pypi.org/simple"): 0,
        }
        project = self._prepare_isis_and_graph(
            list(performance_impact.keys()), performance_impact, 3.0
        )

        performance_adjustment = PerformanceAdjustment(
            graph=GraphDatabase(),
            project=project,
            library_usage=None,
        )
        performance_adjustment.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0)
        ))

        # The order should be fixed - without any change, but scores should be adjusted.
        assert pairs == [
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '2.0.0', 'https://pypi.org/simple'))),
            (3.0, (None, ('flask', '0.12.0', 'https://pypi.org/simple'))),
            (3.0, (None, ('tensorflow', '2.0.0', 'https://pypi.org/simple')))
        ]

        assert list(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == [
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("tensorflow", "2.0.0", "https://pypi.org/simple"),
        ]

    def test_adjusted(self):
        """Test adjustment of direct and indirect dependencies on good perf score."""
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==0.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]

        paths = [
            [("flask", "0.12.0", "https://pypi.org/simple")],
            [
                ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                ("numpy", "2.0.0", "https://pypi.org/simple"),
            ],
        ]

        performance_impact = {
            ("flask", "0.12.0", "https://pypi.org/simple"): 0,
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): 1.0,
            ("numpy", "2.0.0", "https://pypi.org/simple"): 0,
        }
        project = self._prepare_isis_and_graph(
            list(performance_impact.keys()), performance_impact, 2.0
        )

        step_context = StepContext.from_paths(direct_dependencies, paths)

        performance_adjustment = PerformanceAdjustment(
            graph=GraphDatabase(),
            project=project,
            library_usage=None,
        )
        performance_adjustment.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()

        assert pairs == [
            (0.0, (None, ('flask', '0.12.0', 'https://pypi.org/simple'))),
            (2.0, (None, ('tensorflow', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '2.0.0', 'https://pypi.org/simple')))
        ]

        # Make sure TF gets precedence in resolution.
        assert list(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == [
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("tensorflow", "2.0.0", "https://pypi.org/simple"),
        ]

    def test_no_adjusted(self):
        """Test no adjustment if there is not performance impact."""
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==0.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]

        paths = [
            [("flask", "0.12.0", "https://pypi.org/simple")],
            [
                ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                ("numpy", "2.0.0", "https://pypi.org/simple"),
            ],
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths)

        performance_impact = {
            ("flask", "0.12.0", "https://pypi.org/simple"): 0,
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): 0.0,
            ("numpy", "2.0.0", "https://pypi.org/simple"): 0,
        }
        project = self._prepare_isis_and_graph(
            list(performance_impact.keys()), performance_impact, 2.0
        )

        performance_adjustment = PerformanceAdjustment(
            graph=GraphDatabase(),
            project=project,
            library_usage=None,
        )
        performance_adjustment.run(step_context)

        assert step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs() == [
            (0.0, (None, ('flask', '0.12.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('tensorflow', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '2.0.0', 'https://pypi.org/simple')))
        ]

        assert list(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == [
            ("flask", "0.12.0", "https://pypi.org/simple"),
            ("tensorflow", "2.0.0", "https://pypi.org/simple"),
        ]
