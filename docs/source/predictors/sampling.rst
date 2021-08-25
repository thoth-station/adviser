.. _sampling:

Random state space sampling predictor
-------------------------------------

.. note::

  Check :ref:`high level predictor docs <predictor>` for predictor basics.

This simple predictor, named :class:`Sampling
<thoth.adviser.predictors.Sampling>`, performs a random sampling of
the state space, respecting the state space restrictions in :class:`Beam
<thoth.adviser.beam.Beam>` and direct dependencies of an application stack.
It's mostly suitable when dealing with `cold start problem
<https://en.wikipedia.org/wiki/Cold_start_(computing)>`_.

This predictor does not perform well for dependency graphs that are deep as it
can spend a lot of time in state expansion. See :ref:`random walk predictor
<random_walk>` as an alternative to this predictor.
