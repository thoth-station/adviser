#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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

"""Test randomly pickling up a stack coming out of pipeline.."""

import random
import pytest

from thoth.adviser.exceptions import NotAcceptable  # type: ignore
from thoth.adviser.state import State  # type: ignore
from thoth.adviser.strides import RandomDecisionStride

from ..base import AdviserUnitTestCase


class TestRandomDecision(AdviserUnitTestCase):
    """Test randomly pickling up a stack coming out of pipeline.."""

    UNIT_TESTED = RandomDecisionStride

    @pytest.mark.skip(reason="Stride for random decision is never registered.")
    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""

    def test_accept(self) -> None:
        """Check that a stack is randomly accepted randomly (initialized with a seed)."""
        # David's constant seems to work here.
        random_state = random.getstate()
        random.seed(9)
        try:
            stride = RandomDecisionStride()
            assert stride.run(None) is None
        finally:
            # Recover to make sure there is no "implicit" random configuration other steps as a side effect.
            random.setstate(random_state)

    def test_reject(self) -> None:
        """Check that a stack is randomly rejected randomly (initialized with a seed)."""
        # This should be answer to all your questions, if not, you have a problem.
        random_state = random.getstate()
        random.seed(42)
        try:
            stride = RandomDecisionStride()
            with pytest.raises(NotAcceptable):
                stride.run(State(score=666.0))
        finally:
            # Recover to make sure there is no "implicit" random configuration other steps as a side effect.
            random.setstate(random_state)
