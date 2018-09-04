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

"""Tests for package-version parsing and handling."""

import pytest

from thoth.adviser.python.package_version import PackageVersion
from thoth.adviser.exceptions import UnsupportedConfiguration
from thoth.adviser.exceptions import PipfileParseError
from thoth.adviser.exceptions import InternalError

from base import AdviserTestCase


class TestPackageVersion(AdviserTestCase):

    @pytest.mark.parametrize(
        "package_name,package_info,expected_values,is_locked",
        [
            (
                'tensorflow',
                {'version': '==1.9.0rc0', 'index': 'redhat-aicoe-experiments'},
                {'index': 'redhat-aicoe-experiments', 'version': '==1.9.0rc0'},
                True
            ),
            (
                'tensorflow',
                {'version': '*'},
                {'index': None, 'version': '*'},
                False
            ),
            (
                'tensorflow',
                {'version': '<1.9'},
                {'index': None, 'version': '<1.9'},
                False
            )
        ]
    )
    def test_from_pipfile_entry(self, package_name, package_info, expected_values, is_locked):
        package_version = PackageVersion.from_pipfile_entry(package_name, package_info, develop=False)

        for name, value in expected_values.items():
            assert getattr(package_version, name) == value,\
                f"Expected value for {name} for instance does not match: {value}"

        assert package_version.is_locked() is is_locked

    @pytest.mark.parametrize(
        "package_name,package_info",
        [
            (
                'igitt',
                {'git': 'https://gitlab.com/gitmate/open-source/IGitt.git'}
            )
        ]
    )
    def test_from_pipfile_entry_error(self, package_name, package_info):
        with pytest.raises(UnsupportedConfiguration):
            PackageVersion.from_pipfile_entry(package_name, package_info, develop=False)

    @pytest.mark.parametrize(
        "package_name,package_info,expected_values",
        [
            (
                'tensorflow',
                {'version': '==1.9.0rc0', 'index': 'redhat-aicoe-experiments', 'hashes':
                    [
                        "sha256:9c2dc36b84f3729361990b4488b7fde1cbe5afb9e3b59456aafc6928684fcd4b"
                    ]
                 },
                {'index': 'redhat-aicoe-experiments', 'version': '==1.9.0rc0', 'hashes':
                    [
                        "sha256:9c2dc36b84f3729361990b4488b7fde1cbe5afb9e3b59456aafc6928684fcd4b"
                    ]
                 }
            )
        ]
    )
    def test_from_pipfile_lock_entry(self, package_name, package_info, expected_values):
        package_version = PackageVersion.from_pipfile_lock_entry(package_name, package_info, develop=False)

        for name, value in expected_values.items():
            assert getattr(package_version, name) == value, \
                f"Expected value {name} for locked package {package_name} does not match: {value}"

        assert package_version.is_locked() is True

    @pytest.mark.parametrize(
        "package_name,package_info",
        [
            (
                # Package index not used.
                'igitt',
                {'git': 'https://gitlab.com/gitmate/open-source/IGitt.git'}
            ),
            (
                # No hashes present.
                'tensorflow',
                {'version': '==1.9.0rc0', 'index': 'redhat-aicoe-experiments', 'hashes': []}
            ),
            (
                # Missing version information.
                'tensorflow',
                {'index': 'redhat-aicoe-experiments', 'hashes':
                    [
                        "sha256:9c2dc36b84f3729361990b4488b7fde1cbe5afb9e3b59456aafc6928684fcd4b"
                    ]
                 }
            )
        ]
    )
    def test_from_pipfile_lock_entry_error(self, package_name, package_info):
        with pytest.raises(PipfileParseError):
            PackageVersion.from_pipfile_lock_entry(package_name, package_info, develop=False)

    def test_sorted(self):
        array = []
        for version in ('==1.0.0', '==0.1.0', '==3.0.0'):
            array.append(PackageVersion(name='tensorflow', version=version, develop=False))

        assert sorted(pv.locked_version for pv in array) == ['0.1.0', '1.0.0', '3.0.0']

    def test_semver_error(self):
        with pytest.raises(InternalError):
            return PackageVersion(name='tensorflow', version='>1.0.0', develop=False).semantic_version

    def test_version_specification(self):
        pv = PackageVersion(name='tensorflow', version='==0.1.0', develop=False).semantic_version
        vs = PackageVersion(name='tensorflow', version='<1.0.0', develop=False).version_specification
        assert pv in vs

        pv = PackageVersion(name='tensorflow', version='==2.1.0', develop=False).semantic_version
        assert pv not in vs

        vs = PackageVersion(name='tensorflow', version='==2.1.0', develop=False).version_specification
        assert pv in vs
