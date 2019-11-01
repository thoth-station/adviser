.. _pipeline:

State expansion pipeline
------------------------

In this section, one can find the developer's introduction to state expansion
pipeline used in Thoth's adviser that expands states to produce pipeline products.

The pipeline is used to prepare, generate, filter and score partially or fully
resolved software stacks, abstracted into a :class:`State
<thoth.adviser.state.State>`.  The pipeline is run within :ref:`adaptive
simulated annealing <anneal>` which encapsulates results (final states) of the
pipeline runs into a higher abstraction called :class:`Product
<thoth.adviser.product.Product>` which can subsequently become part of a
:class:`Report <thoth.adviser.report.Report>` (see methods
:func:`AdaptiveSimulatedAnnealing.anneal
<thoth.adviser.anneal.AdaptiveSimulatedAnnealing.anneal>` and
:func:`AdaptiveSimulatedAnnealing.anneal_products
<thoth.adviser.anneal.AdaptiveSimulatedAnnealing.anneal_products>` for more
info).

The input to the pipeline is Thoth's `Project` abstraction carrying information
about direct dependencies of an application together with optional additional
vector stating software environment, hardware available and also an optional
result of a static source code analysis on user's application for targeting
application specific recommendations (API used from libraries).

The pipeline is dynamically created based on the incoming vector to the state
generation pipeline, which makes Thoth's adviser a reconfigurable resolver
suitable to resolve optimized software stacks for a specific use.

The pipeline consists of the following types of units:

* :class:`Boot <thoth.adviser.boot.Boot>`

* :class:`Sieve <thoth.adviser.sieve.Sieve>`

* :class:`Step <thoth.adviser.step.Step>`

* :class:`Stride <thoth.adviser.stride.Stride>`

* :class:`Wrap <thoth.adviser.wrap.Wrap>`

A foreword for units
====================

All units are derived from :class:`Unit <thoth.adviser.unit.Unit>` that
provides a common base for implemented units of any type. This way, each and
every unit can benefit from the shared functionality. The base class also
provides access to the input pipeline vectors and other properties:

* `project` property can be used to access project information for which the
  pipeline is producing software stacks, information about **direct
  dependencies**, configured **Python package indexes** (see `Pipfile`
  abstraction)

* the `Project` abstraction (as can be found in Thoth's `thoth-python` library)
  also provides information about **software environment** (operating system
  name and version, Python interpreter version used and additional information
  such as IPython information when resolving software stacks for Jupyter
  Notebooks)

* **hardware information** is also part of the `Project` abstraction and lets
  users of Thoth provide information about hardware used (e.g. GPU card type)
  eigher manually or by using automatic hardware discovery in the Thamos client
  tool when submitting requests to Thoth's backend

* `library_usage` property carries information about **API calls to libraries**,
  that maps names of libraries to symbols used from user's application (this
  is in fact output of Thoth's static analysis done on the source code - see
  `Invectio <https://github.com/thoth-station/invectio/>`_) - this way Thoth
  can build adviser's pipeline configuration that is optimized for example for
  a convolutional neural network if there are detect calls to CNN API calls of
  used libraries

* an instantiated adapter to Thoth's knowledge graph that aggregates
  information about software packages, software run and build environments as
  well as information about hardware that can be used during pipeline units run

Pipeline configuration creation
===============================

Each pipeline unit provides a class method called `should_include` which is executed
on the :class:`pipeline configuration creation
<thoth.adviser.pipeline_config.PipelineConfig>` (that states a list of sieves,
steps and strides to be included in the pipeline). The class method returns a
dictionary stating unit configuration if the given unit should be used (an
empty dictionary if no configuration changes to unit parameters are done), a
special value of `None` indicates the given pipeline unit should not be added
to the pipeline configuration.

The `should_include` unit class method is in fact called multiple times during
pipeline configuration construction. The pipeline builder iterates over all
pipeline units and asks if they should be included in the pipeline
configuration until no change to the pipeline configuration is made. This way
pipeline can be constructed autonomously where a developer of a pipeline unit
just programatically states when the given pipeline unit should be included in
the pipeline configuration (stating dependencies on other pipeline units or
conditionally add pipeline unit under specific circumferences). An example can
be a pipeline unit which includes scoring based on performance indicators done
on `conv2d <https://www.tensorflow.org/api_docs/python/tf/nn/conv2d>`_ used in a
TensorFlow application:

