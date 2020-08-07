.. _rl:

Reinforcement learning driven resolution process
------------------------------------------------

As described in the introductory section, the whole resolution can be treated
as a :ref:`Markov Decision Process (MDP) <introduction_rl>` (see `MDP on
Wikipedia <https://en.wikipedia.org/wiki/Markov_decision_process>`__). Treating
the resolution process this way gave birth to implementations of predictors
that are based on reinforcement learning (RL), such as a predictor based on
Monte-Carlo tree search or another predictor based on Temporal Difference
(TD) learning.

MCTS based predictor as well as TD learning based predictor share core ideas
and concepts. As both RL algorithms expect an opponent in their basic
implementation, these algorithms had to be additionally adjusted to work well
in a resolution process. The main adjustment lies in balancing exploration and
exploitation as there is no "opponent" to play against (formulas like UCB1
cannot be easily applied).

Balancing exploration and exploitation in RL driven resolution process
======================================================================

Exploring the whole state space of all the possible software stacks can be time
and computationally intensive task. Given the size of software stacks for any
real world applications, it is often nearly impossible to explore the whole
state space in a reasonable time. Resolving all the stacks can result in billions
of combinations that are additionally scored.

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

Predictor based on Monte Carlo tree search
==========================================

The `MCTS <https://en.wikipedia.org/wiki/Monte_Carlo_tree_search>`__ based
predictor tries to resolve the whole stack and, if successful, learns policy
from :ref:`steps performed during the resolution process <steps>`.

Predictor based on Temporal Difference learning
===============================================

Another predictor, TD-learning based predictor, learns policy each time a
successful step is performed, even though it does not produce any final
state. This reduces bias, but, considering real world stacks, takes too much
time to produce final stacks in comparision to MCTS based predictor.
