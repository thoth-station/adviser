.. _resolver:

Thoth's resolver
----------------

As Python is a dynamic programming language, the actual resolution of Python
software stacks might take some time (you've probably `encountered this already
<https://github.com/pypa/pipenv/issues/2873>`_). One of the reasons behind it
is the fact that all packages need to be downloaded and installed to verify
version range satisfaction during the installation. This is also one of the
reasons Thoth builds its knowledge base - Thoth pre-computes dependencies in
the Python ecosystem so that resolving can be done offline without interacting
with outside world.

Thoth's resolver performs steps to resolve final states out of initial states
by running pipeline :ref:`sieves <sieves>` and :ref:`steps <steps>`.
Internally, there are computed all the combinations that can occur and there
are produced new states that are added to a pool of states, called beam.
Resolver tightly cooperates with :ref:`predictor <predictor>` that guides
resolver to resolve desired software stacks.

:ref:`Thoth's resolver respects Python ecosystem <compatibility>` to resolve
software stacks as done by pip or Pipenv. This is achieved in a different way
to also include observations about Python packages from Thoth's knowledge base.
Instead of implementing `3SAT
<https://en.wikipedia.org/wiki/Boolean_satisfiability_problem>`_ the resolver
operates directly on dependency graphs that are lazily expanded by expanding
not-yet resolved dependencies in resolver states. The whole resolution is
treated as a `Markov Decision Process (MDP)
<https://en.wikipedia.org/wiki/Markov_decision_process>`_ and the expansion of
dependencies is seen as a step in the MDP. See :ref:`Introduction section
<introduction>` on more info and intuition behind MDP in the resolver
implementation.

Dependencies of not-yet resolved packages (unresolved dependencies) are
resolved based on pre-computed dependency information stored in the Thoth's
knowledge base. This information is aggregated by Thoth's `solvers
<https://github.com/thoth-station/solver>`_ that are run for different software
environments. An example can be a solver for Fedora:31 running Python3.7 or
UBI:8 running Python3.6. These software environments can be then used as base
software environments for running Python applications (container images, also
suitable as base for OpenShift's s2i build process - see `s2i base images
provided by Thoth <https://github.com/thoth-station/s2i-thoth>`_ that are
analyzed by Thoth itself and Thoth has information to drive recommendations for
these container images used in an s2i build).

The resolver has two main purposes:

* resolve software stacks for Dependency Monkey runs and verify generated
  software stacks on `Amun <https://github.com/thoth-station/amun-api>`_

* resolve software stacks for recommendations

To instantiate a resolver, one can use two main functions:

* :func:`Resolver.get_adviser_instance
  <thoth.adviser.resolver.Resolver.get_adviser_instance>` - a resolver that
  produces software stacks for recommendations

* :func:`Resolver.get_dependency_monkey_instance
  <thoth.adviser.resolver.Resolver.get_dependency_monkey_instance>` - a
  resolver that produces software stacks for :ref:`Dependency Monkey
  <dependency_monkey>`

To resolve raw pipeline products, one can use :func:`Resolver.resolve_products
<thoth.adviser.resolver.Resolver.resolve_products>` method that yields raw
products during pipeline run. Another method, :func:`Resolver.resolve
<thoth.adviser.resolver.Resolver.resolve>` creates a complete report of an
adviser run together with some additional pipeline run information. See
:ref:`pipeline section for code examples <pipeline>`.

.. note::

  Pipeline unit methods :func:`Unit.post_run_report
  <thoth.adviser.unit.Unit.post_run_report>` and predictor's
  :func:`Predictor.post_run_report
  <thoth.adviser.predictor.Predictor.post_run_report>` are called only when
  :func:`Resolver.resolve <thoth.adviser.resolver.Resolver.resolve>` method is
  used to resolve software stacks.

Resolver instance transparently runs :ref:`stack resolution pipeline
<pipeline>` to produce scored software stacks.

During the whole run, resolver keeps context that is updated during runs and is
accessible in pipeline units as well as passed to :ref:`predictor's run method
<predictor>` to guide resolver in next states to be resolve.
