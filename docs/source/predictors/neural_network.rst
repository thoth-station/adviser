.. _neural_network:

Using deep reinforcement learning in predictor
----------------------------------------------

.. note::

  Check :ref:`high level predictor docs <predictor>` for predictor basics.

Previous sections discuss about Markov decision process (MDP) and reinforcement
learning based dependency resolution that uses gradient-free methods. Naturally,
gradient based methods will be discussed next.

.. note::

  Gradient based methods are not used during the dependency resolution. This
  part of the documentation serves as a note to future ourselves.

The upcoming video demonstrates a spike that was made for a gradient based dependency resolution.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/XtuWGex0ync" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

In a nutshell, training a neural network during the resolution process seems to
be tricky especially considering how the state space behaves. As a set of
actions that are possible from a state are not constant and vary from state to
state, it is required to create a set of trajectories from the dependency graph
that basically sample how the resolution can look like. Then, it's possible to
use these trajectories to obtain a set of possible actions - packages and
package versions that can be resolved during the resolution process.
Trajectories are stored in a replay buffer as they keep information about
actions taken and reward signals obtained. The replay buffer is used to train a
neural network. Note the replay buffer needs to be shuffled not to provide
samples that depend on each other as an input to the neural network training.

The video proposes a neural network for regression. This architecture was made
during the experiment to reduce number of trainables by encoding the state and
actions on the input. It's also possible to use classification as well though.

Note the neural network needs to be created and trained during the resolution
process (considering the current case) and the input vector size as well as its
overall size is not known (opens "neural network meta-programming question
here"). Thus the neural network cannot be fine-tuned and subsequently pushed to
production.

The video above also discusses a use case where the neural network could be
more suitable than TD-learning or MCTS methods. If the knowledge base consists
of a lot of causal data (e.g. a reward signal obtained in the resolution
process depends on the presence of package X and Y while resolving package Z)
the neural network can learn this patterns and guide the resolution process to
better solutions. Otherwise, gradient-free methods sound like a better solution
(consider time and number of stacks that can be scored if gradient-free methods
are used in comparision to resource hungry and time consuming neural network
training).

If such causal data would be available in the future, the neural network does
not need to be trained during the resolution process as discussed. As such
causal data are known beforehand, the neural network (or other trainable
entity) can be trained prior to the resolution process and can be used on
dependency sub-graphs where it would guide the resolution process.  In other
words, the neural network would be trained on the causal data and would be used
during the resolution process as part of another predictor if the dependency
sub-graph for which it was trained is spotted during the resolution process. In
other cases, gradient-free methods can be used.
