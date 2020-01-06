#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""Test dropout step."""

import random
import pytest

from thoth.adviser.steps import DropoutStep
from thoth.adviser.exceptions import NotAcceptable

from ..base import AdviserTestCase


class TestDropoutStep(AdviserTestCase):
    """Test dropout step."""

    def test_run_accept(self) -> None:
        """Test accepting a new state."""
        step = DropoutStep()

        old_state = random.getstate()
        random.seed(42)
        try:
            assert step.run(None, None) is None
        finally:
            random.setstate(old_state)

    def test_run_no_accept(self) -> None:
        """Test accepting not accepting a new state."""
        step = DropoutStep()

        old_state = random.getstate()
        random.seed(2)
        try:
            with pytest.raises(NotAcceptable):
                step.run(None, None)
        finally:
            random.setstate(old_state)

    def test_default_configuration(self) -> None:
        """Test default configuration of dropout pipeline step."""
        assert DropoutStep.CONFIGURATION_DEFAULT == {"probability": 0.9}
