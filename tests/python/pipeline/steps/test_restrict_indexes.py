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

"""Test removing packages coming in from a restricted package source index."""

import pytest

from thoth.adviser.python.pipeline import StepContext
from thoth.adviser.python.pipeline.steps import RestrictIndexes
from thoth.adviser.python.pipeline.exceptions import CannotRemovePackage

from thoth.python import PackageVersion
from thoth.python import Source
from thoth.python import Project

from base import AdviserTestCase


class TestRestrictIndexes(AdviserTestCase):
    """Test removing packages coming in from a restricted package source index.

    This step is used only in Dependency Monkey (as of now) and is based on
    removal of indexes which do not correspond to explicit configuration in
    project metadata.
    """

    # Make sure only https://pypi.org/simple is kept.
    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "==2.0.0"
"""

    def test_remove_direct(self):
        """Test removal of direct dependencies which do not correspond to restricted indexes."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                    ("numpy", "1.0.0", "https://pypi.org/simple"),
                ],
                [
                    ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                    ("numpy", "2.0.0", "https://pypi.org/simple"),
                ],
            ]
        )
        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )
        restrict_indexes.run(step_context)

        assert len(step_context.raw_paths) == 2, "Wrong number of paths removed"
        assert (
            len(list(step_context.iter_direct_dependencies())) == 1
        ), "Wrong number of direct dependencies"

    def test_remove_transitive(self):
        """Test removal of indirect dependencies which do not correspond to restricted indexes."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                    ("numpy", "1.0.0", "https://pypi.org/simple"),
                ],
                [
                    ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                    ("numpy", "2.0.0", "https://thoth-station.ninja/simple"),
                ],
            ]
        )
        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )
        restrict_indexes.run(step_context)

        assert len(step_context.raw_paths) == 1, "Wrong number of paths removed"
        assert (
            len(list(step_context.iter_direct_dependencies())) == 2
        ), "Wrong number of direct dependencies"

    def test_remove2(self):
        """Test removal of both, direct and transitive dependencies in one run."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                    ("numpy", "1.0.0", "https://pypi.org/simple"),
                ],
                [
                    ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                    ("numpy", "2.0.0", "https://thoth-station.ninja/simple"),
                ],
                [
                    ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                    ("numpy", "2.0.0", "https://thoth-station.ninja/simple"),
                ],
                [
                    ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                    ("numpy", "1.0.0", "https://pypi.org/simple"),
                ],
            ]
        )
        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )
        restrict_indexes.run(step_context)

        assert len(step_context.raw_paths) == 1, "Wrong number of paths removed"
        assert (
            len(list(step_context.iter_direct_dependencies())) == 1
        ), "Wrong number of direct dependencies"

    def test_remove_all_transitive_error(self):
        """Test raising of an error if all the transitive deps of a type were removed."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                    ("numpy", "1.0.0", "https://thoth-station.ninja/simple"),
                ],
                [
                    ("tensorflow", "2.0.0", "https://pypi.org/simple"),
                    ("numpy", "2.0.0", "https://thoth-station.ninja/simple"),
                ],
            ]
        )
        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )

        with pytest.raises(CannotRemovePackage):
            restrict_indexes.run(step_context)

    def test_remove_all_direct_error(self):
        """Test raising an error if all the direct deps of a type were removed."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
            PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                    ("absl-py", "1.0.0", "https://pypi.org/simple"),
                ]
            ]
        )
        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )

        with pytest.raises(CannotRemovePackage):
            restrict_indexes.run(step_context)
