#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 - 2021 Fridolin Pokorny
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

"""Test a boot that checks for Pipfile hash and reports any mismatch to users.."""

from thoth.adviser.boots import PipfileHashBoot
from thoth.adviser.context import Context
from thoth.python import Project
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from ..base import AdviserUnitTestCase


class TestPipifleHashBoot(AdviserUnitTestCase):
    """Test a boot that checks for Pipfile hash and reports any mismatch to users.."""

    UNIT_TESTED = PipfileHashBoot

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        self.verify_multiple_should_include(builder_context)

    def test_no_include_no_pipenv_files(self, builder_context: PipelineBuilderContext) -> None:
        """Test if Pipenv files are not supplied - no hash is available to check against."""
        requirements_in = str(self.data_dir / "projects" / "requirements.in")
        requirements_txt = str(self.data_dir / "projects" / "requirements.txt")

        project = Project.from_pip_compile_files(
            requirements_path=requirements_in,
            requirements_lock_path=requirements_txt,
        )

        builder_context.project = project
        assert list(self.UNIT_TESTED.should_include(builder_context)) == []

    def test_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Test registering this unit."""
        assert list(self.UNIT_TESTED.should_include(builder_context)) == [{}]

    def test_run_hash_match(self, context: Context) -> None:
        """Test no stack info addition if hash mismatches."""
        assert not context.stack_info

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.run()

        assert len(context.stack_info) == 0
        assert context.stack_info == []

    def test_run_hash_mismatch(self, context: Context) -> None:
        """Test adding stack info if hash matches."""
        assert not context.stack_info
        context.project.pipfile_lock.meta.hash["sha256"] = "foo"

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.run()

        assert len(context.stack_info) == 2
        assert set(context.stack_info[0].keys()) == {"link", "message", "type"}
        assert context.stack_info[0]["message"] == (
            "Pipfile hash stated in the Pipfile.lock (foo) does not correspond to the "
            "hash computed (001e85) - was Pipfile adjusted?"
        )

        assert set(context.stack_info[1].keys()) == {"link", "message", "type"}
        assert (
            context.stack_info[1]["message"]
            == "Detected changes in the lock file invalidate using user's stack as a base"
        )
        assert self.verify_justification_schema(context.stack_info)

    def test_run_dev(self, context: Context) -> None:
        """Test discarding user's lock file if development dependencies are not present in lock but provided."""
        pipfile = str(self.data_dir / "projects" / "dev" / "Pipfile")
        pipfile_lock = str(self.data_dir / "projects" / "dev" / "Pipfile.lock")

        project = Project.from_files(pipfile_path=pipfile, pipfile_lock_path=pipfile_lock)

        assert project.pipfile.dev_packages.packages
        assert project.pipfile_lock.dev_packages.packages

        # Remove packages.
        project.pipfile_lock.dev_packages.packages.clear()
        context.cli_parameters["dev"] = True

        context.project = project

        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.run()

        assert project.pipfile.dev_packages.packages
        assert not project.pipfile_lock, "Lock file was not removed from the input"
        assert len(context.stack_info) == 1
        assert self.verify_justification_schema(context.stack_info)

    def test_run_dev_no_dev(self, context: Context) -> None:
        """Test discarding user's lock file if development dependencies are present but no --dev flag provided."""
        pipfile = str(self.data_dir / "projects" / "dev" / "Pipfile")
        pipfile_lock = str(self.data_dir / "projects" / "dev" / "Pipfile.lock")

        project = Project.from_files(pipfile_path=pipfile, pipfile_lock_path=pipfile_lock)

        assert project.pipfile.dev_packages.packages
        assert project.pipfile_lock.dev_packages.packages

        context.cli_parameters["dev"] = False
        context.project = project
        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.run()

        assert project.pipfile.dev_packages.packages
        assert not project.pipfile_lock, "Lock file was not removed from the input"
        assert len(context.stack_info) == 1
        assert self.verify_justification_schema(context.stack_info)

    def test_run_dev_noop(self, context: Context) -> None:
        """Test not discarding user's lock file if development dependencies are present in lock."""
        pipfile = str(self.data_dir / "projects" / "dev" / "Pipfile")
        pipfile_lock = str(self.data_dir / "projects" / "dev" / "Pipfile.lock")

        project = Project.from_files(pipfile_path=pipfile, pipfile_lock_path=pipfile_lock)

        assert project.pipfile.dev_packages.packages
        assert project.pipfile_lock.dev_packages.packages

        context.project = project
        context.cli_parameters["dev"] = True
        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.run()

        assert project.pipfile.dev_packages.packages
        assert project.pipfile_lock
        assert project.pipfile_lock.dev_packages.packages
        assert len(context.stack_info) == 0

    def test_run_dev_noop_no_dev(self, context: Context) -> None:
        """Test not discarding user's lock file if development dependencies are present in lock."""
        pipfile = str(self.data_dir / "projects" / "dev" / "Pipfile")
        pipfile_lock = str(self.data_dir / "projects" / "dev" / "Pipfile.lock")

        project = Project.from_files(pipfile_path=pipfile, pipfile_lock_path=pipfile_lock)

        assert project.pipfile.dev_packages.packages
        assert project.pipfile_lock.dev_packages.packages

        context.project = project
        project.pipfile_lock.dev_packages.packages.clear()
        context.cli_parameters["dev"] = False
        unit = self.UNIT_TESTED()
        with unit.assigned_context(context):
            unit.run()

        assert project.pipfile.dev_packages.packages
        assert project.pipfile_lock
        assert len(context.stack_info) == 0
