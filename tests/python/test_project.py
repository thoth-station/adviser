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

import os
from base import AdviserTestCase

import pytest

from thoth.adviser.python import Project
from thoth.adviser.python import Source
from thoth.adviser.python import Pipfile
from thoth.adviser.python import PipfileLock
from thoth.adviser.exceptions import InternalError


class TestProject(AdviserTestCase):
    def test_add_package(self):
        pipfile = Pipfile.from_file(os.path.join(self.data_dir, 'Pipfile_test1'))
        pipfile_lock = PipfileLock.from_file(os.path.join(self.data_dir, 'Pipfile_test1.lock'))
        project = Project(pipfile=pipfile, pipfile_lock=pipfile_lock)

        assert 'selinon' not in project.pipfile.packages.packages
        project.add_package('selinon', '==1.0.0')

        assert 'selinon' in project.pipfile.packages.packages
        assert project.pipfile.packages['selinon'].version == '==1.0.0'
        assert project.pipfile.packages['selinon'].index is None
        assert project.pipfile.packages['selinon'].develop is False

        # Do not add the package to the lock - lock has to be explicitly done.
        assert 'selinon' not in project.pipfile_lock.packages.packages

    def test_add_package_develop(self):
        pipfile = Pipfile.from_file(os.path.join(self.data_dir, 'Pipfile_test1'))
        pipfile_lock = PipfileLock.from_file(os.path.join(self.data_dir, 'Pipfile_test1.lock'))
        project = Project(pipfile=pipfile, pipfile_lock=pipfile_lock)

        source = Source(name='foo', url='https://foo.bar', verify_ssl=True, warehouse=False)

        assert 'selinon' not in project.pipfile.dev_packages.packages

        with pytest.raises(InternalError):
            # Trying to add package with source but source is not present in the meta.
            project.add_package('selinon', '==1.0.0', develop=True, source=source)

        source = project.add_source(url='https://foo.bar')
        project.add_package('selinon', '==1.0.0', develop=True, source=source)

        assert 'selinon' in project.pipfile.dev_packages.packages
        assert project.pipfile.dev_packages['selinon'].version == '==1.0.0'
        assert project.pipfile.dev_packages['selinon'].index == 'foo'
        assert project.pipfile.dev_packages['selinon'].develop is True
        # Do not add the package to the lock - lock has to be explicitly done.
        assert 'selinon' not in project.pipfile_lock.dev_packages.packages

    def test_add_source(self):
        pipfile = Pipfile.from_file(os.path.join(self.data_dir, 'Pipfile_test1'))
        pipfile_lock = PipfileLock.from_file(os.path.join(self.data_dir, 'Pipfile_test1.lock'))
        project = Project(pipfile=pipfile, pipfile_lock=pipfile_lock)

        source = project.add_source(url='https://foo.bar')

        assert source.name is not None

        assert source.name in project.pipfile.meta.sources
        assert source is project.pipfile.meta.sources[source.name]

        assert source.name in project.pipfile_lock.meta.sources
        assert source is project.pipfile_lock.meta.sources[source.name]
