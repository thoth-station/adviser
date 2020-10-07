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

"""Test implementation of Neural Network (NN) based predictor."""

import math
import numpy as np

import flexmock
import pytest

from thoth.adviser.state import State
from thoth.adviser.context import Context
from thoth.adviser.predictors import NN
from thoth.adviser.predictors import TemporalDifference
import thoth.adviser.predictors.mcts as mcts_module

from ..base import AdviserTestCase


class TestNN(AdviserTestCase):
    """Test implementation of Neural Network based predictor."""

    def test_init(self) -> None:
        """Test the initialization part."""
        predictor = NN()
        assert predictor._next_state is None
        assert predictor._model is None
        assert predictor._model_input_size == 0
        assert predictor._optimizer is None
        assert predictor._loss_fn is None
        assert predictor._train_acc_metric is None
        assert predictor._loss_history == []
        assert predictor._package_mapping == {}

    def test_pre_run(self) -> None:
        """Test calling pre-run for the initialization part."""
        predictor = NN()
        predictor._create_model(100)
        predictor._next_state = flexmock()
        assert predictor._model is not None
        assert predictor._model_input_size == 100
        assert predictor._optimizer is not None
        assert predictor._loss_fn is not None
        assert predictor._train_acc_metric is not None
        assert predictor._loss_history == []
        predictor._loss_history.append(0.123)
        assert predictor._package_mapping == {}
        predictor._package_mapping == {"foo": "bar"}

        predictor.pre_run()
        assert predictor._next_state is None
        assert predictor._model is None
        assert predictor._model_input_size == 0
        assert predictor._optimizer is None
        assert predictor._loss_fn is None
        assert predictor._train_acc_metric is None
        assert predictor._loss_history == []
        assert predictor._package_mapping == {}

    def test_state2vector(self) -> None:
        """Test converting state to a vector."""
        state = State()
        state.add_resolved_dependency(("tensorflow", "2.2.0", "https://pypi.org/simple"))
        state.add_resolved_dependency(("flask", "1.1.2", "https://pypi.org/simple"))
        state.add_resolved_dependency(("selinon", "1.0.0", "https://pypi.org/simple"))
        state.add_resolved_dependency(("micropipenv", "1.0.0", "https://pypi.org/simple"))

        predictor = NN()
        predictor._model_input_size = 5

        predictor._package_mapping = {
            "tensorflow": {
                ("tensorflow", "2.0.0", "https://pypi.org/simple"): (0, 1),
                ("tensorflow", "2.2.0", "https://pypi.org/simple"): (0, 2),
            },
            "flask": {("flask", "1.1.2", "https://pypi.org/simple"): (1, 1),},
            "selinon": {("selinon", "0.1.0", "https://pypi.org/simple"): (2, 1),},
        }

        vector = predictor._state2vector(state)

        assert predictor._package_mapping == {
            "tensorflow": {
                ("tensorflow", "2.0.0", "https://pypi.org/simple"): (0, 1),
                ("tensorflow", "2.2.0", "https://pypi.org/simple"): (0, 2),
            },
            "flask": {("flask", "1.1.2", "https://pypi.org/simple"): (1, 1),},
            "selinon": {
                ("selinon", "0.1.0", "https://pypi.org/simple"): (2, 1),
                ("selinon", "1.0.0", "https://pypi.org/simple"): (2, 2),
            },
            "micropipenv": {("micropipenv", "1.0.0", "https://pypi.org/simple"): (3, 1),},
        }

        assert len(vector) == 5
        assert np.array_equal(vector, np.array([2, 1, 2, 1, 0]))

    def _test_set_reward_signal_nan(self) -> None:
        """Test the reward signal if no new state was generated."""

    def _test_set_reward_signal(self) -> None:
        """Test the reward signal if a new state was generated."""

    def _test_set_reward_signal_inf(self) -> None:
        """Test the reward signal if a final state was generated."""
