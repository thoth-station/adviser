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

"""Test limiting number of latest versions considered for a single package."""

import operator

from thoth.adviser.python.pipeline.steps import LimitLatestVersions
from thoth.adviser.python.pipeline.step_context import StepContext
from thoth.python import PackageVersion
from thoth.python import Source

from base import AdviserTestCase


class TestLimitLatestVersions(AdviserTestCase):
    """Test limiting number of latest versions considered for a single package."""

    def test_limit_direct(self):
        """Test cutting off latest versions for a direct dependency of a type."""
        index_aicoe =Source("https://thoth-station.ninja/simple")

        direct_dependencies = {
            ("tensorflow", "1.9.0", index_aicoe.url): PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=index_aicoe,
                develop=False,
            ),
            ("tensorflow", "2.0.0", index_aicoe.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple"))
            ],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ("numpy", "1.0.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        limit_latest_versions = LimitLatestVersions(
            graph=None,
            project=None,
            library_usage=None
        )
        limit_latest_versions.update_parameters({"limit_latest_versions": 1})
        limit_latest_versions.run(step_context)
        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0)
        ))

        assert pairs == [
            (
                0.0,
                (
                    None,
                    ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ),
            ),
            (
                0.0,
                (
                    ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                    ("numpy", "1.0.0", "https://pypi.org/simple"),
                ),
            )
        ]

        assert list(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == [("tensorflow", "2.0.0", "https://thoth-station.ninja/simple")]

    def test_limit_transitive(self):
        """Test cutting of latest versions for transitive dependencies."""
        direct_dependencies = {
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            )
        }

        paths = {
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ("numpy", "1.0.0", "https://pypi.org/simple")),
            ],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ("numpy", "2.0.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        limit_latest_versions = LimitLatestVersions(
            graph=None,
            project=None,
            library_usage=None,
        )
        limit_latest_versions.update_parameters({"limit_latest_versions": 1})
        limit_latest_versions.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0)
        ))

        assert pairs == [
            (
                0.0,
                (
                    None,
                    ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ),
            ),
            (
                0.0,
                (
                    ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                    ("numpy", "2.0.0", "https://pypi.org/simple"),
                ),
            )
        ]
        assert list(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == [("tensorflow", "2.0.0", "https://thoth-station.ninja/simple")]

    def test_limit_all(self):
        """Test cutting of latest versions for direct and transitive dependencies."""
        source = Source("https://thoth-station.ninja/simple")
        direct_dependencies = {
            ("tensorflow", "1.9.0", source.url): PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=source,
                develop=False,
            ),
            ("tensorflow", "2.0.0", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://thoth-station.ninja/simple"),
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "2.0.0", "https://pypi.org/simple")),
            ],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "2.0.0", "https://pypi.org/simple")),
            ]
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        limit_latest_versions = LimitLatestVersions(
            graph=None,
            project=None,
            library_usage=None,
        )
        limit_latest_versions.update_parameters({"limit_latest_versions": 1})
        limit_latest_versions.run(step_context)

        pairs = list(sorted(
            step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs(),
            key=operator.itemgetter(0)
        ))

        assert pairs == [
            (
                0.0,
                (
                    None,
                    ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                ),
            ),
            (
                0.0,
                (
                    ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                    ("numpy", "2.0.0", "https://pypi.org/simple"),
                ),
            )
        ]
        assert list(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == [("tensorflow", "2.0.0", "https://thoth-station.ninja/simple")]

    def test_limit_no_change(self):
        """Test cutting off latest versions without any change."""
        source = Source("https://thoth-station.ninja/simple")
        direct_dependencies = {
            ("tensorflow", "1.9.0", source.url): PackageVersion(
                name="tensorflow",
                version="==1.9.0",
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
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"): [
                (("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "2.0.0", "https://pypi.org/simple")),
            ],
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"): {
                (("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
                 ("numpy", "2.0.0", "https://pypi.org/simple")),

            }
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        limit_latest_versions = LimitLatestVersions(
            graph=None,
            project=None,
            library_usage=None,
        )
        limit_latest_versions.update_parameters({"limit_latest_versions": 2})
        limit_latest_versions.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()

        assert set(pairs) == {
            (0.0, (None, ('tensorflow', '1.9.0', 'https://thoth-station.ninja/simple'))),
            (0.0, (None, ('tensorflow', '2.0.0', 'https://thoth-station.ninja/simple'))),
            (0.0, (('tensorflow', '1.9.0', 'https://thoth-station.ninja/simple'),
                   ('numpy', '1.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '1.9.0', 'https://thoth-station.ninja/simple'),
                   ('numpy', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://thoth-station.ninja/simple'),
                   ('numpy', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://thoth-station.ninja/simple'),
                   ('numpy', '1.0.0', 'https://pypi.org/simple'))),
        }

        assert set(
            pv.to_tuple() for pv in step_context.iter_direct_dependencies()
        ) == {
            ("tensorflow", "1.9.0", "https://thoth-station.ninja/simple"),
            ("tensorflow", "2.0.0", "https://thoth-station.ninja/simple"),
        }
