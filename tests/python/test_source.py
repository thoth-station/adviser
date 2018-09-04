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

import os
import json
from pathlib import Path

import pytest
import requests
from flexmock import flexmock

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

    def test_get_packages(self):
        source_info = {
            'name': 'pypi',
            'url': 'https://pypi.org/simple',
            'verify_ssl': True,
            'warehouse': True
        }

        class Response:
            text = (Path(self.data_dir) / "simple.html").read_text()

            @staticmethod
            def raise_for_status():
                pass

        flexmock(requests)\
            .should_receive('get')\
            .with_args(source_info['url'], verify=source_info['verify_ssl'])\
            .and_return(Response)

        source = Source.from_dict(source_info)
        assert source.get_packages() == {
            'selinon',
            'thoth',
            'thoth-adviser',
            'thoth-analyzer',
            'thoth-common',
            'thoth-dispatcher',
            'thoth-lab',
            'thoth-package-extract',
            'thoth-solver',
            'thoth-storages',
            'thoth-tasks'
        }

    def test_get_package_versions_warehouse(self):
        source_info = {
            'name': 'pypi',
            'url': 'https://pypi.org/simple',
            'verify_ssl': True,
            'warehouse': True
        }

        class Response:
            status_code = 200

            @staticmethod
            def raise_for_status():
                pass

            @staticmethod
            def json():
                with open(os.path.join(self.data_dir, 'selinon-warehouse-api.json')) as json_file:
                    return json.load(json_file)

        flexmock(requests)\
            .should_receive('get')\
            .with_args('https://pypi.org/pypi/selinon/json', verify=source_info['verify_ssl'])\
            .and_return(Response)

        source = Source.from_dict(source_info)
        assert set(source.get_package_versions('selinon')) == {
            '0.1.0rc2',
            '0.1.0rc3',
            '0.1.0rc4',
            '0.1.0rc5',
            '0.1.0rc6',
            '0.1.0rc7',
            '0.1.0rc8',
            '0.1.0rc9',
            '1.0.0',
            '1.0.0rc1',
            '1.0.0rc2',
            '1.0.0rc3',
            '1.0.0rc4'
        }

    def test_get_package_versions_simple(self):
        source_info = {
            'name': 'pypi',
            'url': 'https://pypi.org/simple',
            'verify_ssl': True,
            'warehouse': False
        }

        class Response:
            text = (Path(self.data_dir) / "simple.html").read_text()
            status_code = 200

            @staticmethod
            def raise_for_status():
                pass

        #flexmock(requests)\
        #    .should_receive('get')\
        #    .with_args(source_info['url'], verify=source_info['verify_ssl'])\
        #    .and_return(Response)

        source = Source.from_dict(source_info)
        # TODO: reduce in response
        assert set(source.get_package_versions('tensorflow')) == {
            '1.1.0rc0',
             '1.7.0',
             '1.10.0rc0',
             '1.8.0',
             '1.10.0',
             '0.12.0rc1',
             '1.4.1',
             '0.12.0rc0',
             '1.2.0rc1',
             '1.5.1',
             '1.9.0',
             '1.2.0rc0',
             '0.12.0',
             '1.9.0rc0',
             '1.4.0rc0',
             '1.1.0rc1',
             '1.2.0',
             '1.6.0rc0',
             '1.0.1',
             '1.1.0',
             '1.3.0',
             '1.8.0rc0',
             '1.5.0rc0',
             '1.10.0rc1',
             '1.3.0rc1',
             '1.2.1',
             '1.4.0rc1',
             '1.9.0rc1',
             '1.3.0rc0',
             '1.7.0rc1',
             '1.6.0',
             '1.1.0rc2',
             '1.5.0rc1',
             '1.2.0rc2',
             '1.5.0',
             '1.8.0rc1',
             '1.9.0rc2',
             '1.0.0',
             '1.3.0rc2',
             '1.7.0rc0',
             '1.7.1',
             '1.6.0rc1',
             '1.4.0',
             '0.12.1'}