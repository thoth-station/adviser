#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
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

"""Test changes to RHEL version for major RHEL releases."""

import flexmock

from thoth.adviser.boots import RHELVersionBoot
from thoth.python import Project

from ..base import AdviserTestCase


class TestRHELVersionBoot(AdviserTestCase):
    """Test changes to RHEL version for major RHEL releases."""

    _CASE_PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"
"""

    def test_version_change(self) -> None:
        """Test changing RHEL version to its major version."""
        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE))
        context.project.runtime_environment.operating_system.name = "rhel"
        context.project.runtime_environment.operating_system.version = "8.1"

        boot = RHELVersionBoot()
        with RHELVersionBoot.assigned_context(context):
            boot.run()

        assert context.project.runtime_environment.operating_system.name == "rhel"
        assert context.project.runtime_environment.operating_system.version == "8"

    def test_version_no_change_no_os_match(self) -> None:
        """Test no change to RHEL version identifier if OS does not match."""
        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE))
        context.project.runtime_environment.operating_system.name = "fedora"
        context.project.runtime_environment.operating_system.version = "31"

        boot = RHELVersionBoot()
        with RHELVersionBoot.assigned_context(context):
            boot.run()

        assert context.project.runtime_environment.operating_system.name == "fedora"
        assert context.project.runtime_environment.operating_system.version == "31"

    def test_version_no_change_no_version(self) -> None:
        """Test no change to RHEL version identifier if OS version was not supplied."""
        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE))
        context.project.runtime_environment.operating_system.name = "rhel"
        context.project.runtime_environment.operating_system.version = None

        boot = RHELVersionBoot()
        with RHELVersionBoot.assigned_context(context):
            boot.run()

        assert context.project.runtime_environment.operating_system.name == "rhel"
        assert context.project.runtime_environment.operating_system.version is None
