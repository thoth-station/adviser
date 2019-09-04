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

"""Cut off unsolved packages from dependency graph."""

import pytest

from thoth.adviser.python.dependency_graph import CannotRemovePackage
from thoth.adviser.python.pipeline import StepContext
from thoth.adviser.python.pipeline.steps import CutUnsolved

from thoth.python import PackageVersion
from thoth.python import Source

from base import AdviserTestCase


class TestCutUnsolved(AdviserTestCase):
    """Test cutting off unsolved packages from dependency graph."""

    def test_cut_unsolved_noop(self):
        """Test cutting unsolved leads to noop if no unsolvable is present."""
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
        }

        paths = {
            ("flask", "0.12", "https://pypi.org/simple"): [
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.14", "https://pypi.org/simple")),
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.15.5", "https://pypi.org/simple")),
            ],
            ("flask", "0.12.1", "https://pypi.org/simple"): [
                (("flask", "0.12.1", "https://pypi.org/simple"),
                 ("werkzeug", "0.15.5", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_unsolved = CutUnsolved(
            graph=None,
            project=None,
            library_usage=None,
        )
        cut_unsolved.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()
        assert set(pairs) == {
            (0.0, (('flask', '0.12', 'https://pypi.org/simple'), ('werkzeug', '0.15.5', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12.1', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12.1', 'https://pypi.org/simple'), ('werkzeug', '0.15.5', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12', 'https://pypi.org/simple'), ('werkzeug', '0.14', 'https://pypi.org/simple'))),
        }

    def test_cut_unsolved_error(self):
        """Test error cutting if dependency graph cannot be constructed."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("flask", "0.12.1", source.url): PackageVersion(
                name="flask",
                version="==0.12.1",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("flask", "0.12.1", "https://pypi.org/simple"): [
                (("flask", "0.12.1", "https://pypi.org/simple"),
                 ("werkzeug", "0.15.5", None)),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_unsolved = CutUnsolved(
            graph=None,
            project=None,
            library_usage=None,
        )

        with pytest.raises(CannotRemovePackage):
            cut_unsolved.run(step_context)

    def test_cut_unsolved(self):
        """Test cutting unsolved dependency from dependency graph."""
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
        }

        paths = {
            ("flask", "0.12", "https://pypi.org/simple"): [
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.14", None)),
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.15.5", "https://pypi.org/simple")),
            ],
            ("flask", "0.12.1", "https://pypi.org/simple"): [
                (("flask", "0.12.1", "https://pypi.org/simple"),
                 ("werkzeug", "0.15.5", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_unsolved = CutUnsolved(
            graph=None,
            project=None,
            library_usage=None,
        )
        cut_unsolved.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()
        assert set(pairs) == {
            (0.0, (('flask', '0.12', 'https://pypi.org/simple'), ('werkzeug', '0.15.5', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12.1', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12', 'https://pypi.org/simple'))),
            (0.0, (('flask', '0.12.1', 'https://pypi.org/simple'), ('werkzeug', '0.15.5', 'https://pypi.org/simple'))),
        }

    def test_cut_unsolved_multi(self):
        """Test cutting off multiple unsolved dependencies from dependency graph."""
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
        }

        paths = {
            ("flask", "0.12", "https://pypi.org/simple"): [
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.14", None)),
                (("flask", "0.12", "https://pypi.org/simple"),
                 ("werkzeug", "0.15.5", "https://pypi.org/simple")),
            ],
            ("flask", "0.12.1", "https://pypi.org/simple"): [
                (("flask", "0.12.1", "https://pypi.org/simple"),
                 ("werkzeug", None, None)),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        cut_unsolved = CutUnsolved(
            graph=None,
            project=None,
            library_usage=None,
        )
        cut_unsolved.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()
        assert set(pairs) == {
            (0.0, (('flask', '0.12', 'https://pypi.org/simple'), ('werkzeug', '0.15.5', 'https://pypi.org/simple'))),
            (0.0, (None, ('flask', '0.12', 'https://pypi.org/simple'))),
        }
