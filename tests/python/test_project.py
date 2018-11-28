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

import attr
import pytest
import semantic_version as semver

from thoth.python import Project
from thoth.python import Source
from thoth.python import Pipfile
from thoth.python import PipfileLock
from thoth.adviser.exceptions import InternalError


class TestProject(AdviserTestCase):
    def test_add_package(self):
        pipfile = Pipfile.from_file(os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test1'))
        pipfile_lock = PipfileLock.from_file(os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test1.lock'))
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
        pipfile = Pipfile.from_file(os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test1'))
        pipfile_lock = PipfileLock.from_file(os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test1.lock'))
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
        pipfile = Pipfile.from_file(os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test1'))
        pipfile_lock = PipfileLock.from_file(os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test1.lock'))
        project = Project(pipfile=pipfile, pipfile_lock=pipfile_lock)

        source = project.add_source(url='https://foo.bar')

        assert source.name is not None

        assert source.name in project.pipfile.meta.sources
        assert source is project.pipfile.meta.sources[source.name]

        assert source.name in project.pipfile_lock.meta.sources
        assert source is project.pipfile_lock.meta.sources[source.name]

    def test_get_outdated_package_versions_indirect(self):
        # The difference between direct and indirect - Pipenv states "index" in
        # the Pipfile.lock file if the given package is a direct dependency.
        # The "index" key for indirect dependencies is omitted though. This way
        # we check both - logic for indirect/direct is slightly different.
        # We cannot use flexmock as Source has slots.
        @attr.s
        class MySource:
            url = attr.ib(type=str)
            verify_ssl = attr.ib(type=bool)
            name = attr.ib(type=str)
            warehouse = attr.ib(type=bool, default=False)
            warehouse_api_url = attr.ib(default=None, type=str)

            def get_latest_package_version(_, package_name):
                return {
                    "certifi": semver.Version.coerce("2018.10.15"), 
                    "chardet": semver.Version.coerce("3.0.4"),
                    "idna": semver.Version.coerce("2.10"),  # Bumped from 2.7
                    "requests": semver.Version.coerce("2.19.1"),
                    "termcolor": semver.Version.coerce("1.1.0"),
                    "urllib3": semver.Version.coerce("1.23"),
                }[package_name]

        project = Project.from_files(
            os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test2'),
            os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test2.lock')
        )

        new_sources = {}
        for source in project.pipfile_lock.meta.sources.values():
            new_sources[source.name] = MySource(**source.to_dict())
        project.pipfile_lock.meta.sources = new_sources

        for package_version in project.iter_dependencies_locked(with_devel=True):
            if package_version.index:
                package_version.index = new_sources[package_version.index.name]

        result = project.get_outdated_package_versions()
        assert len(result) == 1
        assert 'idna' in result
        assert len(result['idna']) == 2
        assert result['idna'][0] is project.pipfile_lock.packages['idna']
        assert isinstance(result['idna'][1], semver.Version)
        assert str(result['idna'][1]) == '2.10.0'


    def test_get_outdated_package_versions_direct(self):
        # See previous test comments for more info.
        # We cannot use flexmock as Source has slots.
        @attr.s
        class MySource:
            url = attr.ib(type=str)
            verify_ssl = attr.ib(type=bool)
            name = attr.ib(type=str)
            warehouse = attr.ib(type=bool, default=False)
            warehouse_api_url = attr.ib(default=None, type=str)

            def get_latest_package_version(_, package_name):
                return {
                    "certifi": semver.Version.coerce("2018.10.15"), 
                    "chardet": semver.Version.coerce("3.0.4"),
                    "idna": semver.Version.coerce("2.7"),
                    "requests": semver.Version.coerce("3.0.0"),
                    "termcolor": semver.Version.coerce("1.1.0"),
                    "urllib3": semver.Version.coerce("1.23"),
                }[package_name]

        project = Project.from_files(
            os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test2'),
            os.path.join(self.data_dir, 'pipfiles', 'Pipfile_test2.lock')
        )

        new_sources = {}
        for source in project.pipfile_lock.meta.sources.values():
            new_sources[source.name] = MySource(**source.to_dict())
        project.pipfile_lock.meta.sources = new_sources

        for package_version in project.iter_dependencies_locked(with_devel=True):
            if package_version.index:
                package_version.index = new_sources[package_version.index.name]

        result = project.get_outdated_package_versions()
        assert len(result) == 1
        assert 'requests' in result
        assert len(result['requests']) == 2
        assert result['requests'][0] is project.pipfile_lock.packages['requests']
        assert isinstance(result['requests'][1], semver.Version)
        assert str(result['requests'][1]) == '3.0.0'
