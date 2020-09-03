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

"""Test implementation of a predictor used to generate package combinations faster."""

import pytest

from thoth.adviser.predictors import PackageCombinations

from ..base import AdviserTestCase


class TestPackageCombinations(AdviserTestCase):
    """Test implementation of a predictor used to generate package combinations faster."""

    def test_pre_run_error(self) -> None:
        """Test pre-run initialization failure."""
        predictor = PackageCombinations()
        with pytest.raises(ValueError, match="No package combinations supplied to the predictor"):
            predictor.pre_run()

        predictor = PackageCombinations(package_combinations=[])
        with pytest.raises(ValueError, match="No package combinations supplied to the predictor"):
            predictor.pre_run()

    def test_pre_run(self) -> None:
        """Test pre-run initialization."""
        predictor = PackageCombinations(package_combinations=["tensorflow", "numpy"])
        assert isinstance(predictor.package_combinations, set)
        assert predictor.package_combinations == {"tensorflow", "numpy"}
