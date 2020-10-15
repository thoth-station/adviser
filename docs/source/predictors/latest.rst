.. _latest:

Approximating Latest predictor
------------------------------

This predictor is used when a "latest" software stack is requested. The
implementation always tries to resolve the latest software stack possible (all
the packages in their latest versions). If that's not possible given the
version range requirements in the dependency graph, predictor starts to perform
random "hops" across releases. This does not implement a proper backtracking
algorithm but rather approximates the latest software stack resolution.

The randomness introduced causes incompatibilities with pip/Pipenv/Poetry
resolver.
