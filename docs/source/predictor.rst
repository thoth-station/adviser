.. _predictor:

Predictor in Thoth's adviser
----------------------------

Two main components in Thoth's adviser are :ref:`Resolver <resolver>` and
Predictor. This section discusses about the latter one. Predictor abstraction
was introduced to guide resolver in expansion of states (performing steps until
a final state is reached). This guidance can have two main purposes:

* Expand states that are the most promising ones to be used by users - used for
  recommending software stacks in adviser

* Expand states for which Thoth has no observation about - used for filling
  Thoth's knowledge base using :ref:`Dependency Monkey <dependency_monkey>` and
  `Amun <https://github.com/thoth-station/amun-api>`_

.. note::

  The :ref:`introductory section <introduction>` discusses about intuition
  behind Thoth's adviser resolver that is based on two core components -
  Predictor and Resolver. The resolution is treated as a `Markov Decision
  Process (MDP) <https://en.wikipedia.org/wiki/Markov_decision_process>`_. See
  :ref:`Introduction section <introduction>` on more info and intuition behind
  MDP in the resolver's implementation.

The two main purposes above make Thoth a self-learning system.

Implementing a predictor
========================

To implement a predictor, you need to derive from :class:`Predictor
<thoth.adviser.predictor.Predictor>` class and implement at least the
:func:`run <thoth.adviser.predictor.Predictor.run>` method:

.. code-block:: python

  import attr

  from thoth.adviser import Beam
  from thoth.adviser import Context
  from thoth.adviser import Predictor
  from thoth.adviser import State


  @attr.s(slots=True)
  class MyPredictor(Predictor):
      """An example predictor implementation."""

      def run(self, context: Context, beam: Beam) -> Tuple[State, str]:
          """Main entry-point for predictor implementation."""
          state = next(context.iter_states())
          return state, next(iter(state.unresolved_dependencies))

The main method - ``run`` - accepts two parameters - :class:`context
<thoth.adviser.context.Context>` (adviser's context) and a :class:`beam
<thoth.adviser.beam.Beam>`. The beam is used as a pool of (not final) states
that are about to be resolved. The main goal of predictor is to return a state
present in the beam and package that should be resolved from the returned
state. The state  will be expanded in the next resolver round by resolving the
returned package.  The package is resolved by retrieving all the direct
dependencies of that dependency in different versions and new states are
generated out of all the combinations of packages in different versions that
can occur -- if such transition is valid based on Python ecosystem dependency
resolving; and dependencies are accepted by pipeline :ref:`sieves <sieves>` and
:ref:`steps <steps>`.

.. warning::

  Predictor does not adjust any properties stored in the context or beam!

  The state and package considered for the next resolution have to stay in the
  beam.

The example implementation above always expands the first state in the beam by
resolving direct dependencies of the first package stored in
:py:attr:`State.unresolved_dependencies
<thoth.adviser.state.State.unresolved_dependencies>`.  Note there is no
guarantee on order of states in the beam, unless sorted states are requested.

The beam will always hold at least one state. With at least one unresolved
dependency.

.. note::

  Raising exception :class:`EagerStopPipeline
  <thoth.adviser.exceptions.EagerStopPipeline>` will stop the resolution process.

  Raising any other exception has undefined behaviour.

Another example shows expansion of a random state and iteration over all the
states present in the beam:

.. code-block:: python

  def run(self, context: Context, beam: Beam) -> int:
      # Could be simplified to:
      #   return random.randint(0, beam.size - 1)
      for idx, state in enumerate(beam.iter_states()):
          if random.choice((True, False)):
              return state, random.choice(list(state.unresolved_dependencies))

      # Fallback to the first state.
      return beam.get(0)

The predictor can keep already computed results in its state, but note there is
no guarantee on index preserving and order in which states are stored in the
beam. It's also recommended to use :func:`Beam.iter_new_added_states
<thoth.adviser.beam.Beam.iter_new_added_states>` to check newly added states
between predictor runs. Note the state returned is *always* removed from the
beam.

.. note::

   Order of states in the beam can change across predictor invocations. Use
   ``id`` for checking identity and possible hashing of states in predictor's
   internal structures to optimize time spent in predictor.

Predictor attributes and methods
================================

The predictor implementation **should not** use any non-default attributes as
the constructor is called without any parameters. If any adjustment is desired,
a user can implement :func:`Predictor.pre_run
<thoth.adviser.predictor.Predictor.pre_run>` method that is called with
initialized adviser context before the stack generation pipeline is triggered:

.. code-block:: python

    def pre_run(self, context: Context) -> None:
        """Implement any pre-run initialization here."""

Predictor is instantiated only once per resolver - if resolution is run
multiple times on the same resolver instance, it reuses already instantiated
pipeline units and predictor. A proper implementation of pipeline units and
resolver use the ``pre_run`` method to initialize any internal state before
resolution.

Additional methods that can be provided are:

* :func:`Predictor.post_run <thoth.adviser.predictor.Predictor.post_run>` - run
  after the stack generation pipeline is finished to tear down the predictor

* :func:`Predictor.post_run_report
  <thoth.adviser.predictor.Predictor.post_run_report>` - run after the stack
  generation pipeline is finished and report is constructed as per user request
  (see :ref:`resolver for more info <resolver>`)

* :func:`Predictor.plot <thoth.adviser.predictor.Predictor.plot>` - used to
  plot predictor's history

See :ref:`Adaptive Simulated Annealing <annealing>` as an example of a
predictor that samples state space or performs hill climbing.
