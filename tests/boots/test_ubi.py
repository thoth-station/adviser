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

"""Test UBI to RHEL mapping boot."""

import flexmock

from thoth.adviser.boots import UbiBoot
from thoth.python import Project

from ..base import AdviserTestCase


class TestUbiBoot(AdviserTestCase):
    """Test UBI to RHEL mapping boot."""

    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"
"""

    def test_rhel_assign(self) -> None:
        """Test remapping UBI to RHEL."""
        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE))
        context.project.runtime_environment.operating_system.name = "ubi"

        boot = UbiBoot()
        with UbiBoot.assigned_context(context):
            boot.run()

        assert context.project.runtime_environment.operating_system.name == "rhel"

    def test_no_rhel_assign(self) -> None:
        """Test no change made if operating system is not UBI."""
        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE))
        context.project.runtime_environment.operating_system.name = "fedora"

        boot = UbiBoot()
        with UbiBoot.assigned_context(context):
            boot.run()

        assert context.project.runtime_environment.operating_system.name == "fedora"
