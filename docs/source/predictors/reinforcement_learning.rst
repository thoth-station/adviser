.. _rl:

Reinforcement learning driven resolution process
------------------------------------------------

.. note::

  Check :ref:`high level predictor docs <predictor>` for predictor basics.

As described in the introductory section, the whole resolution can be treated
as a :ref:`Markov Decision Process (MDP) <introduction_rl>` (see `MDP on
Wikipedia <https://en.wikipedia.org/wiki/Markov_decision_process>`__). Treating
the resolution process this way gave birth to implementations of predictors
that are based on reinforcement learning (RL). The upcoming sections will
discuss gradient-free methods:

* :ref:`Monte Carlo Tree Search <mcts>` (also known as Monte Carlo learning)
* :ref:`Temporal Difference learning <temporal_difference_learning>` and its n-step variation

MCTS based predictor as well as TD learning based predictor share core ideas
and concepts. As both RL algorithms expect an opponent in their basic
implementation, these algorithms had to be additionally adjusted to work well
in a resolution process. The main adjustment lies in balancing exploration and
exploitation as there is no "opponent" to play against (formulas like UCB1
cannot be directly applied).

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/WEJ65Rvj3lc" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

.. _rl_balancing:

Balancing exploration and exploitation in RL driven resolution process
======================================================================

Exploring the whole state space of all the possible software stacks can be time
and computationally intensive task. Given the size of software stacks for any
real world applications, it is often nearly impossible to explore the whole
state space in a reasonable time. Resolving all the stacks can result in
billions of combinations that are additionally scored.

In these cases, the real opponent to play against is time. The idea of
temperature function from :ref:`adaptive simulated annealing <annealing>` was
used. The temperature function balances exploration and exploitation. If
the temperature drops to 0, only exploitation is done. Otherwise, exploration is
done with a certain probability of exploration given the current temperature
(the lower temperature is, the lower probability of exploration). The
temperature can take into account number of software stacks resolved so far,
number of software stacks to resolve, number of resolver rounds and other
internal attributes of resolver.

.. note::

  The temperature function can be plotted when ``--plot`` option is supplied to
  an adviser run.

See `this notebook that shows the resolution process using TD-learning
predictor
<https://github.com/thoth-station/notebooks/blob/master/notebooks/development/Gradient-free%20reinforcement%20learning%20predictors.ipynb>`__.
