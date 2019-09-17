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
    def _prepare_step_context() -> StepContext:
        """Prepare step context for test scenarios."""
        direct_dependencies = {}
        paths = {}
        source = Source("https://pypi.org/simple")

        for version_identifier in ("0.12.1", "1.0.1"):
            package_tuple = ("flask", version_identifier, source.url)
            direct_dependencies[package_tuple] = PackageVersion(
                name="flask",
                version="==" + version_identifier,
                index=source.url,
                develop=False,
            )

            paths[package_tuple] = [
                (package_tuple, ("werkzeug", "0.13", "https://pypi.org/simple")),
                (package_tuple, ("werkzeug", "0.14", "https://pypi.org/simple")),
                (("werkzeug", "0.13", "https://pypi.org/simple"), ("six", "1.7.0", "https://pypi.org/simple")),
                (("werkzeug", "0.13", "https://pypi.org/simple"), ("six", "1.8.0", "https://pypi.org/simple")),
                (("werkzeug", "0.14", "https://pypi.org/simple"), ("six", "1.7.0", "https://pypi.org/simple")),
                (("werkzeug", "0.14", "https://pypi.org/simple"), ("six", "1.8.0", "https://pypi.org/simple")),
             ]

        return StepContext.from_paths(direct_dependencies, paths)

    def test_not_resolved(self) -> None:
        direct_dependencies = {
            ("flask", "1.12.0", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==1.12.0",
                index="https://pypi.org/simple",
                develop=False,
            )
        }
        paths = {
            ("flask", "1.12.0", "https://pypi.org/simple"): [
                (("flask", "1.12.0", "https://pypi.org/simple"), ("werkzeug", "0.13", None))
            ]
        }
        step_context = StepContext.from_paths(direct_dependencies, paths)
        assert ("werkzeug", "0.13", None) in step_context.iter_transitive_dependencies_tuple()
        assert ("werkzeug", "0.13", None) in step_context.unsolved_packages
        assert step_context.unsolved_packages.get(("werkzeug", "0.13", None)) is not None

        assert len(list(step_context.iter_transitive_dependencies(develop=None))) == 1
        assert len(list(step_context.iter_transitive_dependencies(develop=False))) == 1
        assert len(list(step_context.iter_transitive_dependencies(develop=True))) == 0
        direct_dependencies = list(step_context.iter_direct_dependencies())
        assert len(direct_dependencies) == 1
        assert direct_dependencies[0].name == "flask"

    def test_remove_package_tuple_direct(self) -> None:
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

    def test_remove_package_tuple_transitive(self) -> None:
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

    def test_remove_package_tuple_transitive_with_direct_change(self) -> None:
        """Test removal of a transitive dependency which leads to removal of a direct dependency candidate."""
        paths = {}
        direct_dependencies = {}
        source = Source("https://pypi.org/simple")
        for version_identifier in ("0.12.1", "1.0.1"):
            package_tuple = ("flask", version_identifier, source.url)

            direct_dependencies[package_tuple] = PackageVersion(
                name="flask",
                version="==" + version_identifier,
                index=Source("https://pypi.org/simple"),
                develop=False,
            )

        paths[("flask", "0.12.1", "https://pypi.org/simple")] = [
            (("flask", "0.12.1", "https://pypi.org/simple"), ("werkzeug", "0.13", "https://pypi.org/simple"))
        ]
        paths[("flask", "1.0.1", "https://pypi.org/simple")] = [
            (("flask", "1.0.1", "https://pypi.org/simple"), ("werkzeug", "0.14", "https://pypi.org/simple"))
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

    def test_remove_package_tuple_transitive_with_direct_error(self) -> None:
        """Test removal of a package which does not have any candidate of direct dependency."""
        paths = {}
        direct_dependencies = {}
        source = Source("https://pypi.org/simple")
        for version_identifier in ("0.12.1", "1.0.1"):
            package_tuple = ("flask", version_identifier, source.url)

            direct_dependencies[package_tuple] = PackageVersion(
                name="flask",
                version="==" + version_identifier,
                index=source.url,
                develop=False,
            )

            paths[package_tuple] = [
                (package_tuple, ("werkzeug", "0.13", "https://pypi.org/simple")),
                (package_tuple, ("werkzeug", "0.14", "https://pypi.org/simple")),
                (("werkzeug", "0.13", "https://pypi.org/simple"), ("six", "1.0.0", "https://pypi.org/simple")),
                (("werkzeug", "0.14", "https://pypi.org/simple"), ("six", "1.0.0", "https://pypi.org/simple")),
            ]

        step_context = StepContext.from_paths(direct_dependencies, paths)

        with pytest.raises(CannotRemovePackage):
            with step_context.remove_package_tuples(("six", "1.0.0", "https://pypi.org/simple")):
                pass

    def test_remove_package_tuple_transitive_with_direct_diamond_error(self) -> None:
        """Test removal of a package which does not have any candidate of direct dependency."""
        direct_dependencies = {
            ("flask", "0.12.1", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==0.12.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        }

        paths = {
            ("flask", "0.12.1", "https://pypi.org/simple"): [
                (("flask", "0.12.1", "https://pypi.org/simple"), ("werkzeug", "0.13", "https://pypi.org/simple")),
                (("werkzeug", "0.13", "https://pypi.org/simple"), ("six", "1.0.0", "https://pypi.org/simple")),
                (("flask", "0.12.1", "https://pypi.org/simple"), ("werkzeug", "0.14", "https://pypi.org/simple")),
                (("werkzeug", "0.14", "https://pypi.org/simple"), ("six", "1.0.0", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths)

        with pytest.raises(CannotRemovePackage):
            with step_context.remove_package_tuples(("six", "1.0.0", "https://pypi.org/simple")):
                pass

    def test_remove_package_tuple_direct_error(self) -> None:
        """Test removal of a package which is a direct dependency and causes issues."""
        direct_dependencies = {
            ("flask", "0.12.1", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==0.12.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        }

        step_context = StepContext.from_paths(
            direct_dependencies,
            paths={
                ("flask", "0.12.1", "https://pypi.org/simple"): []
            }
        )

        with pytest.raises(CannotRemovePackage):
            with step_context.remove_package_tuples(("flask", "0.12.1", "https://pypi.org/simple")):
                pass

    def test_remove_package_tuple_transitive_error(self) -> None:
        """Remove a transitive dependency which will cause error during removal."""
        direct_dependencies = {
            ("flask", "0.12.1", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==0.12.1",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        }

        paths = {
            ("flask", "0.12.1", "https://pypi.org/simple"): [
                (("flask", "0.12.1", "https://pypi.org/simple"), ("werkzeug", "0.13", "https://pypi.org/simple")),
                (("werkzeug", "0.13", "https://pypi.org/simple"), ("six", "1.0.0", "https://pypi.org/simple")),
            ]
        }

        step_context = StepContext.from_paths(direct_dependencies, paths=paths)

        with pytest.raises(CannotRemovePackage):
            with step_context.remove_package_tuples(("six", "1.0.0", "https://pypi.org/simple")):
                pass

    def test_iter_dependencies(self) -> None:
        source = Source("https://pypi.org/simple")

        direct_dependencies = {
            ("flask", "0.12.1", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==0.12.1",
                index=source,
                develop=False,
            ),
            ("pytest", "5.0.1", "https://pypi.org/simple"): PackageVersion(
                name="pytest",
                version="==5.0.1",
                index=source,
                develop=True,
            ),
            ("flask", "1.0.2", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==1.0.2",
                index=source,
                develop=False,
            ),
        }

        paths = {
            ("flask", "0.12.1", "https://pypi.org/simple"): [
                (("flask", "0.12.1", "https://pypi.org/simple"), ("werkzeug", "0.15.5", "https://pypi.org/simple")),
            ],
            ("flask", "1.0.2", "https://pypi.org/simple"): [
                (("flask", "1.0.2", "https://pypi.org/simple"), ("werkzeug", "0.15.5", "https://pypi.org/simple")),
            ],
            ("pytest", "5.0.1", "https://pypi.org/simple"): [
                (("pytest", "5.0.1", "https://pypi.org/simple"), ("pytest-cov", "2.7.1", "https://pypi.org/simple")),
            ],
        }

        step_context = StepContext.from_paths(direct_dependencies, paths=paths)

        all_dependencies = set(pv.to_tuple() for pv in step_context.iter_all_dependencies(develop=None))
        assert len(all_dependencies) == 5
        assert all_dependencies == {
            ("flask", "0.12.1", "https://pypi.org/simple"),
            ("pytest", "5.0.1", "https://pypi.org/simple"),
            ("flask", "1.0.2", "https://pypi.org/simple"),
            ("werkzeug", "0.15.5", "https://pypi.org/simple"),
            ("pytest-cov", "2.7.1", "https://pypi.org/simple"),
        }

        all_develop_dependencies = set(pv.to_tuple() for pv in step_context.iter_all_dependencies(develop=True))
        assert all_develop_dependencies == {
            ("pytest", "5.0.1", "https://pypi.org/simple"),
            ("pytest-cov", "2.7.1", "https://pypi.org/simple"),
        }

        all_nondevelop_dependencies = set(pv.to_tuple() for pv in step_context.iter_all_dependencies(develop=False))
        assert all_nondevelop_dependencies == {
            ("flask", "0.12.1", "https://pypi.org/simple"),
            ("flask", "1.0.2", "https://pypi.org/simple"),
            ("werkzeug", "0.15.5", "https://pypi.org/simple"),
        }

        transitive_nondevelop_dependencies = set(pv.to_tuple() for pv in step_context.iter_transitive_dependencies(develop=False))
        assert transitive_nondevelop_dependencies == {
            ("werkzeug", "0.15.5", "https://pypi.org/simple"),
        }

        transitive_develop_dependencies = set(pv.to_tuple() for pv in step_context.iter_transitive_dependencies(develop=True))
        assert transitive_develop_dependencies == {
            ("pytest-cov", "2.7.1", "https://pypi.org/simple"),
        }

        direct_develop_dependencies = set(pv.to_tuple() for pv in step_context.iter_direct_dependencies(develop=True))
        assert direct_develop_dependencies == {
            ("pytest", "5.0.1", "https://pypi.org/simple"),
        }

        direct_nondevelop_dependencies = set(pv.to_tuple() for pv in step_context.iter_direct_dependencies(develop=False))
        assert direct_nondevelop_dependencies == {
            ("flask", "0.12.1", "https://pypi.org/simple"),
            ("flask", "1.0.2", "https://pypi.org/simple"),
        }
