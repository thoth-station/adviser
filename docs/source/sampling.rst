.. _sampling:

Random state space sampling
---------------------------

This simple predictor, named :class:`Sampling
<thoth.adviser.predictors.Sampling>`, performs a random sampling of
the state space, respecting the state space restrictions in :class:`Beam
<thoth.adviser.beam.Beam>`. It's mostly suitable for dealing with `cold start
problem <https://en.wikipedia.org/wiki/Cold_start_(computing)>`_.
