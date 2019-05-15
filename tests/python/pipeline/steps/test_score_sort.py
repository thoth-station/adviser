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

"""Test filtering out packages which have runtime errors."""

from thoth.adviser.python.pipeline.step_context import StepContext
from thoth.adviser.python.pipeline.steps import ScoreSort
from thoth.python import PackageVersion
from thoth.python import Source

from base import AdviserTestCase


class TestScoreSort(AdviserTestCase):
    """Test filtering out packages which have runtime errors."""

    def test_score_sort_direct(self):
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.15.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==0.12",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==0.13.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.score_package_tuple(direct_dependencies[0].to_tuple(), 2.0)
        step_context.score_package_tuple(direct_dependencies[1].to_tuple(), 1.0)
        step_context.score_package_tuple(direct_dependencies[2].to_tuple(), 3.0)

        score_sort = ScoreSort(graph=None, project=None, library_usage=None)
        score_sort.run(step_context)

        assert list(
            step_context.iter_direct_dependencies()
        ) == [direct_dependencies[1], direct_dependencies[0], direct_dependencies[2]]
        assert step_context.raw_paths == []

    def test_score_sort_paths(self):
        paths = [
            [
                ("flask", "0.15.0", "https://pypi.org/simple"),
                ("werkzeug", "2.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.15.0", "https://pypi.org/simple"),
                ("werkzeug", "1.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12", "https://pypi.org/simple"),
                ("werkzeug", "1.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12", "https://pypi.org/simple"),
                ("werkzeug", "2.0.0", "https://pypi.org/simple"),
            ],
        ]
        step_context = StepContext()
        step_context.add_paths(paths)

        step_context.score_package_tuple(paths[0][0], 3.4)  # S1
        step_context.score_package_tuple(paths[1][1], 2.1)  # S2
        step_context.score_package_tuple(paths[2][0], 1.2)  # S3
        step_context.score_package_tuple(paths[3][0], 0.0)  # S4

        score_sort = ScoreSort(graph=None, project=None, library_usage=None)
        score_sort.run(step_context)

        assert list(step_context.iter_paths_with_score()) == [
            (1.2, [  # S3
                ('flask', '0.12', 'https://pypi.org/simple'),
                ('werkzeug', '2.0.0', 'https://pypi.org/simple')]),
            (3.3, [  # S2 + S3
                ('flask', '0.12', 'https://pypi.org/simple'),
                ('werkzeug', '1.0.0', 'https://pypi.org/simple')]),
            (3.4, [  # S1
                ('flask', '0.15.0', 'https://pypi.org/simple'),
                ('werkzeug', '2.0.0', 'https://pypi.org/simple')]),
            (5.5, [  # S1 + S2
                ('flask', '0.15.0', 'https://pypi.org/simple'),
                ('werkzeug', '1.0.0', 'https://pypi.org/simple')])
        ]
        assert list(step_context.iter_direct_dependencies()) == []
