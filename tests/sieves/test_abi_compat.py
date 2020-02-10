#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Kevin Postlethwait
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

"""Test filtering out Python Packages based on required and available ABI symbols."""

import pytest
import flexmock

from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.sieves import AbiCompatabilitySieve
from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.python import PackageVersion
from thoth.python import Source
from thoth.storages import GraphDatabase
from thoth.storages.exceptions import NotFoundError

from ..base import AdviserTestCase

system_symbols = ["GLIBC_2.0", "GLIBC_2.1", "GLIBC_2.2", "GLIBC_2.3", "GLIBC_2.4", "GLIBC_2.5", "GCC_3.4", "X_2.21"]
required_symbols_a = ["GLIBC_2.9"]
required_symbols_b = ["GLIBC_2.4"]


class TestAbiCompatSieve(AdviserTestCase):
    """Test filtering out packages based on enabled or disabled Python package index."""

    def test_abi_compat_symbols_present(self) -> None:
        source = Source("https://pypi.org/simple")
        package_version = PackageVersion(
            name="tensorflow", version="==1.9.0", index=source, develop=False
        )
        flexmock(GraphDatabase)
        GraphDatabase.should_call("get_analyzed_image_symbols_all").and_return(system_symbols).once()
        GraphDatabase.should_call("get_python_package_required_symbols").and_return(required_symbols_b).once()

        context = flexmock(graph=GraphDatabase())
        with AbiCompatabilitySieve.assigned_context(context):
            sieve = AbiCompatabilitySieve()
            assert list(sieve.run((p for p in [package_version]))) == [package_version]

    def test_abi_compat_symbols_not_present(self) -> None:
        source = Source("https://pypi.org/simple")
        package_version = PackageVersion(
            name="tensorflow", version="==1.9.0", index=source, develop=False
        )
        flexmock(GraphDatabase)
        GraphDatabase.should_call("get_analyzed_image_symbols_all").and_return(system_symbols).once()
        GraphDatabase.should_call("get_python_package_required_symbols").and_return(required_symbols_a).once()

        context = flexmock(graph=GraphDatabase())
        with AbiCompatabilitySieve.assigned_context(context):
            sieve = AbiCompatabilitySieve()
            assert list(sieve.run((p for p in [package_version]))) == []
