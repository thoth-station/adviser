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

"""Test suggesting not to use TensorFlow 2.1 with h5py>=3."""

from itertools import product
import flexmock
import pytest

from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import NotAcceptable
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.steps import TensorFlow21H5pyStep
from thoth.python import PackageVersion
from thoth.python import Source

from ...base import AdviserUnitTestCase


class TestTensorFlow21H5PyStep(AdviserUnitTestCase):
    """Test suggesting not to use TensorFlow 2.1 with h5py>=3."""

    UNIT_TESTED = TensorFlow21H5pyStep

    def test_verify_multiple_should_include(self, builder_context: PipelineBuilderContext) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context.recommendation_type = RecommendationType.STABLE
        self.verify_multiple_should_include(builder_context)

    @pytest.mark.parametrize(
        "tf_version,h5py_version",
        list(product(("2.1.0", "2.1.1", "2.1.2"), ("3.0.0", "3.0.1", "4.0.0", "3.2.0"))),
    )
    def test_tf_21(self, context: Context, tf_version: str, h5py_version: str) -> None:
        """Test blocking resolution of h5py with TensorFlow==2.1."""
        tf_package_version = PackageVersion(
            name="tensorflow",
            version=f"=={tf_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        h5py_package_version = PackageVersion(
            name="h5py",
            version=f"=={h5py_version}",
            develop=False,
            index=Source("https://pypi.org/simple"),
        )

        state = State()
        state.resolved_dependencies["tensorflow"] = tf_package_version.to_tuple()

        assert not context.stack_info

        with self.UNIT_TESTED.assigned_context(context):
            unit = self.UNIT_TESTED()
            unit.pre_run()
            assert unit._message_logged is False
            with pytest.raises(NotAcceptable):
                unit.run(state, h5py_package_version)
            assert unit._message_logged is True

        assert context.stack_info
        assert self.verify_justification_schema(context.stack_info)

    @pytest.mark.parametrize("h5py_version,tf_version", [("2.9", "2.1.0"), ("3.0", "2.3")])
    def test_no_tf_21(self, h5py_version: str, tf_version: str) -> None:
        """Test no blocking when using h5py<3 or TensorFlow!=2.1."""
        h5py_package_version = PackageVersion(
            name="h5py",
            version=f"=={h5py_version}",
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
        with self.UNIT_TESTED.assigned_context(context):
            unit = self.UNIT_TESTED()
            assert unit.run(state, h5py_package_version) is None
