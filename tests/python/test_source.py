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
        # We set warehouse to False so the there is not used API of the public PyPI index but rather there
        # is tested code that implements PEP-0503 logic.
        pypi_index = {
            'name': 'aicoe',
            'url': 'https://pypi.python.org/simple',
            'verify_ssl': True,
            'warehouse': False
        }

        source = Source.from_dict(pypi_index)
        assert source.get_package_hashes('tensorflow', '0.12.0') == [
            {'name': 'tensorflow-0.12.0rc0-cp27-cp27m-macosx_10_11_x86_64.whl',
             'sha256': 'feaf06c7df5c0a480654bf1f38dd4d3b809c7315502a7d9f295033f9d2bd9b13'},
            {'name': 'tensorflow-0.12.0rc0-cp27-cp27mu-manylinux1_x86_64.whl',
             'sha256': 'd4b6ca2cacb64513350c1544c33a6e9493073f928398407d20ba018d991fb28e'},
            {'name': 'tensorflow-0.12.0rc0-cp34-cp34m-manylinux1_x86_64.whl',
             'sha256': '58ed3cda954eb6cfe07f87273570de5c568b02dfb0f9ae20ca4b01e3455ef0dd'},
            {'name': 'tensorflow-0.12.0rc0-cp35-cp35m-macosx_10_11_x86_64.whl',
             'sha256': '9cd8631971e02969ad17ca68e66e7cf324c888092a9111c8764e6e61187c47e3'},
            {'name': 'tensorflow-0.12.0rc0-cp35-cp35m-manylinux1_x86_64.whl',
             'sha256': '20e3f558a0522cee625c2c67adefe3e943ceb83545b7c1c9b062eb3d7b2cf5dd'},
            {'name': 'tensorflow-0.12.0rc0-cp35-cp35m-win_amd64.whl',
             'sha256': 'aea0f34d979d9c7824c30c1a857e74f3c6f5b3e344461a33bdc809da67d10bcb'},
            {'name': 'tensorflow-0.12.0rc1-cp27-cp27m-macosx_10_11_x86_64.whl',
             'sha256': '1d864572d483d44b9735af1050f06f0dd4eedeb1e4208c5a93d115b46b05195b'},
            {'name': 'tensorflow-0.12.0rc1-cp27-cp27mu-manylinux1_x86_64.whl',
             'sha256': 'ec4549f0347be1db56dd9bb50ff68bef1b57e5a1bf31d0fb7037936ced6e2a79'},
            {'name': 'tensorflow-0.12.0rc1-cp34-cp34m-manylinux1_x86_64.whl',
             'sha256': '3b51610edecf070eefb9d63a29ff98ed29f94ead6d9373a496b965823fe54914'},
            {'name': 'tensorflow-0.12.0rc1-cp35-cp35m-macosx_10_11_x86_64.whl',
             'sha256': '72c15e0777268abba4195a8ae711e0e189f2569f6aca3f1ede4e24613f07c133'},
            {'name': 'tensorflow-0.12.0rc1-cp35-cp35m-manylinux1_x86_64.whl',
             'sha256': '1004a95f0f4e81a7bfd6935dceda0cbeb4cc1105e18a73e7f9e856c8d4db6fab'},
            {'name': 'tensorflow-0.12.0rc1-cp35-cp35m-win_amd64.whl',
             'sha256': '895fa483d19eb8caef77171c6357aabb56ef8a5a1ac27deb5333ce16d348046f'},
            {'name': 'tensorflow-0.12.0-cp27-cp27m-macosx_10_11_x86_64.whl',
             'sha256': '90c71d70dc6df9091be9832819a74464a8efe0958b90249a63c69c652b88fc66'},
            {'name': 'tensorflow-0.12.0-cp27-cp27mu-manylinux1_x86_64.whl',
             'sha256': '3c51e10b6d5ec7afbc38af772ea65518930873a4806b062171fa1d45fd2ddb3d'},
            {'name': 'tensorflow-0.12.0-cp34-cp34m-manylinux1_x86_64.whl',
             'sha256': '44f873e85780e1d82746de1ceae1a0100ca5ccc84f779c2f2e49f20ed26c7525'},
            {'name': 'tensorflow-0.12.0-cp35-cp35m-macosx_10_11_x86_64.whl',
             'sha256': 'd0616adfb35b9a915f212d68e9389113e56d41f1131397ebaf14b5b77487733a'},
            {'name': 'tensorflow-0.12.0-cp35-cp35m-manylinux1_x86_64.whl',
             'sha256': '11053eb97d21402f6fbfcd5d8c8bcf8b6ba74d2d890f16c8b7588065bef355db'},
            {'name': 'tensorflow-0.12.0-cp35-cp35m-win_amd64.whl',
             'sha256': '795a1bdddc832289ab958dc9bd9a1c46b849011cbc81fd89d6fe144efc7aae69'}
        ]

    def test_get_packages(self):
        source_info = {
            'name': 'my-pypi',
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
            'name': 'my-pypi',
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
            'name': 'my-pypi',
            'url': 'https://pypi.org/simple',
            'verify_ssl': True,
            'warehouse': False
        }

        class Response:
            text = (Path(self.data_dir) / "tensorflow.html").read_text()
            status_code = 200

            @staticmethod
            def raise_for_status():
                pass

        flexmock(requests)\
            .should_receive('get')\
            .with_args(source_info['url'] + '/tensorflow', verify=source_info['verify_ssl'])\
            .and_return(Response)

        source = Source.from_dict(source_info)
        assert set(source.get_package_versions('tensorflow')) == {
            '0.12.1',
            '1.3.0rc1',
            '1.0.0',
            '0.12.0rc1',
            '1.1.0',
            '1.3.0rc0',
            '0.12.0rc0',
            '1.2.0',
            '1.0.1',
            '1.2.0rc2',
            '1.1.0rc0',
            '1.1.0rc1',
            '0.12.0',
            '1.1.0rc2',
            '1.2.0rc1',
            '1.2.1',
            '1.2.0rc0'
        }

