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

from thoth.adviser.python.pipeline import StepContext
from thoth.adviser.python.pipeline.steps import CutUnreachable

from thoth.python import PackageVersion
from thoth.python import Source

from base import AdviserTestCase


class TestCutUnreachable(AdviserTestCase):
    """Test cutting off unreachable dependencies."""

    def test_remove_single(self):
        """Test removing a single dependency from paths based on locked down direct dependency to a specific version."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("flask", "0.12", source.url): PackageVersion(
                name="flask",
                version="==0.12",
                index=source,
                develop=False,
            ),
            ("flask", "0.12.1", source.url): PackageVersion(
                name="flask",
                version="==0.12.1",
                index=source,
                develop=False,
            ),
            ("six", "1.12.0", source.url): PackageVersion(
                name="six",
                version="==1.12.0",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("flask", "0.12", "https://pypi.org/simple"): [
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("six", "1.11.0", "https://pypi.org/simple")),
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("six", "1.12.0", "https://pypi.org/simple")),
            ],
            ("flask", "0.12.1", "https://pypi.org/simple"): [
                (("flask", "0.12.1", "https://pypi.org/simple"),
                 ("six", "1.12.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_unreachable = CutUnreachable(
            graph=None,
            project=None,
            library_usage=None,
        )
        cut_unreachable.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()

        # Six in version 1.11.0 should be removed.
        assert set(pairs) == {
            (0.0, (None, ('flask', '0.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12', 'https://pypi.org/simple'),
                   ('six', '1.12.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12.1', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12.1', 'https://pypi.org/simple'),
                   ('six', '1.12.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('six', '1.12.0', 'https://pypi.org/simple')))
        }

    def test_no_remove(self):
        """Check there is not removed any dependency if no unreachable cutoff is applicable."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("flask", "0.12", source.url): PackageVersion(
                name="flask",
                version="==0.12",
                index=source,
                develop=False,
            ),
            ("flask", "0.12.1", source.url): PackageVersion(
                name="flask",
                version="==0.12.1",
                index=source,
                develop=False,
            ),
            ("six", "0.12.1", source.url): PackageVersion(
                name="six",
                version="==1.12.1",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("flask", "0.12", "https://pypi.org/simple"): [
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("six", "1.12.0", "https://pypi.org/simple")),
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "2.2.0", "https://pypi.org/simple")),
                (("werkzeug", "2.2.0", "https://pypi.org/simple"),
                 ("six", "1.12.0", "https://pypi.org/simple")),
            ],
            ("flask", "0.12.1", "https://pypi.org/simple"): [],
            ("six", "0.12.1", "https://pypi.org/simple"): [],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_unreachable = CutUnreachable(
            graph=None,
            project=None,
            library_usage=None,
        )

        cut_unreachable.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()

        # flask==0.12 should be removed because of direct dependency six==0.12.1
        assert set(pairs) == {
            (0.0, (None, ('flask', '0.12.1', 'https://pypi.org/simple'))),
            (0.0, (None, ('six', '0.12.1', 'https://pypi.org/simple')))
        }

    def test_remove_multi(self):
        """Test removal of multiple paths based on locked down direct dependencies."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("flask", "0.12", source.url): PackageVersion(
                name="flask",
                version="==0.12",
                index=source,
                develop=False,
            ),
            ("werkzeug", "0.15.1", source.url): PackageVersion(
                name="werkzeug",
                version="==0.15.1",
                index=source,
                develop=False,
            ),
            ("six", "1.12.0", source.url): PackageVersion(
                name="six",
                version="==1.12.0",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("flask", "0.12", "https://pypi.org/simple"): [
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("six", "1.12.0", "https://pypi.org/simple")),
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.13.0", "https://pypi.org/simple")),
                (("werkzeug", "0.13.0", "https://pypi.org/simple"),
                 ("six", "1.12.1", "https://pypi.org/simple")),
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.15.1", "https://pypi.org/simple")),
                (("werkzeug", "0.15.1", "https://pypi.org/simple"),
                 ("six", "1.12.0", "https://pypi.org/simple")),
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.13.0", "https://pypi.org/simple")),
                (("werkzeug", "0.13.0", "https://pypi.org/simple"),
                 ("six", "1.12.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_unreachable = CutUnreachable(
            graph=None,
            project=None,
            library_usage=None,
        )

        cut_unreachable.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()

        # werkzeug and flask are used only in one version based on direct dependencies
        assert set(pairs) == {
            (0.0, (None, ('flask', '0.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12', 'https://pypi.org/simple'),
                   ('six', '1.12.0', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12', 'https://pypi.org/simple'),
                   ('werkzeug', '0.15.1', 'https://pypi.org/simple'))),
            (0.0, (('werkzeug', '0.15.1', 'https://pypi.org/simple'),
                   ('six', '1.12.0', 'https://pypi.org/simple'))),
            (0.0, (None, ('werkzeug', '0.15.1', 'https://pypi.org/simple'))),
            (0.0, (None, ('six', '1.12.0', 'https://pypi.org/simple')))
        }
