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

import pytest

from thoth.adviser.python.pipeline import StrideContext
from thoth.adviser.python.pipeline.strides import ScoreFiltering
from thoth.adviser.python.pipeline.exceptions import StrideRemoveStack

from base import AdviserTestCase


class TestScoreFiltering(AdviserTestCase):
    """Test randomly pickling up a stack coming out of pipeline.."""

    def test_accept_first(self):
        """Test accepting the very first result with a specific score."""
        stride_context = StrideContext(
            [("selinon", "1.0.0", "https://pypi.org/simple")]
        )
        stride_context.adjust_score(0.02)  # Set some score.
        ScoreFiltering(
            graph=None,
            project=None,
            library_usage=None,
        ).run(stride_context)

    def test_reject_second(self):
        """Test accepting the very first result and rejecting a second one with same score."""
        stride_context = StrideContext(
            [("selinon", "1.0.0", "https://pypi.org/simple")]
        )
        stride_context.adjust_score(0.02)  # Set some score.
        score_filtering = ScoreFiltering(
            graph=None,
            project=None,
            library_usage=None,
        )

        # The first one should always pass.
        score_filtering.run(stride_context)

        stride_context = StrideContext([("celery", "1.0.0", "https://pypi.org/simple")])
        stride_context.adjust_score(0.02)  # Set to same score.
        with pytest.raises(StrideRemoveStack):
            score_filtering.run(stride_context)

        # Another score should pass again
        stride_context = StrideContext([("dask", "1.0.0", "https://pypi.org/simple")])
        stride_context.adjust_score(0.5451)
        score_filtering.run(stride_context)
