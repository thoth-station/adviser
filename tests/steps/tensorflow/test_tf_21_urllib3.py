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

"""Test TensorFlow 2.1 urllib3 step."""

import flexmock
import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.steps import TensorFlow21Urllib3Step
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlow21Urllib32Step(AdviserUnitTestCase):
    """Test a step that suggests not to use TensorFlow 2.1 as issues with six were spotted on imports."""

    UNIT_TESTED = TensorFlow21Urllib3Step

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize(
        "urllib3_version,tf_version",
        [("1.2", "2.1"), ("1.2.1", "2.1.1"), ("1.2.2", "2.1.0"), ("1.3", "2.1"), ("1.4", "2.1"), ("1.5", "2.1.dev")],
    )
    def test_tf_21(self, context: Context, urllib3_version: str, tf_version: str) -> None:
        """Test penalizing TensorFlow in version 2.1."""
        tf_package_version = PackageVersion(
            name="tensorflow",
            version=f"=={tf_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        urllib3_package_version = PackageVersion(
            name="urllib3",
            version=f"=={urllib3_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        state.resolved_dependencies["tensorflow"] = tf_package_version.to_tuple()

        assert not context.stack_info

        with TensorFlow21Urllib3Step.assigned_context(context):
            unit = TensorFlow21Urllib3Step()
            unit.pre_run()
            assert unit._message_logged is False
            with pytest.raises(NotAcceptable):
                assert unit.run(state, urllib3_package_version)
                assert unit._message_logged is True

        assert context.stack_info
        assert self.verify_justification_schema(context.stack_info)

    @pytest.mark.parametrize("urllib3_version,tf_version", [("1.2", "2.2.0"), ("1.25.10", "2.1")])
    def test_no_tf_21(self, urllib3_version: str, tf_version: str) -> None:
        """Test no penalization for TensorFlow other than 2.1 by this pipeline step."""
        urllib3_package_version = PackageVersion(
            name="urllib3",
            version=f"=={urllib3_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        tf_package_version = PackageVersion(
            name="tensorflow",
            version=f"=={tf_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        state.resolved_dependencies["tensorflow"] = tf_package_version.to_tuple()

        # Context is not used during the actual pipeline run.
        context = flexmock()
        with TensorFlow21Urllib3Step.assigned_context(context):
            unit = TensorFlow21Urllib3Step()
            assert unit.run(state, urllib3_package_version) is None
