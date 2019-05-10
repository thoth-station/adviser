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

"""Test randomly pickling up a stack coming out of pipeline.."""

import random
import pytest

from thoth.adviser.python.pipeline import StrideContext
from thoth.adviser.python.pipeline.strides import RandomDecision
from thoth.adviser.python.pipeline.exceptions import StrideRemoveStack

from base import AdviserTestCase


class TestRandomDecision(AdviserTestCase):
    """Test randomly pickling up a stack coming out of pipeline.."""

    def test_accept(self):
        """Check that a stack is randomly accepted randomly (initialized with a seed)."""
        random.seed(9)  # David's constant seems to work here.
        try:
            step_context = StrideContext(
                [("tensorflow", "1.9.0", "https://thoth-station.ninja/simple")]
            )
            RandomDecision(
                project=None,
                graph=None,
                library_usage=None,
            ).run(step_context)
        finally:
            # Recover to make sure there is no "implicit" random configuration other steps as a side effect.
            random.seed(None)

    def test_reject(self):
        """Check that a stack is randomly rejected randomly (initialized with a seed)."""
        random.seed(
            42
        )  # This should be answer to all your questions, if not, you have a problem.
        try:
            step_context = StrideContext(
                [("tensorflow", "1.9.0", "https://thoth-station.ninja/simple")]
            )
            with pytest.raises(StrideRemoveStack):
                RandomDecision(
                    project=None,
                    graph=None,
                    library_usage=None,
                ).run(step_context)
        finally:
            # Recover to make sure there is no "implicit" random configuration other steps as a side effect.
            random.seed(None)
