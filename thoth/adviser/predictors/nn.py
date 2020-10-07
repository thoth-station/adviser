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

"""Implementation of a predictor based on a neural network (NN) with adaptive simulating annealing.

The adaptive simulated annealing part (ASA) is used to balance exploration and exploitation.
"""

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
import logging
import math
import random

import attr
import numpy as np
import os
import matplotlib
from matplotlib import pyplot as plt

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # TODO: move to manifest
import tensorflow as tf

from thoth.adviser.predictor import Predictor
from thoth.adviser.state import State
from thoth.adviser.exceptions import NoHistoryKept

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class NN(Predictor):
    """Implementation of a predictor based on a Neural Network."""

    learning_rate = attr.ib(type=float, default=1e-6, init=True)
    train_epochs = attr.ib(type=int, default=2, init=True)
    batch_size = attr.ib(type=int, default=64, init=True)

    _last_score = attr.ib(type=float, default=0.0, init=False)
    _next_state = attr.ib(type=Optional[State], default=None, init=False)
    _model = attr.ib(type=Optional[tf.keras.Model], default=None)
    _model_input_size = attr.ib(type=int, default=0)
    _optimizer = attr.ib(type=Optional[tf.keras.optimizers.SGD], default=None)
    _loss_fn = attr.ib(type=Optional[tf.keras.losses.MeanSquaredError], default=None)
    _train_acc_metric = attr.ib(type=Optional[tf.keras.metrics.MeanAbsoluteError], default=None)
    _loss_history = attr.ib(type=List, factory=list, init=False)
    # Mapping for package_name to package tuple that maps to a tuple of ints (input layer node idx, package idx/value)
    _package_mapping = attr.ib(type=Dict[str, Dict[Tuple[str, str, str], Tuple[int, int]]], factory=dict, init=False)
    _exploration_phase = attr.ib(type=bool, default=True, init=False)
    _exploration_data = attr.ib(factory=list, init=False)

    def _state2vector(self, resolved_dependencies: dict, *, learning: bool = True) -> np.array:
        """Convert state to a list of ints suitable to be passed to the neural network as input."""
        vector = np.zeros(shape=(self._model_input_size,), dtype=np.int16)
        for package_tuple in resolved_dependencies.values():
            node_idx, package_idx = self._mark_package_tuple_vector(package_tuple, learning=learning)
            vector[node_idx] = package_idx

        return vector

    def _mark_package_tuple_vector(self, package_tuple: Tuple[str, str, str], *, learning: bool = True) -> Tuple[int, int]:
        """Mark the given package in the vector."""
        packages_mapped = self._package_mapping.get(package_tuple[0])
        if packages_mapped is None and not learning:
            return len(self._package_mapping), 1
        elif packages_mapped is None:
            node_idx = len(self._package_mapping)
            self._package_mapping[package_tuple[0]] = {package_tuple: (node_idx, 1)}
            return node_idx, 1
        else:
            package_tuple_mapped = packages_mapped.get(package_tuple)
            if package_tuple_mapped is not None:
                return package_tuple_mapped[0], package_tuple_mapped[1]
            elif package_tuple is None and not learning:
                return len(self._package_mapping), 1
            else:
                node_idx = next(iter(packages_mapped.values()))[0]
                package_idx = len(packages_mapped) + 1
                self._package_mapping[package_tuple[0]][package_tuple] = node_idx, package_idx
                return node_idx, package_idx

    def _create_model(self) -> tf.keras.Model:
        """Create model given the parameters provided."""
        assert self._model is None, "Model already created"

        self._model = tf.keras.Sequential(
            [
                tf.keras.Input(shape=(self._model_input_size,), name="inputs"),
                tf.keras.layers.Dense(
                    self._model_input_size,
                    activation="relu",
                    name="dense_1",
                ),
                tf.keras.layers.Dense(
                    self._model_input_size,
                    activation="relu",
                    name="dense_2",
                ),
                tf.keras.layers.Dense(1, name="prediction", activation="linear"),
            ]
        )

        if _LOGGER.getEffectiveLevel() <= logging.INFO:
            self._model.summary(print_fn=_LOGGER.info)

        self._optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
        self._loss_fn = tf.keras.losses.MeanSquaredError()
        self._train_acc_metric = tf.keras.metrics.MeanAbsoluteError()

    @staticmethod
    @tf.function
    def _train_step(
        model: tf.keras.Model,
        optimizer: tf.keras.optimizers.SGD,
        loss_fn: tf.keras.losses.MeanSquaredError,
        train_acc_metric: tf.keras.metrics.SparseCategoricalAccuracy,
        x: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """Train the given NN by performing a single step.

        This function is marked as tf.function to enable graph optimizations in TF.
        """
        with tf.GradientTape() as tape:
            logits = model(x, training=True)
            loss_value = loss_fn(y, logits)

        grads = tape.gradient(loss_value, model.trainable_weights)
        optimizer.apply_gradients(zip(grads, model.trainable_weights))
        train_acc_metric.update_state(y, logits)
        return loss_value

    def pre_run(self) -> None:
        """Initialize pre-running of this predictor."""
        self._next_state = None
        self._model = None
        self._model_input_size = 0
        self._optimizer = None
        self._loss_fn = None
        self._train_acc_metric = None
        self._loss_history.clear()
        # self._package_mapping.clear()
        self._exploration_phase = True
        self._exploration_data.clear()
        super().pre_run()

    def set_reward_signal(self, state: State, package_tuple: Tuple[str, str, str], reward: float) -> None:
        """Note down reward signal of the last action performed."""
        if self._exploration_phase and math.isinf(reward):
            # Check if the exploration phase should end.
            # if self.context.accepted_final_states_count > self.context.limit - (self.context.limit >> 3):
            if self.context.accepted_final_states_count >= self.context.limit - 1:
                _LOGGER.warning("Exploration phase has ended...")
                self._exploration_phase = False
                self._on_exploration_phase_end()

            self._exploration_data.append((state.resolved_dependencies.copy(), self._last_score - state.score))
            return
        elif self._exploration_phase and not math.isnan(reward):
            # Store exploration data to buffer for later training - perform copy due to reuse
            # state optimizations in beam.
            self._exploration_data.append((state.resolved_dependencies.copy(), reward))
            return

        print("Obtained: {:+g}".format(reward))
        if math.isinf(reward):
            print("Final score: ", state.score)
        # TODO: replay buffer?!
        return

    def _plot(self) -> matplotlib.figure.Figure:
        """Plot model's loss history."""
        if self._loss_history is None:
            raise NoHistoryKept("No history datapoints kept")

        plt.plot(self._loss_history)
        plt.title("Model loss")
        plt.xlabel("iteration")
        plt.legend(["loss"], loc="upper right")
        return plt.figure(1)

    def _on_exploration_phase_end(self) -> None:
        """Finish exploration phase."""
        # Approximate input size.
        packages_seen = set()
        random.shuffle(self._exploration_data)
        for resolved_dependencies, _ in self._exploration_data:
            packages_seen.update(resolved_dependencies.keys())

        # Add a "sink" input that is used in exploitation phase for packages not seen during the exploration phase.
        self._model_input_size = len(packages_seen) + 1
        _LOGGER.info("Trained neural network will have %d inputs", self._model_input_size)

        # Construct model.
        _LOGGER.info("Building the neural network...")
        self._create_model()

        _LOGGER.info("Training the neural network...")
        # Train with exploration data.
        x_train = []
        y_train = []
        for resolved_dependencies, reward in self._exploration_data:
            x = self._state2vector(resolved_dependencies, learning=True)
            x_train.append(np.reshape(x, (-1, self._model_input_size)))
            y_train.append(np.array([reward]))

        log_step = len(x_train) // 10
        self.batch_size = 1
        train_data = tf.data.Dataset.from_tensor_slices((x_train, y_train))

        for epoch in range(self.train_epochs):
            # for epoch in range(1):
            # Iterate over the batches of the dataset.
            for step, (x_batch_train, y_batch_train) in enumerate(train_data):
                loss_value = self._train_step(
                    self._model, self._optimizer, self._loss_fn, self._train_acc_metric, x_batch_train, y_batch_train
                )

                if self.keep_history:
                    self._loss_history.append(float(loss_value))

                if step % log_step == 0:
                    _LOGGER.info(
                        "Training loss in epoch %d at step %d (samples seen: %d): %g",
                        epoch,
                        step,
                        ((step + 1) * self.batch_size),
                        float(loss_value)
                    )

            # Display metrics at the end of each epoch.
            train_acc = self._train_acc_metric.result()
            _LOGGER.info("Training acc over epoch: %g" % (float(train_acc),))

            # Reset training metrics at the end of each epoch
            self._train_acc_metric.reset_states()

        # No need to keep data.
        # self._exploration_data.clear()

    def _run_random_walk(self) -> Tuple[State, Tuple[str, str, str]]:
        """Perform a random walk during the exploration phase."""
        state = self.context.beam.get_last()
        if state is None:
            state = self.context.beam.get_random()

        self._last_score = state.score
        return state, state.get_random_unresolved_dependency(prefer_recent=True)

    def run(self) -> Tuple[State, Tuple[str, str, str]]:
        """Predict next state based on a Neural Network.

        The prediction phase (exploitation) is after training (exploration).
        """
        if self._exploration_phase:
            return self._run_random_walk()

        from thoth.adviser.exceptions import EagerStopPipeline
        raise EagerStopPipeline

        state = self.context.beam.max()
        state_vector = self._state2vector(state.resolved_dependencies, learning=False)
        # np.reshape(state_vector, (-1, self._model_input_size))
        to_resolve_tuple = None
        to_resolve_tuple_prediction = -1000.0
        print("New run call")
        for unresolved_dependencies in state.unresolved_dependencies.values():
            for unresolved_dependency in unresolved_dependencies.values():
                node_idx, package_idx = self._mark_package_tuple_vector(unresolved_dependency, learning=False)
                assert not state_vector[node_idx]
                state_vector[node_idx] = package_idx
                print(node_idx, package_idx)
                print(state_vector)
                prediction = self._model.predict(np.array([state_vector]))[0][0]
                print("  prediction for ", unresolved_dependency, " is ", prediction)
                state_vector[node_idx] = 0
                if prediction > to_resolve_tuple_prediction:
                    to_resolve_tuple = unresolved_dependency
                    to_resolve_tuple_prediction = prediction

        print("Predicted: ", to_resolve_tuple, "prediction: ", to_resolve_tuple_prediction)
        return state, to_resolve_tuple

    def post_run(self) -> None:
        import pickle

        with open("exploration_data.pickle", "wb") as f:
            pickle.dump(self._exploration_data, f)

        self._model.save("model. bin")

        with open("package_mapping.pickle", "wb") as f:
            pickle.dump(self._package_mapping, f)
