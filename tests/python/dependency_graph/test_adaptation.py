#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019 Fridolin Pokorny
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

"""Test adjustment and package removals on dependency graph used for adjustments."""

import operator
import pytest

from base import AdviserTestCase

from thoth.adviser.python.dependency_graph import DependencyGraphAdaptation
from thoth.adviser.python.dependency_graph import CannotRemovePackage


class TestDependencyGraphAdaptation(AdviserTestCase):
    def test_empty(self):
        with pytest.raises(ValueError):
            DependencyGraphAdaptation.from_paths([], [])

    def test_empty_paths(self):
        direct_dependencies = [
            ("selinon", "1.0.0", "https://pypi.org/simple")
        ]
        dg = DependencyGraphAdaptation.from_paths(direct_dependencies, [])
        pairs = dg.to_scored_package_tuple_pairs()
        assert pairs == [(0.0, (None, ('selinon', '1.0.0', 'https://pypi.org/simple')))]

    def test_score_one(self):
        package_tuple = ("daiquiri", "1.5.0", "https://pypi.org/simple")
        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple],
            paths=[],
        )

        dg.score_package_tuple(package_tuple, 2.0)
        dg.score_package_tuple(package_tuple, 1.0)

        pairs = dg.to_scored_package_tuple_pairs()

        assert pairs == [
            (3.0, (None, package_tuple))
        ]

    def test_score_multiple_one_path(self):
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")

        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple1],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
            ]
        )

        dg.score_package_tuple(package_tuple1, 2.0)
        dg.score_package_tuple(package_tuple2, 1.0)

        pairs = list(sorted(dg.to_scored_package_tuple_pairs(), key=operator.itemgetter(0)))
        pairs_expected = [
            (0.0, (package_tuple2, package_tuple3)),
            (1.0, (package_tuple1, package_tuple2)),
            (2.0, (None, package_tuple1)),
        ]

        assert pairs == pairs_expected

    def test_score_multiple_paths(self):
        package_tuple0 = ("daiquiri", "1.5.0", "https://pypi.org/simple")
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")
        package_tuple4 = ("click", "0.2.0", "https://pypi.org/simple")
        package_tuple5 = ("werkzeug", "0.16.0", "https://pypi.org/simple")

        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[
                package_tuple0,
                package_tuple1,
            ],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple4),
                (package_tuple1, package_tuple5),
                (package_tuple5, package_tuple4),
                (package_tuple1, package_tuple5),
                (package_tuple5, package_tuple3),
            ]
        )

        dg.score_package_tuple(package_tuple1, +2.0)
        dg.score_package_tuple(package_tuple2, +1.0)
        dg.score_package_tuple(package_tuple5, -1.0)
        dg.score_package_tuple(package_tuple4, -3.0)
        dg.score_package_tuple(package_tuple5, -1.0)

        pairs = list(sorted(dg.to_scored_package_tuple_pairs(), key=operator.itemgetter(0)))
        pairs_expected = [
            (-3.0, (package_tuple2, package_tuple4)),
            (-3.0, (package_tuple5, package_tuple4)),
            (-2.0, (package_tuple1, package_tuple5)),
            (0.0, (None, package_tuple0)),
            (0.0, (package_tuple2, package_tuple3)),
            (0.0, (package_tuple5, package_tuple3)),
            (1.0, (package_tuple1, package_tuple2)),
            (2.0, (None, package_tuple1))
        ]

        assert pairs == pairs_expected

    def test_score_cyclic(self):
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")
        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple1],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
                (package_tuple3, package_tuple1),
            ]
        )

        dg.score_package_tuple(package_tuple1, 2.0)
        dg.score_package_tuple(package_tuple2, 1.0)

        pairs = list(sorted(dg.to_scored_package_tuple_pairs(), key=operator.itemgetter(0)))
        pairs_expected = [
            (0.0, (package_tuple2, package_tuple3)),
            (1.0, (package_tuple1, package_tuple2)),
            (2.0, (None, package_tuple1)),
            (2.0, (package_tuple3, package_tuple1)),
        ]

        assert pairs == pairs_expected

    def test_remove_direct_one(self):
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("flask", "0.12.0", "https://pypi.org/simple")
        package_tuple3 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple1, package_tuple2],
            paths=[
                (package_tuple1, package_tuple3),
                (package_tuple2, package_tuple3),
        ])

        with dg.remove_package_tuples(package_tuple1) as txn:
            txn.commit()

        pairs = dg.to_scored_package_tuple_pairs()
        pairs_expected = [
            (0.0, (None, package_tuple2)),
            (0.0, (package_tuple2, package_tuple3)),
        ]

        assert pairs == pairs_expected

    def test_remove_direct_one_error(self):
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple1],
            paths=[
                (package_tuple1, package_tuple2)
            ]
        )

        with pytest.raises(CannotRemovePackage):
            with dg.remove_package_tuples(package_tuple1):
                pass

        pairs = dg.to_scored_package_tuple_pairs()
        pairs_expected = [
            (0.0, (None, package_tuple1)),
            (0.0, (package_tuple1, package_tuple2))
        ]
        assert pairs == pairs_expected

    def test_remove_direct_multiple(self):
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("flask", "0.12.0", "https://pypi.org/simple")
        package_tuple3 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple1, package_tuple2],
            paths=[
                (package_tuple1, package_tuple3),
                (package_tuple2, package_tuple3),
            ]
        )

        with dg.remove_package_tuples(package_tuple1) as txn:
            txn.commit()

        pairs = dg.to_scored_package_tuple_pairs()
        pairs_expected = [
            (0.0, (None, package_tuple2)),
            (0.0, (package_tuple2, package_tuple3)),
        ]

        assert pairs == pairs_expected

    def test_remove_transitive_one0(self):
        package_tuple0 = ("daiquiri", "1.5.0", "https://pypi.org/simple")
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")
        package_tuple4 = ("click", "0.2.0", "https://pypi.org/simple")
        package_tuple5 = ("werkzeug", "0.16.0", "https://pypi.org/simple")

        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple0, package_tuple1],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple4),
                (package_tuple1, package_tuple5),
                (package_tuple5, package_tuple4),
                (package_tuple1, package_tuple5),
                (package_tuple5, package_tuple3),
            ]
        )

        with dg.remove_package_tuples(package_tuple2) as txn:
            txn.commit()

        pairs = dg.to_scored_package_tuple_pairs()
        pairs_expected = [
            (0.0, (None, package_tuple0)),
            (0.0, (None, package_tuple1)),
            (0.0, (package_tuple1, package_tuple5)),
            (0.0, (package_tuple5, package_tuple4)),
            (0.0, (package_tuple5, package_tuple3)),
        ]

        assert pairs == pairs_expected

    def test_remove_transitive_one1(self):
        package_tuple0 = ("daiquiri", "1.5.0", "https://pypi.org/simple")
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")
        package_tuple4 = ("click", "0.2.0", "https://pypi.org/simple")
        package_tuple5 = ("werkzeug", "0.16.0", "https://pypi.org/simple")

        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple0, package_tuple1],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple4),
                (package_tuple1, package_tuple5),
                (package_tuple5, package_tuple3),
        ])

        with dg.remove_package_tuples(package_tuple2) as txn:
            txn.commit()

        pairs = dg.to_scored_package_tuple_pairs()
        pairs_expected = [
            (0.0, (None, package_tuple0)),
            (0.0, (None, package_tuple1)),
            (0.0, (package_tuple1, package_tuple5)),
            (0.0, (package_tuple5, package_tuple3)),
        ]

        assert pairs == pairs_expected

    def test_remove_transitive_multiple(self):
        package_tuple0 = ("daiquiri", "1.5.0", "https://pypi.org/simple")
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")
        package_tuple4 = ("click", "0.2.0", "https://pypi.org/simple")
        package_tuple5 = ("werkzeug", "0.16.0", "https://pypi.org/simple")

        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple0, package_tuple1],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple4),
                (package_tuple1, package_tuple5),
                (package_tuple5, package_tuple4),
                (package_tuple1, package_tuple5),
                (package_tuple5, package_tuple3),
            ]
        )

        with dg.remove_package_tuples(package_tuple2, package_tuple4) as txn:
            txn.commit()

        pairs = dg.to_scored_package_tuple_pairs()
        pairs_expected = [
            (0.0, (None, package_tuple0)),
            (0.0, (None, package_tuple1)),
            (0.0, (package_tuple1, package_tuple5)),
            (0.0, (package_tuple5, package_tuple3)),
        ]

        assert pairs == pairs_expected

    def test_remove_transitive_one_error(self):
        package_tuple0 = ("daiquiri", "1.5.0", "https://pypi.org/simple")
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")

        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple0, package_tuple1],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
            ]
        )

        with pytest.raises(CannotRemovePackage):
            with dg.remove_package_tuples(package_tuple3):
                pass

    def test_remove_transitive_multiple_error(self):
        package_tuple0 = ("daiquiri", "1.5.0", "https://pypi.org/simple")
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")
        package_tuple4 = ("click", "0.2.0", "https://pypi.org/simple")
        package_tuple5 = ("werkzeug", "0.16.0", "https://pypi.org/simple")

        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple0, package_tuple1],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple4),
                (package_tuple1, package_tuple5),
                (package_tuple5, package_tuple3),
        ])

        with pytest.raises(CannotRemovePackage):
            with dg.remove_package_tuples(package_tuple3, package_tuple4):
                pass

    def test_remove_transitive_cyclic(self):
        package_tuple1 = ("flask", "1.0.2", "https://pypi.org/simple")
        package_tuple2 = ("werkzeug", "0.15.4", "https://pypi.org/simple")
        package_tuple3 = ("click", "0.1.2", "https://pypi.org/simple")
        package_tuple4 = ("werkzeug", "0.16.0", "https://pypi.org/simple")
        package_tuple5 = ("click", "1.0.0", "https://pypi.org/simple")

        dg = DependencyGraphAdaptation.from_paths(
            direct_dependencies=[package_tuple1],
            paths=[
                (package_tuple1, package_tuple2),
                (package_tuple2, package_tuple3),
                (package_tuple3, package_tuple2),
                (package_tuple1, package_tuple4),
                (package_tuple4, package_tuple5),
            ]
        )

        with dg.remove_package_tuples(package_tuple3) as txn:
            txn.commit()

        pairs = dg.to_scored_package_tuple_pairs()
        pairs_expected = [
            (0.0, (None, package_tuple1)),
            (0.0, (package_tuple1, package_tuple4)),
            (0.0, (package_tuple4, package_tuple5)),
        ]

        assert pairs == pairs_expected
