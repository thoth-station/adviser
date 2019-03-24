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

"""Test cutting off unreachable dependencies."""

import pytest

from thoth.adviser.python.pipeline import StepContext
from thoth.adviser.python.pipeline.steps import CutUnreachable
from thoth.adviser.python.pipeline.exceptions import CannotRemovePackage

from thoth.python import PackageVersion
from thoth.python import Source

from base import AdviserTestCase


class TestCutUnreachable(AdviserTestCase):
    """Test cutting off unreachable dependencies."""

    def test_remove_single(self):
        """Test removing a single dependency from paths based on locked down direct dependency to a specific version."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==0.12.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="six",
                version="==1.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("six", "1.12.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("six", "1.11.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12.1", "https://pypi.org/simple"),
                    ("six", "1.12.0", "https://pypi.org/simple"),
                ],
            ]
        )

        cut_unreachable = CutUnreachable(graph=None, project=None)
        cut_unreachable.run(step_context)

        assert (
            len(step_context.raw_paths) == 2
        ), "Unreachable dependency was not removed"
        for path in step_context.raw_paths:
            assert (
                "six",
                "1.12.0",
                "https://pypi.org/simple",
            ) in path, "Removed wrong path"
        assert (
            len(list(step_context.iter_direct_dependencies())) == 3
        ), "Removed direct dependency which should not be removed"

    def test_no_remove(self):
        """Check there is not removed any dependency if no unreachable cutoff is applicable."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="flask",
                version="==0.12.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="six",
                version="==1.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("six", "1.12.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("werkzeug", "2.2.0", "https://pypi.org/simple"),
                    ("six", "1.12.0", "https://pypi.org/simple"),
                ],
            ]
        )
        cut_unreachable = CutUnreachable(graph=None, project=None)

        cut_unreachable.run(step_context)

        assert (
            len(step_context.raw_paths) == 2
        ), "Removed path which should not be removed"
        assert (
            len(list(step_context.iter_direct_dependencies())) == 3
        ), "Removed direct dependency which should not be removed"

    def test_remove_multi(self):
        """Test removal of multiple paths based on locked down direct dependencies."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="werkzeug",
                version="==0.15.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="six",
                version="==1.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("six", "1.12.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("werkzeug", "0.13.0", "https://pypi.org/simple"),
                    ("six", "1.12.1", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("werkzeug", "0.15.1", "https://pypi.org/simple"),
                    ("six", "1.12.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("werkzeug", "0.13.0", "https://pypi.org/simple"),
                    ("six", "1.12.0", "https://pypi.org/simple"),
                ],
            ]
        )
        cut_unreachable = CutUnreachable(graph=None, project=None)

        cut_unreachable.run(step_context)

        assert (
            len(step_context.raw_paths) == 2
        ), "Not all paths were removed based on cut-off"
        assert (
            len(list(step_context.iter_direct_dependencies())) == 3
        ), "Removed direct dependency which should not be removed"

    def test_cutoff_error(self):
        """Mark error when cutting off dependency which is required by dependency graph."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            PackageVersion(
                name="werkzeug",
                version="==0.15.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("six", "1.12.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("werkzeug", "0.15.1", "https://pypi.org/simple"),
                    ("six", "1.12.1", "https://pypi.org/simple"),
                ],
            ]
        )
        cut_unreachable = CutUnreachable(graph=None, project=None)
        cut_unreachable.run(step_context)
