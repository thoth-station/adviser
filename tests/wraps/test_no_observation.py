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

"""Test wrap adding information about no justification."""

from thoth.adviser.state import State
from thoth.adviser.wraps import NoObservationWrap

from ..base import AdviserTestCase


class TestNoObservationWrap(AdviserTestCase):
    """Test dropout step."""

    def test_run_justification_noop(self) -> None:
        """Test no operation when justification is present."""
        state = State()
        assert not state.justification

        state.add_justification([{"type": "INFO", "message": "Foo bar"}])

        unit = NoObservationWrap()
        unit.run(state)

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message"}
        assert state.justification[0]["type"] == "INFO"

    def test_run_no_justification(self) -> None:
        """Test adding information about justification."""
        state = State()
        assert not state.justification

        unit = NoObservationWrap()
        unit.run(state)

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message"}
        assert state.justification[0]["type"] == "INFO"
