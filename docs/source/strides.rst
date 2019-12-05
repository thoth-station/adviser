.. _strides:

Stride pipeline unit type
-------------------------

Once there are no more unresolved dependencies in the resolver state (no more
:ref:`steps <steps>` to be performed), such state becomes a "final state" (see
:ref:`introduction` for theoretical background). Pipeline units called
":class:`strides <thoth.adviser.stride.Stride>`" are then called on the given
final state to check whether the given final state should be accepted and
treated as one of the pipeline products.

Main usage
==========

* Decide whether the given fully resolved software stack should be accepted and
  be treated as one of the pipeline products

  * Raising exception :class:`NotAcceptable
    <thoth.adviser.exceptions.NotAcceptable>` will prevent from adding fully
    resolved (final) state to the pipeline products

* Prematurely end resolution based on the the final state reached

  * Raising exception :class:`EagerStopPipeline
    <thoth.adviser.exceptions.EagerStopPipeline>` will cause stopping the whole
    resolver run and causing resolver to return products computed so far

Real world examples
===================

* Filter out software stacks with same score in recommendations - most probably
  they include package-versions that do not differentiate resolved software
  stack quality

* To test TensorFlow with different versions of ``numpy`` in :ref:`Dependency
  Monkey <dependency_monkey>` a stride implementation can prevent from
  generating stacks that have same ``numpy`` version

* Do not accept stacks for :ref:`Dependency Monkey <dependency_monkey>` runs
  for which Thoth has observation already (for example performance related
  testing using `performance indicators
  <https://github.com/thoth-station/performance>`_)

* Randomly sample state space and run `Amun inspection jobs
  <https://github.com/thoth-station/amun-api>`_ to gather observations about
  Python ecosystem and packages present

An example implementation
=========================

.. code-block:: python

  from typing import Dict
  from typing import List
  from typing import Optional
  from typing import Tuple
  import random

  from thoth.adviser.exceptions import NotAcceptable
  from thoth.adviser import Stride
  from thoth.python import PackageVersion


  class StrideExample(Stride):
      """Flip a coin, heads discard the given state."""

      def run(self, state: State) -> None:
          """The main entry-point for stride implementation demonstration."""
          if bool(random.getrandbits(1)):
              raise NotAcceptable(
                  f"State with score {state.score!r} was randomly discarded by flipping a coin"
              )


The implementation can also provide other methods, such as :func:`Unit.pre_run
<thoth.adviser.unit.Unit.post_run>`, :func:`Unit.post_run
<thoth.adviser.unit.Unit.post_run>` or :func:`Unit.post_run_report
<thoth.adviser.unit.Unit.post_run>` and pipeline unit configuration adjustment.
See :ref:`unit documentation <unit>` for more info.
