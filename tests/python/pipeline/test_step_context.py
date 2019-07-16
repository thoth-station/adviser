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

"""Test manipulation with step context."""

import pytest

from thoth.python import PackageVersion
from thoth.python import Source

from thoth.adviser.python.pipeline.step_context import StepContext
from thoth.adviser.python.dependency_graph import CannotRemovePackage

from base import AdviserTestCase


class TestStepContext(AdviserTestCase):
    """Test step context - manipulation on paths."""

    @staticmethod
    def _prepare_step_context():
        """Prepare step context for test scenarios."""
        direct_dependencies = []
        paths = []
        for version_identifier in ("==0.12.1", "==1.0.1"):
            direct_dependencies.append(
                PackageVersion(
                    name="flask",
                    version=version_identifier,
                    index=Source("https://pypi.org/simple"),
                    develop=False,
                )
            )

            paths.extend([
                [
                    ("flask", version_identifier[2:], "https://pypi.org/simple"),
                    ("werkzeug", "0.13", "https://pypi.org/simple"),
                    ("six", "1.7.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", version_identifier[2:], "https://pypi.org/simple"),
                    ("werkzeug", "0.13", "https://pypi.org/simple"),
                    ("six", "1.8.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", version_identifier[2:], "https://pypi.org/simple"),
                    ("werkzeug", "0.14", "https://pypi.org/simple"),
                    ("six", "1.7.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", version_identifier[2:], "https://pypi.org/simple"),
                    ("werkzeug", "0.14", "https://pypi.org/simple"),
                    ("six", "1.8.0", "https://pypi.org/simple"),
                ],
            ])

        return StepContext.from_paths(direct_dependencies, paths)

    def test_remove_package_tuple_direct(self) -> StepContext:
        """Test removal of a single direct dependency."""
        step_context = self._prepare_step_context()
        original_direct_deps_len = len(list(step_context.iter_direct_dependencies()))
        original_transitive_deps_len = len(
            list(step_context.iter_transitive_dependencies())
        )

        to_remove = ("flask", "0.12.1", "https://pypi.org/simple")
        with step_context.remove_package_tuples(to_remove) as txn:
            txn.commit()

        assert original_transitive_deps_len == len(
            list(step_context.iter_transitive_dependencies())
        ), "No transitive dependency should be removed"
        assert original_direct_deps_len - 1 == len(
            list(step_context.iter_direct_dependencies())
        )
        assert to_remove not in list(step_context.iter_direct_dependencies_tuple())
        assert len(list(step_context.iter_direct_dependencies())) == len(
            list(step_context.iter_direct_dependencies_tuple())
        )
        assert len(list(step_context.iter_transitive_dependencies())) == len(
            list(step_context.iter_transitive_dependencies_tuple())
        )

    def test_remove_package_tuple_transitive(self):
        """Test removal of a transitive dependency."""
        step_context = self._prepare_step_context()
        original_direct_deps_len = len(list(step_context.iter_direct_dependencies()))
        original_transitive_deps_len = len(
            list(step_context.iter_transitive_dependencies())
        )

        to_remove = ("werkzeug", "0.13", "https://pypi.org/simple")
        with step_context.remove_package_tuples(to_remove) as txn:
            txn.commit()

        assert original_direct_deps_len == len(
            list(step_context.iter_direct_dependencies())
        ), "No direct dependencies should be removed"
        assert original_transitive_deps_len - 1 == len(
            list(step_context.iter_transitive_dependencies_tuple())
        )
        assert to_remove not in list(step_context.iter_transitive_dependencies_tuple())
        assert len(list(step_context.iter_direct_dependencies())) == len(
            list(step_context.iter_direct_dependencies_tuple())
        )
        assert len(list(step_context.iter_transitive_dependencies())) == len(
            list(step_context.iter_transitive_dependencies_tuple())
        )

    def test_remove_package_tuple_transitive_with_direct_change(self):
        """Test removal of a transitive dependency which leads to removal of a direct dependency candidate."""
        direct_dependencies = []
        for version_identifier in ("==0.12.1", "==1.0.1"):
            direct_dependencies.append(
                PackageVersion(
                    name="flask",
                    version=version_identifier,
                    index=Source("https://pypi.org/simple"),
                    develop=False,
                )
            )

        paths = [
            [
                ("flask", "0.12.1", "https://pypi.org/simple"),
                ("werkzeug", "0.13", "https://pypi.org/simple"),
            ],
            [
                ("flask", "1.0.1", "https://pypi.org/simple"),
                ("werkzeug", "0.14", "https://pypi.org/simple"),
            ],
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths)

        # Now remove werkzeug 0.14 which will lead to removal of flask 1.0.1.
        to_remove = ("werkzeug", "0.14", "https://pypi.org/simple")
        with step_context.remove_package_tuples(to_remove) as txn:
            txn.commit()

        assert len(list(step_context.iter_direct_dependencies())) == 1
        assert len(list(step_context.iter_transitive_dependencies_tuple())) == 1
        assert len(list(step_context.iter_transitive_dependencies_tuple())) == len(
            list(step_context.iter_transitive_dependencies())
        )
        assert to_remove not in list(step_context.iter_transitive_dependencies_tuple())

    def test_remove_package_tuple_transitive_with_direct_error(self):
        """Test removal of a package which does not have any candidate of direct dependency."""
        direct_dependencies = []
        for version_identifier in ("==0.12.1", "==1.0.1"):
            direct_dependencies.append(
                PackageVersion(
                    name="flask",
                    version=version_identifier,
                    index=Source("https://pypi.org/simple"),
                    develop=False,
                )
            )

        paths = [
            [
                ("flask", "0.12.1", "https://pypi.org/simple"),
                ("werkzeug", "0.13", "https://pypi.org/simple"),
                ("six", "1.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "1.0.1", "https://pypi.org/simple"),
                ("werkzeug", "0.14", "https://pypi.org/simple"),
                ("six", "1.0.0", "https://pypi.org/simple"),
            ],
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths)

        with pytest.raises(CannotRemovePackage):
            with step_context.remove_package_tuples(("six", "1.0.0", "https://pypi.org/simple")):
                pass

    def test_remove_package_tuple_transitive_with_direct_diamond_error(self):
        """Test removal of a package which does not have any candidate of direct dependency."""
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        ]

        paths = [
            [
                ("flask", "0.12.1", "https://pypi.org/simple"),
                ("werkzeug", "0.13", "https://pypi.org/simple"),
                ("six", "1.0.0", "https://pypi.org/simple"),
            ],
            [
                ("flask", "0.12.1", "https://pypi.org/simple"),
                ("werkzeug", "0.14", "https://pypi.org/simple"),
                ("six", "1.0.0", "https://pypi.org/simple"),
            ],
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths)

        with pytest.raises(CannotRemovePackage):
            with step_context.remove_package_tuples(("six", "1.0.0", "https://pypi.org/simple")):
                pass

    def test_remove_package_tuple_direct_error(self):
        """Test removal of a package which is a direct dependency and causes issues."""
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths=[])

        with pytest.raises(CannotRemovePackage):
            with step_context.remove_package_tuples(("flask", "0.12.1", "https://pypi.org/simple")):
                pass

    def test_remove_package_tuple_transitive_error(self):
        """Remove a transitive dependency which will cause error during removal."""
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        ]

        paths = [
            [
                ("flask", "0.12.1", "https://pypi.org/simple"),
                ("werkzeug", "0.13", "https://pypi.org/simple"),
                ("six", "1.0.0", "https://pypi.org/simple"),
            ]
        ]

        step_context = StepContext.from_paths(direct_dependencies, paths=paths)

        with pytest.raises(CannotRemovePackage):
            with step_context.remove_package_tuples(("six", "1.0.0", "https://pypi.org/simple")):
                pass
