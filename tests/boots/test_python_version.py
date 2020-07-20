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

"""Test boot for Python version assignment."""

import flexmock

from thoth.adviser.boots import PythonVersionBoot
from thoth.python import Project

from ..base import AdviserTestCase


class TestPythonVersionBoot(AdviserTestCase):
    """Test changes to runtime environment or configuration done with respect to configured Python."""

    _CASE_PIPFILE_NO_PYTHON = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"
"""

    _CASE_PIPFILE_PYTHON = """
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
tensorflow = "*"

[requires]
python_version = "3.6"
"""

    def test_no_python_config(self) -> None:
        """Test assigning Python version from Thoth's config file."""
        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE_PYTHON), stack_info=[])
        context.project.runtime_environment.operating_system.name = "rhel"
        context.project.runtime_environment.operating_system.version = "8"

        assert context.project.runtime_environment.python_version is None

        boot = PythonVersionBoot()
        with PythonVersionBoot.assigned_context(context):
            boot.run()

        assert context.project.runtime_environment.operating_system.name == "rhel"
        assert context.project.runtime_environment.operating_system.version == "8"
        assert context.project.runtime_environment.python_version == "3.6"
        assert context.stack_info == [
            {
                "Message": "No version of Python specified in the configuration, using "
                "Python version found in Pipfile: '3.6'",
                "type": "WARNING",
            },
        ]

    def test_no_python_pipfile(self) -> None:
        """Test assigning Python version from Pipfile."""
        context = flexmock(project=Project.from_strings(self._CASE_PIPFILE_NO_PYTHON), stack_info=[])
        context.project.runtime_environment.operating_system.name = "rhel"
        context.project.runtime_environment.operating_system.version = "8"
        context.project.runtime_environment.python_version = "3.6"

        boot = PythonVersionBoot()
        with PythonVersionBoot.assigned_context(context):
            boot.run()

        assert context.project.runtime_environment.operating_system.name == "rhel"
        assert context.project.runtime_environment.operating_system.version == "8"
        assert context.project.runtime_environment.python_version == "3.6"
        assert context.stack_info == [
            {
                "Message": "No version of Python specified explicitly, assigning the one "
                "found in Thoth's configuration: '3.6'",
                "type": "WARNING",
            }
        ]