.. code-block:: python

    # snip ...

    @classmethod
    def should_include(
        cls, context: PipelineBuilderContext
    ) -> Optional[Dict[str, Any]]:
        """Include this pipeline unit if user uses TensorFlow and there are done calls to conv2d."""
        if context.is_included(cls):
           # This pipeline unit is already included in the pipeline configuration, we don't
           # need to include this pipeline unit multiple times.
           # 
           # The same method `is_included' can be used to inspect if pre-requisite pipeline
           # units are present in the pipeline configuration.
           return None

        if context.library_usage and "tf.nn.conv2d" in context.library_usage.get("tensorflow", {}):
           # As an example - adjust parameter `score_factor' of this pipeline
           # unit to 2.0, which will override the default one.
           return {"score_factor": 2.0}

    # ... snip


On a pipeline run, there are first executed all sieves on all the resolved
packages which are considered to become a part of states, then all steps to
produce a final state and lastly all strides on a final state. Each unit type
respects relative ordering - the very first sieve added is run first, then a
second one and so on respecting the relative order of sieves in the pipeline
configuration (the order in which they were registered). The same logic applies
to steps and strides.

See implementation of :class:`PipelineBuilderContext
<thoth.adviser.pipeline_builder.PipelineBuilderContext>` for more info on
provided methods that can be used during pipeline configuration creation.

Note the annealing algorithm with pipeline steps is shared for computing
advises and for Dependency Monkey to test and evaluate characteristics of
software stacks. You can use methods provided by :class:`PipelineBuilderContext
<thoth.adviser.pipeline_builder.PipelineBuilderContext>` to check if the
pipeline configuration is created for computing advises or whether the created
pipeline configuration is used in Dependency Monkey runs.


Boot
====

A very first pipeline unit is called "boot" as it boots up the whole pipeline.
It's run prior to any resolution right after the simulated annealing is started.
A boot unit can be used to check parameters to the pipeline from semantics point
of view.

.. note::

  When to use a boot unit?

  If you want to inspect supplied project to the pipeline or used runtime
  environment. The boot part can for example block runtime environments which are
  too old or are known to have serious issues (e.g. blocking OpenShift s2i
  builds cluster wide by Thoth administrator).


Note any exception raised in a boot unit is causing a stop in the whole
stack recommendation request.

Sieve
=====

The second pipeline unit called "`sieve
<https://en.wikipedia.org/wiki/Sieve>`_" is used to filter out packages which
should not occur in a software stack at all. An example use case can be
filtering packages which have installation issues in the given software
environment so there is no reason to produce software stacks with these
packages in recommendations.

An example implementation of a sieve implementation can be to use Thoth's
knowledge graph to filter out packages which are not installable into the
software environment (e.g. installation of legacy Python2 packages when
Python3+ is used as described above):

.. literalinclude:: ../../thoth/adviser/sieves/solved.py
   :language: python
   :lines: 18-

Another example of a sieve can be filtering packages that are pre-releases, but
pre-releases were disabled in *Pipenv* file:

.. literalinclude:: ../../thoth/adviser/sieves/prereleases.py
   :language: python
   :lines: 18-

