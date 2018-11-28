#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
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
import pytest

from base import AdviserTestCase
from graph_mock import with_graph_db_mock
from thoth.adviser.python import DependencyGraph
from thoth.python import Project


class TestDependencyGraph(AdviserTestCase):

    @with_graph_db_mock('db_1.yaml')
    def test_construct_project0(self, project_name: str = None):
        project_name = project_name or 'Pipfile_project0'
        project = Project.from_files(os.path.join(self.data_dir, 'projects', 'Pipfile_project0'))
        dependency_graph = DependencyGraph.from_project(project)
        count = 0
        for project in dependency_graph.walk():
            count += 1
        raise ValueError(f"{count}")
