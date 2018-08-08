#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
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

"""Test enumerations present in the recommendation engine."""

import pytest

from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import PythonRecommendationOutput
from thoth.adviser.enums import Ecosystem


def test_recommendation_type_enum():
    assert RecommendationType.by_name('stable') == RecommendationType.STABLE
    assert RecommendationType.by_name('testing') == RecommendationType.TESTING
    assert RecommendationType.by_name('latest') == RecommendationType.LATEST

    with pytest.raises(ValueError):
        RecommendationType.by_name('unknown')

    assert len(RecommendationType) == 3


def test_python_recommendation_output_enum():
    assert PythonRecommendationOutput.by_name('pipenv') == PythonRecommendationOutput.PIPENV
    assert PythonRecommendationOutput.by_name('requirements') == PythonRecommendationOutput.REQUIREMENTS
    assert len(PythonRecommendationOutput) == 2


def test_ecosystem_enum():
    assert Ecosystem.by_name('python') == Ecosystem.PYTHON
    assert len(Ecosystem) == 1
