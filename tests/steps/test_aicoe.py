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

"""A test for prioritizing releases from AICoE."""

import flexmock

from thoth.adviser.steps import AICoEReleasesStep
from thoth.python import PackageVersion
from thoth.python import Source

from ..base import AdviserTestCase


class TestAICoEReleasesStep(AdviserTestCase):
    """A test for prioritizing releases from AICoE."""

    def test_aicoe_release(self) -> None:
        """Make sure an AICoE release affects stack score."""
        package_version = PackageVersion(
            name="tensorflow",
            version="==2.0.0",
            index=Source("https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple"),
            develop=False,
        )

        context = flexmock()
        with AICoEReleasesStep.assigned_context(context):
            step = AICoEReleasesStep()
            result = step.run(None, package_version)

        assert result is not None
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], float)
        assert 0.0 < result[0] < 1.0
        assert isinstance(result[1], list)
        assert len(result[1]) == 1
        assert isinstance(result[1][0], dict)
        assert result[1][0].get("type") == "INFO"
        assert result[1][0].get("message"), "No message for user produced"

    def test_no_aicoe_release(self) -> None:
        """Make sure the stack score is untouched if not an AICoE release."""
        package_version = PackageVersion(
            name="tensorflow", version="==2.0.0", index=Source("https://pypi.org/simple"), develop=False,
        )

        context = flexmock()
        with AICoEReleasesStep.assigned_context(context):
            step = AICoEReleasesStep()
            result = step.run(None, package_version)

        assert result is None
