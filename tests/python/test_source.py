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

"""Tests for package index handling - package source control."""

import pytest

from thoth.adviser.python.source import Source

from base import AdviserTestCase


class TestSource(AdviserTestCase):

    def test_dict(self):
        source_info = {
            'url': 'https://index-aicoe.a3c1.starter-us-west-1.openshiftapps.com/',
            'verify_ssl': True,
            'name': 'redhat-aicoe-experiments',
            'warehouse': True
        }

        source = Source.from_dict(source_info)
        assert source.to_dict(include_warehouse=True) == source_info
        source_info.pop('warehouse')
        assert source.to_dict() == source_info

    def test_default_warehouse(self):
        source_info = {
            'url': 'https://index-aicoe.a3c1.starter-us-west-1.openshiftapps.com/',
            'verify_ssl': True,
            'name': 'redhat-aicoe-experiments',
        }

        source = Source.from_dict(source_info)
        assert source.warehouse is False, "Default warehouse configuration is not implicitly set to False"

    @pytest.mark.online
    def test_get_package_hashes_warehouse(self):
        pypi_index = {
            'name': 'pypi',
            'url': 'https://pypi.python.org/simple',
            'verify_ssl': True,
            'warehouse': True
        }

        source = Source.from_dict(pypi_index)
        assert source.get_package_hashes('selinon', '1.0.0') == [
            {
                'name': 'selinon-1.0.0-py3-none-any.whl',
                'sha256': '9a62e16ea9dc730d006e1271231f318ee2dad48d145fd3b9e902a925ea3cca2e'
            },
            {
                'name': 'selinon-1.0.0.tar.gz',
                'sha256': '392ab7d2ff1430417a50327515538cec3e9f302b7513dc8e8474745a1b28187a'
            }
        ]

    @pytest.mark.online
    def test_get_package_hashes_server(self):
        pypi_index = {
            'name': 'aicoe',
            'url': 'https://index-aicoe.a3c1.starter-us-west-1.openshiftapps.com/fedora28/1.9/jemalloc/',
            'verify_ssl': True,
            'warehouse': False
        }

        source = Source.from_dict(pypi_index)
        assert source.get_package_hashes('tensorflow', '1.9.0') == [
            {
                'name': 'tensorflow-1.9.0-cp27-cp27mu-linux_x86_64.whl',
                'sha56': 'dfcf516c771bb0b146e85a03434b837cb6a642735163b4d88667bca9e0141910'
            },
            {
                'name': 'tensorflow-1.9.0-cp35-cp35m-linux_x86_64.whl',
                'sha56': '689dc93f298a25a23c539298221ae213e8ff0e9c6fb8726835313239538299cb'
            },
            {
                'name': 'tensorflow-1.9.0-cp36-cp36m-linux_x86_64.whl',
                'sha56': '147a15ebd7bda819f9a9a956e7f3924e0992c68fc22d95e0e3ea23d15af57c85'
            }
        ]
