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

"""Test sorting of packages in the dependency graph (paths) based on semantic version."""

from thoth.adviser.python.pipeline import StepContext
from thoth.adviser.python.pipeline.steps import SemverSort

from thoth.python import PackageVersion
from thoth.python import Source


from base import AdviserTestCase


class TestSemverSort(AdviserTestCase):
    """Test sorting of packages in the dependency graph (paths) based on semantic version."""

    def test_semver_sort(self):
        """Test sorting based on semantic version."""
        # TODO: implement
        return
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
            [
                ("flask", "0.13.0", "https://pypi.org/simple"),
                ("werkzeug", "2.0.0", "https://pypi.org/simple"),
                ("six", "1.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.13.0", "https://pypi.org/simple"),
                ("werkzeug", "2.0.0", "https://pypi.org/simple"),
                ("six", "1.0.1", "https://pypi.org/simple"),
            ],
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths)

        semver_sort = SemverSort(
            project=None,
            graph=None,
            library_usage=None,
        )
        semver_sort.run(step_context)

        assert step_context.raw_paths == [
            [
                ("flask", "0.12", "https://pypi.org/simple"),
                ("werkzeug", "1.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12", "https://pypi.org/simple"),
                ("werkzeug", "2.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.13.0", "https://pypi.org/simple"),
                ("werkzeug", "2.0.0", "https://pypi.org/simple"),
                ("six", "1.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.13.0", "https://pypi.org/simple"),
                ("werkzeug", "2.0.0", "https://pypi.org/simple"),
                ("six", "1.0.1", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.15.0", "https://pypi.org/simple"),
                ("werkzeug", "1.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.15.0", "https://pypi.org/simple"),
                ("werkzeug", "2.0.0", "https://pypi.org/simple"),
            ],
        ], "Wrong order of transitive paths"

        assert list(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == [
            ("flask", "0.12", "https://pypi.org/simple"),
            ("flask", "0.13.0", "https://pypi.org/simple"),
            ("flask", "0.15.0", "https://pypi.org/simple"),
        ], "Wrong order of direct dependencies"