The parameter `package_version` is of type `PackageVersion` which is an
abstraction on top of a Python's package in a version (stating all its
properties, see library `thoth-python` for more info). Note artifact hashes are
retrieved lazily once a final state is produced (hance the
`PackageVersion.hashes` property will in most cases be an empty array unless
the given package was already produced in one of the pipeline's final states).

.. note::

  When to use a sieve?

  If you want to evaluate addition of a single package without considering the current state in the resolution.

Step
====

The main purpose of a unit of type :class:`Step <thoth.adviser.step.Step>` is
to decide whether a creation of a new state out of an already existing one is
acceptable and what would be the score adjustment if the given step is
performed together with a justification reported to a user. A new state is
created out of an existing one by resolving direct dependencies of a not yet
resolved dependency in the dependency graph. Hence, the new state inherits all
the properties of the parent state and pipeline steps decide what is the impact
of adding new packages to the (expanded) parent state.

Note by resolving a dependency in a parent state, we possibly get multiple
states based on combinations of package types in different versions in which
dependencies may occur.

In other words, a step is performed to create new states closer to final states
out of an already found non-final state in the discrete state space of all
the possible states (final and non-final ones).

An implementation of a step accepts

.. note::

  When to use a step?

  If you want to evaluate acceptance of a package into a state and its impact.

  An example can be:

  * blocking two or more packages to be present in a state due to API incompatibilities spotted on runtime (Python is a dynamic programming language)

  * blocking a package from being present in resolved software stacks due to a native dependecy which is not present in the runtime environment 

  * penalize stacks with packages because of security vulnerabilities found in packages forming the stack

  * prioritize packages in resolved software stacks because of good performance observations in software and hardware environment used

  * etc.

You can find an example of a step implementation performing penalization if a
security vulnerability is found bellow:

.. literalinclude:: ../../thoth/adviser/steps/cve.py
   :language: python
   :lines: 18-


Stride
======

Units of type stride are the last pipeline units executed on final states which
keep fully resolved Python software stacks considering the given software
environment and hardware information as provided to the pipeline.

.. note::

  When to use a stride?

  If you want to evaluate acceptance of a final state that will become pipeline product.

An example of a stride implementation can be a random decision stride which is
used in Dependency Monkey to sample state space of possible software stacks to
gather observations for adviser when recommending software stacks:

.. literalinclude:: ../../thoth/adviser/strides/random_decision.py
   :language: python
   :lines: 18-


Wrap
====

Last but not least pipeline unit is called "wrap" as it wraps up the whole work done
on a state. It's called each time a final step is produced and accepted by all the
strides. Note any operations on the :class:`thoth.adviser.state.State` are still
valid as this pipeline unit is called before creation of a pipeline product (if requested so).

.. note::

  When to use a wrap unit?

  Each time you would like to do an operation on a fully resolved and accepted Python software stack
  on the given environment. This can be also an external event - like signalizing progress
  to an external service.


Afterword for pipeline units
============================

All the sieves, steps and strides *should not* raise any exception - raising an
exception other than :class:`thoth.adviser.exceptions.NotAcceptable`
and :class:`thoth.adviser.exceptions.EagerStopPipeline` (used to terminate annealing
prematurely) causes undefined behaviour (mostly crashes on the annealing part).

Pipeline units of type boot and wrap *should not* raise any exception except
for :class:`thoth.adviser.exceptions.EagerStopPipeline` for premature end of annealing
in a nice, way.

All pipeline units should be atomic pieces and `they should do one thing
and do it well <https://en.wikipedia.org/wiki/Unix_philosophy>`_. They were
designed to be small pieces forming complex resolution system.


Static source code analysis - library usage
===========================================

A user can use static source code analysis on the client side when asking for
advises. In that case, sources are scanned for library imports and calls
(`Invectio <https://github.com/thoth-station/invectio>`_ is used). The gathered
library usage captures libraries and what symbols are used from these libraries
in sources. This information can be subsequently used in recommendations (in
the state generation pipeline) to target recommendations specific to user's
application.


Recommendation type
###################

To target user specific requirements for the recommended application stack,
there were introduced three types of recommendations:

* **LATEST**
* **TESTING**
* **STABLE**

**Latest** recommendations recommend the most latest versions of libraries.
This functionality somehow mimics raw pip or Pipenv but recommended latest
versions are already analyzed by Thoth and respect package source index
configuration the user used (annealing will become `hill climbing
<https://en.wikipedia.org/wiki/Hill_climbing>`_).

**Stable** recommendations target the most suited software stacks which, based
on Thoth's gathered observations, are considered as stable - always running in
the given runtime environment.

**Testing** recommendation types recommend software for which there are no
negative observations but they might not behave stable in all cases.


Software environment
####################

Software environment is yet another vector coming to the recommendation engine.
It states additional software present in the environment, such as operating
system, Python interpreter version or IPython information in case of Jupyter
Notebooks.

Software environment can be automatically detected by `Thamos
<https://github.com/thoth-station/thamos>`_ - a user can use Thoth to get
recommendations for the same application when running in different software
(and also hardware) environments (for example different setup for a cluster and
a local desktop run).

Software environment used to run an application together with hardware
environment form "*runtime environment*".


Hardware environment
####################

Hardware environment is stating what hardware is present to run the given
application. `Thamos <https://github.com/thoth-station/thamos>`_ is capable to
perform hardware discovery as well (besides software environment discovery). An
example of hardware environment configuration can be GPU or CPU type.

