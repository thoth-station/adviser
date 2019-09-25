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

"""Test reduction of observations on dependency graph."""

from thoth.adviser.python.pipeline.step_context import StepContext
from thoth.adviser.python.pipeline.steps import ObservationReduction
from thoth.python import PackageVersion
from thoth.python import Source

from base import AdviserTestCase


class TestObservationReduction(AdviserTestCase):
    """Test limiting number of latest versions considered for a single package."""

    def test_no_observation_latest(self):
        """Test that we always end up with the latest version possible if no observations are found."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("tensorflow", "2.0.0", source.url): PackageVersion(
                name="tensorflow",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
            ("tensorflow", "1.9.0", source.url): PackageVersion(
                name="tensorflow",
                version="==1.9.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        }

        paths = {
            ("tensorflow", "1.9.0", "https://pypi.org/simple"): [
                (("tensorflow", "1.9.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
                (("tensorflow", "1.9.0", "https://pypi.org/simple"),
                ("numpy", "2.0.0", "https://pypi.org/simple")),
            ],
            ("tensorflow", "2.0.0", "https://pypi.org/simple"): [
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "2.0.0", "https://pypi.org/simple")),
                (("tensorflow", "2.0.0", "https://pypi.org/simple"),
                 ("numpy", "1.0.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths=paths)

        observation_reduction = ObservationReduction(
            graph=None,
            project=None,
            library_usage=None,
        )

        observation_reduction.run(step_context)

        observation_reduced = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()
        assert set(observation_reduced) == {
            (0.0, (None, ('tensorflow', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('tensorflow', '2.0.0', 'https://pypi.org/simple'),
                   ('numpy', '2.0.0', 'https://pypi.org/simple')))
        }

    def test_cyclic(self):
        """Test cyclic dependencies - test we actually break cycles."""
        direct_dependencies = {
            ("a", "2.0.0", "https://pypi.org/simple"): PackageVersion(
                name="a",
                version="==2.0.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        }

        paths = {
            ("a", "2.0.0", "https://pypi.org/simple"): [
                (("a", "2.0.0", "https://pypi.org/simple"),
                 ("b", "2.0.0", "https://pypi.org/simple")),
                (("b", "2.0.0", "https://pypi.org/simple"),
                 ("c", "2.0.0", "https://pypi.org/simple")),
                (("c", "2.0.0", "https://pypi.org/simple"),
                 ("b", "2.0.0", "https://pypi.org/simple")),
                (("a", "2.0.0", "https://pypi.org/simple"),
                 ("b", "1.0.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths=paths)

        observation_reduction = ObservationReduction(
            graph=None,
            project=None,
            library_usage=None,
        )
        observation_reduction.run(step_context)

        observation_reduced = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()
        assert set(observation_reduced) == {
            (0.0, (None, ('a', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('a', '2.0.0', 'https://pypi.org/simple'),
                   ('b', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('b', '2.0.0', 'https://pypi.org/simple'),
                   ('c', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('c', '2.0.0', 'https://pypi.org/simple'),
                   ('b', '2.0.0', 'https://pypi.org/simple')))
        }

    def test_one_observation(self):
        """Test one observation and subsequent correct reduction."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("a", "2.0.0", source.url): PackageVersion(
                name="a",
                version="==2.0.0",
                index=source,
                develop=False,
            ),
            ("a", "1.0.0", source.url): PackageVersion(
                name="a",
                version="==1.0.0",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("a", "2.0.0", "https://pypi.org/simple"): [
                (("a", "2.0.0", "https://pypi.org/simple"),
                 ("b", "2.0.0", "https://pypi.org/simple")),
                (("a", "2.0.0", "https://pypi.org/simple"),
                 ("b", "1.0.0", "https://pypi.org/simple")),
            ],
            ("a", "1.0.0", "https://pypi.org/simple"): [
                (("a", "1.0.0", "https://pypi.org/simple"),
                 ("b", "2.0.0", "https://pypi.org/simple")),
                (("a", "1.0.0", "https://pypi.org/simple"),
                 ("b", "1.0.0", "https://pypi.org/simple")),
            ],
        }
        step_context = StepContext.from_paths(direct_dependencies, paths=paths)

        step_context.score_package_tuple(("a", "1.0.0", "https://pypi.org/simple"), 2.0)

        observation_reduction = ObservationReduction(
            graph=None,
            project=None,
            library_usage=None,
        )
        observation_reduction.run(step_context)

        observation_reduced = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()
        assert set(observation_reduced) == {
            (2.0, (None, ('a', '1.0.0', 'https://pypi.org/simple'))),
            (0.0, (('a', '1.0.0', 'https://pypi.org/simple'),
                   ('b', '2.0.0', 'https://pypi.org/simple'))),
        }

    def test_multiple_observation(self):
        """Test adjustment based on multiple observations.."""
        source = Source("https://pypi.org/simple")
        direct_dependencies = {
            ("a", "2.0.0", source.url): PackageVersion(
                name="a",
                version="==2.0.0",
                index=source,
                develop=False,
            ),
            ("a", "3.0.0", source.url): PackageVersion(
                name="a",
                version="==3.0.0",
                index=source,
                develop=False,
            ),
            ("a", "1.0.0", source.url): PackageVersion(
                name="a",
                version="==1.0.0",
                index=source,
                develop=False,
            ),
        }

        from itertools import product
        paths_long = list(product(
            (
                ("a", "3.0.0", "https://pypi.org/simple"),
                ("a", "2.0.0", "https://pypi.org/simple"),
                ("a", "1.0.0", "https://pypi.org/simple"),
            ),
            (
                ("b", "3.0.0", "https://pypi.org/simple"),
                ("b", "2.0.0", "https://pypi.org/simple"),
                ("b", "1.0.0", "https://pypi.org/simple"),
            ),
            (
                ("c", "3.0.0", "https://pypi.org/simple"),
                ("c", "2.0.0", "https://pypi.org/simple"),
                ("c", "1.0.0", "https://pypi.org/simple"),
            ),
        ))
        paths = {}
        for item in paths_long:
            if item[0] not in paths:
                paths[item[0]] = []

            for idx in range(len(item) - 1):
                paths[item[0]].append((item[idx], item[idx + 1]))

        step_context = StepContext.from_paths(direct_dependencies, paths=paths)

        #       Possibly resolved  |   Score     |  A    B    C   |
        # =========================|=============|================|========================================
        # A1    a==1, b==1, c==1   |    -1.0     |  -             | Removed - no positive observations.
        # A2    a==1, b==1, c==2   |    -0.5     |  -         +   | Kept because of c.
        # A3    a==1, b==1, c==3   |    -1.0     |  -             | Removed - no positive observations.
        # A4    a==1, b==2, c==1   |     1.0     |  -    +        | Removed - c==2 is better.
        # A5    a==1, b==2, c==2   |     1.5     |  -    +    +   | Kept because of b and c.
        # A6    a==1, b==2, c==3   |     1.0     |  -    +        | Removed because c==2 is better.
        # A7    a==1, b==3, c==1   |    -1.0     |  -             | Removed - no positive observations.
        # A8    a==1, b==3, c==2   |    -0.5     |  -         +   | Kept because of c.
        # A9    a==1, b==3, c==3   |    -1.0     |  -             | Removed - c==2 is better.
        #
        # B1    a==2, b==1, c==1   |             |                | See A1.
        # B2    a==2, b==1, c==2   |     0.5     |            +   | See A2.
        # B3    a==2, b==1, c==3   |             |                | See A3.
        # B4    a==2, b==2, c==1   |     2.0     |       +        | See A4.
        # B5    a==2, b==2, c==2   |     2.5     |       +    +   | See A5.
        # B6    a==2, b==2, c==3   |     2.0     |       +        | See A6.
        # B7    a==2, b==3, c==1   |             |                | See A7.
        # B8    a==2, b==3, c==2   |     0.5     |            +   | See A8.
        # B9    a==2, b==3, c==3   |             |                | See A9.
        #
        # C1    a==3, b==1, c==1   |             |  +             | See B1.
        # C2    a==3, b==1, c==2   |     0.5     |  +         +   | See B2.
        # C3    a==3, b==1, c==3   |             |  +             | See B3.
        # C4    a==3, b==2, c==1   |     2.0     |  +    +        | See B4.
        # C5    a==3, b==2, c==2   |     2.5     |  +    +    +   | See B5.
        # C6    a==3, b==2, c==3   |     2.0     |  +    +        | See B6.
        # C7    a==3, b==3, c==1   |             |  +             | See B7.
        # C8    a==3, b==3, c==2   |     0.5     |  +         +   | See B8.
        # C9    a==3, b==3, c==3   |             |  +             | See B9.
        #
        #
        # Note sub-graphs are shared so B1-9 and C1-9 share reasoning with A1-9.
        #

        step_context.score_package_tuple(("a", "1.0.0", "https://pypi.org/simple"), -1.0)
        step_context.score_package_tuple(("a", "3.0.0", "https://pypi.org/simple"), 5.0)
        step_context.score_package_tuple(("b", "2.0.0", "https://pypi.org/simple"), 2.0)
        step_context.score_package_tuple(("c", "2.0.0", "https://pypi.org/simple"), 0.5)

        observation_reduction = ObservationReduction(
            graph=None,
            project=None,
            library_usage=None,
        )
        observation_reduction.run(step_context)

        observation_reduced = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()
        assert set(observation_reduced) == {
            (-1.0, (None, ('a', '1.0.0', 'https://pypi.org/simple'))),
            (0.0, (('a', '1.0.0', 'https://pypi.org/simple'),
                   ('b', '1.0.0', 'https://pypi.org/simple'))),
            (2.0, (('a', '1.0.0', 'https://pypi.org/simple'),
                   ('b', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('a', '1.0.0', 'https://pypi.org/simple'),
                   ('b', '3.0.0', 'https://pypi.org/simple'))),

            (0.0, (None, ('a', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('a', '2.0.0', 'https://pypi.org/simple'),
                   ('b', '1.0.0', 'https://pypi.org/simple'))),
            (2.0, (('a', '2.0.0', 'https://pypi.org/simple'),
                   ('b', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('a', '2.0.0', 'https://pypi.org/simple'),
                   ('b', '3.0.0', 'https://pypi.org/simple'))),

            (5.0, (None, ('a', '3.0.0', 'https://pypi.org/simple'))),
            (0.0, (('a', '3.0.0', 'https://pypi.org/simple'),
                   ('b', '3.0.0', 'https://pypi.org/simple'))),
            (2.0, (('a', '3.0.0', 'https://pypi.org/simple'),
                   ('b', '2.0.0', 'https://pypi.org/simple'))),
            (0.0, (('a', '3.0.0', 'https://pypi.org/simple'),
                   ('b', '1.0.0', 'https://pypi.org/simple'))),

            (0.5, (('b', '2.0.0', 'https://pypi.org/simple'),
                   ('c', '2.0.0', 'https://pypi.org/simple'))),
            (0.5, (('b', '3.0.0', 'https://pypi.org/simple'),
                   ('c', '2.0.0', 'https://pypi.org/simple'))),
            (0.5, (('b', '1.0.0', 'https://pypi.org/simple'),
                   ('c', '2.0.0', 'https://pypi.org/simple'))),
        }
