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

    def test_remove_single22(self):
        """Test removing one single dependency from dependency paths, keep paths with same package of a type.

        In other words - always keep latest toolchain.
        """
        direct_dependencies = {
            ("flask", "0.12", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==0.12",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        }

        paths = {
            ("flask", "0.12", "https://pypi.org/simple"): [
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.15.1", "https://pypi.org/simple")),
                (("werkzeug", "0.15.1", "https://pypi.org/simple"),
                 ("wheel", "1.12.0", "https://pypi.org/simple")),
                (("werkzeug", "0.15.1", "https://pypi.org/simple"),
                 ("six", "1.12.1", "https://pypi.org/simple")),
                (("werkzeug", "0.15.1", "https://pypi.org/simple"),
                 ("wheel", "1.12.1", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_toolchain = CutToolchain(
            graph=None,
            project=None,
            library_usage=None,
        )
        cut_toolchain.run(step_context)

        # We always expect the latest one to be present.
        assert step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs() == [
            (0.0, (None, ('flask', '0.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12', 'https://pypi.org/simple'),
                   ('werkzeug', '0.15.1', 'https://pypi.org/simple'))),
            (0.0, (('werkzeug', '0.15.1', 'https://pypi.org/simple'),
                   ('six', '1.12.1', 'https://pypi.org/simple'))),
            (0.0, (('werkzeug', '0.15.1', 'https://pypi.org/simple'),
                   ('wheel', '1.12.1', 'https://pypi.org/simple')))
        ]

    def test_remove_multi(self):
        """Check all types of "toolchain" packages get removed."""
        direct_dependencies = {
            ("goblinoid", "1.0.0", "https://pypi.org/simple"): PackageVersion(
                name="goblinoid",
                version="==1.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        }

        paths = {
            ("goblinoid", "1.0.0", "https://pypi.org/simple"): [
                (("goblinoid", "1.0.0", "https://pypi.org/simple"),
                 ("wheel", "1.0.0", "https://pypi.org/simple")),
                (("goblinoid", "1.0.0", "https://pypi.org/simple"),
                 ("wheel", "2.0.0", "https://pypi.org/simple")),
                (("goblinoid", "1.0.0", "https://pypi.org/simple"),
                 ("setuptools", "1.0.0", "https://pypi.org/simple")),
                (("goblinoid", "1.0.0", "https://pypi.org/simple"),
                 ("setuptools", "2.0.0", "https://pypi.org/simple")),
                (("goblinoid", "1.0.0", "https://pypi.org/simple"),
                 ("pip", "1.0.0", "https://pypi.org/simple")),
                (("goblinoid", "1.0.0", "https://pypi.org/simple"),
                 ("pip", "2.0.0", "https://pypi.org/simple")),
            ]
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_toolchain = CutToolchain(
            graph=None,
            project=None,
            library_usage=None,
        )
        cut_toolchain.run(step_context)

        assert step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs() == [
            (0.0, (None, ('goblinoid', '1.0.0', 'https://pypi.org/simple'))),
            (0.0, (('goblinoid', '1.0.0', 'https://pypi.org/simple'),
                   ('wheel', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('goblinoid', '1.0.0', 'https://pypi.org/simple'),
                   ('setuptools', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('goblinoid', '1.0.0', 'https://pypi.org/simple'),
                   ('pip', '2.0.0', 'https://pypi.org/simple')))
        ]

    def test_no_remove(self):
        """Make sure packages which are not toolchain do not get removed."""
        direct_dependencies = {
            ("goblinoid", "1.0.0", "https://pypi.org/simple"): PackageVersion(
                name="goblinoid",
                version="==1.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        }

        paths = {
            ("goblinoid", "1.0.0", "https://pypi.org/simple"): [
                (("goblinoid", "1.0.0", "https://pypi.org/simple"),
                 ("foo", "1.0.0", "https://pypi.org/simple")),
            ]
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_toolchain = CutToolchain(
            graph=None,
            project=None,
            library_usage=None,
        )
        cut_toolchain.run(step_context)

        assert step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs() == [
            (0.0, (None, ('goblinoid', '1.0.0', 'https://pypi.org/simple'))),
            (0.0, (('goblinoid', '1.0.0', 'https://pypi.org/simple'),
                   ('foo', '1.0.0', 'https://pypi.org/simple'))),
        ]
