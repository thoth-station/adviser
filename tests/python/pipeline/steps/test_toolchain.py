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

from typing import Tuple
from typing import List

from thoth.adviser.python.pipeline.steps import CutToolchain
from thoth.adviser.python.pipeline.step_context import StepContext

from thoth.python import PackageVersion
from thoth.python import Source

from base import AdviserTestCase


class TestCutToolchain(AdviserTestCase):
    """Test sorting of packages in the dependency graph (paths) based on semantic version."""

    @staticmethod
    def in_any_path(
        package_tuple: Tuple[str, str, str], paths: List[List[Tuple[str, str, str]]]
    ):
        """Check if the given package tuple is present in any path."""
        for path in paths:
            if package_tuple in path:
                return True
        return False

    def test_remove_single22(self):
        """Test removing one single dependency from dependency paths, keep paths with same package of a type.

        In other words - always keep latest toolchain.
        """
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("werkzeug", "0.15.1", "https://pypi.org/simple"),
                    ("wheels", "1.12.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("werkzeug", "0.15.1", "https://pypi.org/simple"),
                    ("six", "1.12.1", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12", "https://pypi.org/simple"),
                    ("werkzeug", "0.15.1", "https://pypi.org/simple"),
                    ("wheels", "1.12.1", "https://pypi.org/simple"),
                ],
            ]
        )
        cut_toolchain = CutToolchain(graph=None, project=None)
        cut_toolchain.run(step_context)

        # We always expect the latest one to be present.
        assert self.in_any_path(
            ("wheels", "1.12.1", "https://pypi.org/simple"), step_context.raw_paths
        )
        assert self.in_any_path(
            ("six", "1.12.1", "https://pypi.org/simple"), step_context.raw_paths
        )

    def test_remove_multi(self):
        """Check all types of "toolchain" packages get removed."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="goblinoid",
                version="==1.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("goblinoid", "1.0.0", "https://pypi.org/simple"),
                    ("wheels", "1.0.0", "https://pypi.org/simple"),
                ],
                [
                    ("goblinoid", "1.0.0", "https://pypi.org/simple"),
                    ("wheels", "2.0.0", "https://pypi.org/simple"),
                ],
                [
                    ("goblinoid", "1.0.0", "https://pypi.org/simple"),
                    ("setuptools", "1.0.0", "https://pypi.org/simple"),
                ],
                [
                    ("goblinoid", "1.0.0", "https://pypi.org/simple"),
                    ("setuptools", "2.0.0", "https://pypi.org/simple"),
                ],
                [
                    ("goblinoid", "1.0.0", "https://pypi.org/simple"),
                    ("pip", "1.0.0", "https://pypi.org/simple"),
                ],
                [
                    ("goblinoid", "1.0.0", "https://pypi.org/simple"),
                    ("pip", "2.0.0", "https://pypi.org/simple"),
                ],
            ]
        )
        cut_toolchain = CutToolchain(graph=None, project=None)
        cut_toolchain.run(step_context)

        assert len(step_context.raw_paths) == 3, "Wrong number of paths removed"
        # We always expect the latest one to be present.
        assert self.in_any_path(
            ("wheels", "2.0.0", "https://pypi.org/simple"), step_context.raw_paths
        )
        assert self.in_any_path(
            ("setuptools", "2.0.0", "https://pypi.org/simple"), step_context.raw_paths
        )
        assert self.in_any_path(
            ("pip", "2.0.0", "https://pypi.org/simple"), step_context.raw_paths
        )

    def test_no_remove(self):
        """Make sure packages which are not toolchain do not get removed."""
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="goblinoid",
                version="==1.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("goblinoid", "1.0.0", "https://pypi.org/simple"),
                    ("foo", "1.0.0", "https://pypi.org/simple"),
                ]
            ]
        )
        cut_toolchain = CutToolchain(graph=None, project=None)
        cut_toolchain.run(step_context)

        assert len(step_context.raw_paths) == 1, "Wrong number of paths removed"
