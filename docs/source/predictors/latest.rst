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

Check `termial random
<https://medium.com/@fridex/termial-random-for-prioritized-picking-an-item-from-a-list-a65a4f563224>`__
and `its optimized form
<https://medium.com/@fridex/optimizing-termial-random-by-removing-binomial-coefficient-e39b9ca7aaa3>`__
which is used to prioritize picking more recent releases considering version
specifier.
