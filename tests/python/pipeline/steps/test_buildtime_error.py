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

from itertools import chain

from base import AdviserTestCase

import pytest
from flexmock import flexmock

from thoth.adviser.python.pipeline.step_context import StepContext
from thoth.adviser.python.pipeline.steps import BuildtimeErrorFiltering
from thoth.adviser.python.dependency_graph import CannotRemovePackage

from thoth.storages import GraphDatabase
from thoth.common import RuntimeEnvironment
from thoth.python import PackageVersion
from thoth.python import Source


class _FakeProject:

    runtime_environment = RuntimeEnvironment.from_dict({})


class TestBuildtimeErrorFiltering(AdviserTestCase):
    """Test filtering out buildtime errors."""

    @staticmethod
    def _get_prepared_context():
        direct_dependencies = {
            ("flask", "0.12.0", "https://pypi.org/simple"): PackageVersion(
                name="flask",
                version="==0.12.0",
                index=Source("https://pypi.org/simple"),
                develop=False,
            )
        }

        paths = {
            ("flask", "0.12.0", "https://pypi.org/simple"): [
                (("flask", "0.12.0", "https://pypi.org/simple"), ("click", "2.0", "https://pypi.org/simple")),
                (("flask", "0.12.0", "https://pypi.org/simple"), ("click", "2.1", "https://pypi.org/simple")),
            ],
        }

        return StepContext.from_paths(direct_dependencies, paths)

    def test_remove_simple(self):
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            package_name="flask",
            package_version="0.12.0",
            index_url="https://pypi.org/simple",
            os_name=None,
            os_version=None,
            python_version=None
        ).and_return(False).ordered()
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            package_name="click",
            package_version="2.0",
            index_url="https://pypi.org/simple",
            os_name=None,
            os_version=None,
            python_version=None
        ).and_return(True).ordered()
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            package_name="click",
            package_version="2.1",
            index_url="https://pypi.org/simple",
            os_name=None,
            os_version=None,
            python_version=None
        ).and_return(False).ordered()

        step_context = self._get_prepared_context()

        buildtime_error_filtering = BuildtimeErrorFiltering(
            graph=GraphDatabase(),
            project=_FakeProject(),
            library_usage=None
        )
        buildtime_error_filtering.run(step_context)

        pairs = step_context.dependency_graph_adaptation.to_scored_package_tuple_pairs()
        assert len(pairs) == 2, "Wrong number of paths removed"
        pairs = chain(pair[1] for pair in pairs)
        assert ("click", "2.0", "https://pypi.org/simple") not in pairs, "Wrong path removed"

    def test_remove_error(self):
        flexmock(GraphDatabase)
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            package_name="flask",
            package_version="0.12.0",
            index_url="https://pypi.org/simple",
            os_name=None,
            os_version=None,
            python_version=None
        ).and_return(True).ordered()
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            package_name="click",
            package_version="2.0",
            index_url="https://pypi.org/simple",
            os_name=None,
            os_version=None,
            python_version=None
        ).and_return(False).ordered()
        GraphDatabase.should_receive("has_python_solver_error").with_args(
            package_name="click",
            package_version="2.1",
            index_url="https://pypi.org/simple",
            os_name=None,
            os_version=None,
            python_version=None,
        ).and_return(False).ordered()

        step_context = self._get_prepared_context()
        # TODO: pass project
        buildtime_error_filtering = BuildtimeErrorFiltering(
            graph=GraphDatabase(),
            project=_FakeProject(),
            library_usage=None,
        )

        with pytest.raises(CannotRemovePackage):
            buildtime_error_filtering.run(step_context)
