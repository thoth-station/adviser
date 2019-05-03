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

"""Test filtering out buildtime errors."""

from base import AdviserTestCase

import pytest
from flexmock import flexmock

from thoth.adviser.python.pipeline.step_context import StepContext
from thoth.adviser.python.pipeline.steps import BuildtimeErrorFiltering
from thoth.adviser.python.exceptions import UnableLock

from thoth.storages import GraphDatabase
from thoth.python import PackageVersion
from thoth.python import Source


class TestBuildtimeErrorFiltering(AdviserTestCase):
    """Test filtering out buildtime errors."""

    @staticmethod
    def _get_prepared_context():
        step_context = StepContext()
        direct_dependencies = [
            PackageVersion(
                name="flask",
                version="==0.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            ),
        ]
        for package_version in direct_dependencies:
            step_context.add_resolved_direct_dependency(package_version)

        step_context.add_paths(
            [
                [
                    ("flask", "0.12.0", "https://pypi.org/simple"),
                    ("click", "2.0", "https://pypi.org/simple"),
                ],
                [
                    ("flask", "0.12.0", "https://pypi.org/simple"),
                    ("click", "2.1", "https://pypi.org/simple"),
                ],
            ]
        )

        return step_context

    def test_remove_simple(self):
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            "flask", "0.12.0", "https://pypi.org/simple",
        ).and_return(False).ordered()
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            "click", "2.0", "https://pypi.org/simple",
        ).and_return(True).ordered()
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            "click", "2.1", "https://pypi.org/simple",
        ).and_return(False).ordered()

        step_context = self._get_prepared_context()

        buildtime_error_filtering = BuildtimeErrorFiltering(graph=GraphDatabase(), project=None)
        buildtime_error_filtering.run(step_context)

        assert len(step_context.raw_paths) == 1, "Wrong number of paths removed"
        assert ("click", "2.0", "https://pypi.org/simple") not in step_context.raw_paths[0], "Wrong path removed"

    def test_remove_error(self):
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            "flask", "0.12.0", "https://pypi.org/simple",
        ).and_return(True).ordered()
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            "click", "2.0", "https://pypi.org/simple",
        ).and_return(False).ordered()
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            "click", "2.1", "https://pypi.org/simple",
        ).and_return(False).ordered()

        step_context = self._get_prepared_context()
        buildtime_error_filtering = BuildtimeErrorFiltering(graph=GraphDatabase(), project=None)

        with pytest.raises(UnableLock):
            buildtime_error_filtering.run(step_context)
