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

"""Test cutting off pre-releases based on pre-release configuration."""

import pytest

from thoth.python import PackageVersion
from thoth.python import Source
from thoth.python import Project

from thoth.adviser.python.pipeline.step_context import StepContext
from thoth.adviser.python.pipeline.steps import CutPreReleases
from thoth.adviser.python.dependency_graph import CannotRemovePackage

from base import AdviserTestCase


class TestCutPreReleases(AdviserTestCase):
    """Test cutting off pre-releases based on pre-release configuration."""

    # Make sure only https://pypi.org/simple is kept.
    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"

[pipenv]
allow_prereleases = false
"""

    def test_remove_direct(self):
        """Test removal of direct dependencies which is not a pre-release."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("tensorflow", "2.0.0rc1", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0rc1",
                index=source,
                develop=False,
            ),
            ("tensorflow", "2.0.0", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=source,
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
        restrict_indexes = CutPreReleases(
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

    def test_remove_transitive(self):
        """Test removal of indirect dependencies which is not a pre-release."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("tensorflow", "2.0.0", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0rc1", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "2.0.0", "https://thoth-station.ninja/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = CutPreReleases(
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
                   ('numpy', '2.0.0', 'https://thoth-station.ninja/simple'))),
        ]
        assert set(step_context.iter_direct_dependencies_tuple()) == {
            ('tensorflow', '2.0.0', 'https://pypi.org/simple'),
        }

    def test_remove(self):
        """Test removal of both, direct and transitive dependencies in one run."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("tensorflow", "2.0.0", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=source,
                develop=False,
            ),
            ("tensorflow", "2.0.0rc1", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0rc1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0rc1", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0-rc1", "https://pypi.org/simple")),
            ]
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = CutPreReleases(
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
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("tensorflow", "2.0.0", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=source,
                develop=False,
            )
        }

        paths = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0rc1", "https://thoth-station.ninja/simple")),
            ]
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = CutPreReleases(
            graph=None,
            project=project,
            library_usage=None,
        )

        with pytest.raises(CannotRemovePackage):
            restrict_indexes.run(step_context)

    def test_remove_all_direct_error(self):
        """Test raising an error if all the direct deps of a type were removed."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("tensorflow", "2.0.0", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=source,
                develop=False,
            ),
            ("numpy", "1.0.0rc1", source.url): PackageVersion(
                name="numpy",
                version="==1.0.0rc1",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("absl-py", "1.0.0", "https://pypi.org/simple")),
            ]
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        project = Project.from_strings(self._CASE_PIPFILE)
        restrict_indexes = CutPreReleases(
            graph=None,
            project=project,
            library_usage=None,
        )

        with pytest.raises(CannotRemovePackage):
            restrict_indexes.run(step_context)
