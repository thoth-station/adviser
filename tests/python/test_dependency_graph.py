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


"""Test dependency graph construction and operations on it."""

import os

from base import AdviserTestCase
from graph_mock import MockedGraphDatabase
from thoth.adviser.python import DependencyGraph
from thoth.python import Project
from thoth.common import RuntimeEnvironment


class TestDependencyGraph(AdviserTestCase):
    def always_true(self, _):
        return True, [{"foo": "bar"}]

    def test_construct_project0(self):
        graph = MockedGraphDatabase("db_1.yaml")
        project = Project.from_files(
            os.path.join(self.data_dir, "projects", "Pipfile_project0")
        )

        dependency_graph = DependencyGraph.from_project(graph, project, runtime_environment=RuntimeEnvironment.from_dict({}), restrict_indexes=False)
        count = 0
        stacks = set()
        for reasoning, generated_project in dependency_graph.walk(self.always_true):
            assert isinstance(generated_project, Project)
            generated_project = generated_project.to_dict()
            pipfile_lock = generated_project['requirements_locked']
            stack = tuple((k, v['version'], v['index']) for k, v in pipfile_lock['default'].items())
            assert stack not in stacks
            stacks.add(stack)

            assert not pipfile_lock['develop']

            assert isinstance(reasoning, tuple)
            assert reasoning == (True, [{"foo": "bar"}])
            count += 1

        # 7 stacks for a/b, 8 stacks for b/d => 56 as they do not interfere
        assert count == 56
