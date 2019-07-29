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
from thoth.adviser.python.dependency_graph import CannotRemovePackage

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
        direct_dependencies = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "2.0.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )
        restrict_indexes.run(step_context)

        assert step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs() == [
            (0.0, (None, ('tensorflow', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '1.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '2.0.0', 'https://pypi.org/simple')))
        ]
        assert (
                len(list(step_context.iter_direct_dependencies())) == 1
        ), "Wrong number of direct dependencies"
        assert list(step_context.iter_direct_dependencies_tuple()) == [
            ('tensorflow', '2.0.0', 'https://pypi.org/simple')
        ]

    def test_remove_transitive(self):
        """Test removal of indirect dependencies which do not correspond to restricted indexes."""
        direct_dependencies = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "2.0.0", "https://thoth-station.ninja/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )
        restrict_indexes.run(step_context)

        assert step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs() == [
            (0.0, (None, ('tensorflow', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '1.0.0', 'https://pypi.org/simple'))),
        ]
        assert (
            len(list(step_context.iter_direct_dependencies())) == 1
        ), "Wrong number of direct dependencies"
        assert list(step_context.iter_direct_dependencies_tuple()) == [
            ('tensorflow', '2.0.0', 'https://pypi.org/simple')
        ]

    def test_remove2(self):
        """Test removal of both, direct and transitive dependencies in one run."""
        direct_dependencies = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "2.0.0", "https://thoth-station.ninja/simple")),
            ],
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "2.0.0", "https://thoth-station.ninja/simple")),
                (("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )
        restrict_indexes.run(step_context)

        assert step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs() == [
            (0.0, (None, ('tensorflow', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '1.0.0', 'https://pypi.org/simple')))
        ]
        assert (
            len(list(step_context.iter_direct_dependencies())) == 1
        ), "Wrong number of direct dependencies"

    def test_remove_all_transitive_error(self):
        """Test raising of an error if all the transitive deps of a type were removed."""
        direct_dependencies = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        }

        paths = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://thoth-station.ninja/simple")),
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "2.0.0", "https://thoth-station.ninja/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

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
        direct_dependencies = {
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                 ("absl-py", "1.0.0", "https://pypi.org/simple")),
            ]
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = RestrictIndexes(
            graph=None,
            project=project,
            library_usage=None,
        )

        with pytest.raises(CannotRemovePackage):
            restrict_indexes.run(step_context)
