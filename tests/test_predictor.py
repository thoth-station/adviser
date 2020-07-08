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

"""Test predictor and its core functionality."""

import os
import flexmock
import pytest

from .base import AdviserTestCase


class TestPredictor(AdviserTestCase):
    """Test predictor's core functionality."""

    def test_keep_temperature_history_init(self, predictor_mock_class: type) -> None:
        """Test initialization of temperature history."""
        assert "THOTH_ADVISER_NO_HISTORY" not in os.environ
        predictor = predictor_mock_class()
        assert predictor.keep_history is True, "Temperature history not kept by default"

        flexmock(os)
        os.should_receive("getenv").with_args("THOTH_ADVISER_NO_HISTORY", 0).and_return("0").and_return("1").twice()

        predictor = predictor_mock_class()
        assert predictor.keep_history is True

        predictor = predictor_mock_class()
        assert predictor.keep_history is False

    def test_assign_context(self, predictor_mock_class: type) -> None:
        """Test assigning context to predictor."""
        predictor = predictor_mock_class()
        with pytest.raises(ValueError):
            predictor.context

        context = flexmock()
        with predictor.assigned_context(context):
            assert predictor.context is context
