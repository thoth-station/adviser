.. _hill_climbing:

Hill climbing predictor
-----------------------

.. note::

  Check :ref:`high level predictor docs <predictor>` for predictor basics.

Another simple predictor is based on an optimization technique called
:class:`hill climbing <thoth.adviser.predictors.HillClimbing>`
(see `Wikipedia <https://en.wikipedia.org/wiki/Hill_climbing>`_). As any
resolver, it respects the current :class:`beam size <thoth.adviser.beam.Beam>`
and always picks the best solution found so far.

The biggest advantages of this predictor are simplicity and speed. It can be
easily stuck in a local optima though.

The figure bellow shows hill climbing performed during resolution of a software
stack in a state space with random score assigned to packages. x-axis shows
resolver iterations and y-axis corresponds to scores computed. As can be seen,
the predictor does not learn state space characteristics to resolve software
stacks possibly `falling into a local optima
<https://en.wikipedia.org/wiki/Local_search_(optimization)>`__.  The score
gradually increases, taking always the top rated state from the beam.

.. image:: ../_static/hill_climbing.png
   :target: ../_static/hill_climbing.png
   :alt: An example of a history during hill climbing in adviser.
