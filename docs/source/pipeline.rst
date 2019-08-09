.. _pipeline:

Stack generation pipeline
-------------------------

In this section, one can find the developer's introduction to stack generation
pipeline used in Thoth's adviser to generate stacks.

The pipeline is used to prepare, generate, filter and score software stacks.
The input to the pipeline is Thoth's `Project` abstraction carrying information
about direct dependencies for an application together with optional additional
vector stating software environment, hardware available and also other
information (see bellow for a complete listing).

The output of the pipeline is a list of generated `Project` instances, with
dependencies locked to a specific version based on pipeline results together
with a score and justification on why a certain stack is better than another
one.  The pipeline is dynamically created based on the incoming vector to the
stack generation pipeline.

The pipeline consists of the following three types of units:

* :class:`Sieve <thoth.adviser.python.pipeline.sieve.Sieve>`

* :class:`Step <thoth.adviser.python.pipeline.step.Step>`

* :class:`Stride <thoth.adviser.python.pipeline.stride.Stride>`

These units are provided as a list of concrete sieve, step and stride
implementations to :class:`Pipeline
<thoth.adviser.python.pipeline.pipeline.Pipeline>` constructor. They are
executed respecting their relative order in the supplied list (this is a lot of
times important relation as they might depend on each other).

The vector coming into the recommendation pipeline consists of the following
features:

* direct dependencies for the application - *required*
* recommendation type - *required*
* static source code analysis - library usage - *optional*
* software environment - *optional*
* hardware environment - *optional*

A more detailed description of each feature is described bellow.

Direct dependencies for the application
#######################################

Direct dependencies of the application - these dependencies are coming to the
resolver but they can also be used in the pipeline builder to configure stack
generation pipeline (sieves, steps and strides) to be configured for a
specific application.

Static source code analysis - library usage
###########################################

A user can use static source code analysis on the client side when asking for
advises. In that case, sources are scanned for library imports and
calls (`Invectio https://github.com/thoth-station/invectio`_ is used). The
gathered library usage captures libraries and what symbols are used from these
libraries in sources. This information can be subsequently used in recommendations
(in stack generation pipeline) to target recommendations specific to user's application.

Recommendation type
###################

To target user specific requirements for the recommended application stack, there
were introduced three types of recommendations:

* **LATEST**
* **TESTING**
* **STABLE**

**Latest** recommendations recommend the most latest versions of libraries. This
functionality somehow mimics raw pip or Pipenv but recommended latest versions are
already analyzed by Thoth and respect package source index configuration the user used.

**Stable** recommendations target the most suited software stacks which, based on
Thoth's gathered observations, are considered as stable - always running in
the given runtime environment.

**Testing** recommendation types recommend software for which there are no negative
observations but they might not behave stable in all cases.

Software environment
####################

Software environment is yet another vector coming to the recommendation engine.
It states additional software present in the environment, such as operating
system, Python interpreter version or IPython information in case of Jupyter
Notebooks.

Software environment can be automatically detected by `Thamos
<https://github.com/thoth-station/thamos>`_ - a user can use Thoth to get
recommendations for the same application when running in different software
(and also hardware) environments (for example different setup for a cluster
and a local desktop run).

Software environment together with hardware environment form "*runtime environment*".

Hardware environment
####################

Hardware environment is stating what hardware is present to run the given
application. `Thamos <https://github.com/thoth-station/thamos>`_ is capable to
perform hardware discovery as well (besides software environment discovery). An
example of hardware environment configuration can be GPU or CPU type.

Pipeline units
==============

The whole recommendation engine is designed as a pipeline which is made out of
3 unit types described in the upcoming sections. The configuration of pipeline
(how these units are grouped together and how are they relatively organized) is
determined dynamically on user request based on the vector described above to
target user specific requirements for the application and runtime environment
where the application runs in.

The order of pipeline unit types is set by stack generation pipeline
implementation to semantically distinguish how pipeline units form and score
the produced software stacks:

#. *Sieves* on direct dependencies
#. *Steps* on dependency graph
#. *Strides* on produced software stacks

The order of each pipeline unit implementation inside the group is then formed
in the stack generation pipeline builder respecting the input vector (see below).

Sieve
#####

The very first type of a pipeline unit is called :class:`Sieve
<thoth.adviser.python.pipeline.sieve.Sieve>`. This pipeline unit works on a
list of direct dependencies in specific versions (which were resolved based on
Thoth's knowledge base) and its aim is to filter out direct dependencies which
are not suitable. An example can be a sieve that filters out direct
dependencies which are known for issues based on supplied user's library usage.

.. note::

  When to use a sieve?

  If you want to do operations solely on direct dependencies. Each sieve can be written as a step, but by using a sieve you will reduce the overhead needed to construct additional data structures for dependency graph and optimize some of the queries done to the Thoth's knowledge base.

**Example**

See `this upstream issue
<https://github.com/tensorflow/tensorflow/issues/30990>`_. In summary, if user
uses `LSTM` and `ModelCheckpoint` in a TensorFlow application at the same time
the model does not work well. An example implementation of a sieve to target
this issue can be (note the implementation is artificial as the issue was
present only in nightly builds):

.. code-block:: python

  import logging
  from typing import List

  from thoth.python import PackageVersion
  from thoth.adviser.python.pipeline import Sieve
  from thoth.adviser.python.pipeline import SieveContext

  _LOGGER = logging.getLogger(__name__)


  class LSTMModelCheckpointIssue(Sieve):
      """Filter out direct dependencies based on TensorFlow issue #30990."""

      def run(self, sieve_context: SieveContext) -> None:
          """Filter out TensorFlow releases which have issues with LSTM and ModelCheckpoint use."""
          tensorflow_usage = self.library_usage["report"].get("tensorflow", [])
          if "tensorflow.keras.callbacks.ModelCheckpoint" in tensorflow_usage and "tensorflow.python.keras.layers.LSTM" in tensorflow_usage:
              for package_version in sieve_context.iter_package_versions():
                  if package_version.name != "tensorflow" or list(package_version.semantic_version) != [2, 0, 0, None, None]:
                      # Not 2.0.0 release with the given issue.
                      _LOGGER.debug("Package %r not affecting issue #30990", package_version.to_tuple())
                  else:
                      try:
                          sieve_context.remove_package_version(package_version)
                          _LOGGER.debug("Package %r excluded due to LSTM and ModelCheckpoint issue #30990", package_version.to_tuple())
                      except CannotRemovePackage as exc:
                          # Removing would cause invalidity - e.g. all direct dependencies of type TensorFlow would be removed.
                          _LOGGER.warning("Cannot remove package %r, user might encounter TensorFlow issue #30990: %s", package_version.to_tuple(), str(exc))
          else:
              _LOGGER.debug("ModelCheckPoint and LSTM not used at the same time")

Note the sieve can be added to the stack generation pipeline by pipeline
builder only if `ModelCheckpoint` and `LSTM` are used together to reduce
overhead running this sieve in cases when its not desired (see bellow for
more info).

A `CannotRemovePackage` exception can be raised if the given package cannot be
removed.

Once all sieves are run, Thoth obtains the whole dependency graph out of its
knowledge base and next pipeline units can be run - steps.

Steps
#####

A :class:`Step <thoth.adviser.python.pipeline.step.Step>` abstracts away
operations on top of dependency graph. One can perform transactional operations
on top of dependency graph - mark some of the nodes for
removal in a transaction and once the transaction is committed the logic behind step context
:class:`step context <thoth.adviser.python.pipeline.step_context.StepContext>`
ensures the validity of the transaction.

Besides removal of packages in the dependency graph, one can also score some of
the packages. When scoring the dependency graph is adjusted in a way the better
a package score has the higher precedence it has in the final resolution (the
dependency graph is weighted graph). The score can be positive, but also
negative (penalize the given package in resolution).

.. note::

  When to use a step?

  If you want to:

  * Filter out packages from resolution (e.g. installation-time errors)
  * Penalize packages in resolved software stacks (e.g. security vulnerabilities)
  * Prioritize packages in resolved software stacks (e.g. good performance)

**Example**

An example implementation of a step can be found below. The implementation of
the step iterates over all packages present in the dependency graph and
packages which are pre-releases based on semantic version are removed.

.. code-block:: python

  import logging
  from typing import Tuple

  from thoth.adviser.python.dependency_graph import CannotRemovePackage

  from thoth.adviser.python.pipeline import Step
  from thoth.adviser.python.pipeline import StepContext

  _LOGGER = logging.getLogger(__name__)

  class CutPreReleases(Step):
      """Cut-off pre-releases if project does not explicitly allows them."""

      def run(self, step_context: StepContext) -> None:
          """Cut-off pre-releases if project does not explicitly allows them."""
          if self.project.prereleases_allowed:
              _LOGGER.info(
                  "Project accepts pre-releases, skipping cutting pre-releases step"
              )
              return

          for package_version in step_context.iter_all_dependencies():
              if (
                  package_version.semantic_version.prerelease
                  or package_version.semantic_version.build
              ):
                  package_tuple = package_version.to_tuple()
                  _LOGGER.debug(
                      "Removing package %r - pre-releases are disabled", package_tuple
                  )
                  try:
                      with step_context.remove_package_tuples(package_tuple) as txn:
                          txn.commit()
                  except CannotRemovePackage as exc:
                      _LOGGER.error("Cannot produce stack with removing all pre-releases: %s", str(exc))
                      raise

The context manager used when accessing :func:`StepContext
<thoth.adviser.python.pipeline.step_context.StepContext.remove_package_tuples>` is acting as a
transaction on top of dependency graph. You can stack multiple removals of
packages. Once the transaction gets committed, all the packages are removed in order they
were scheduled to be removed. If some of the packages causes invalidity to
dependency graph, the transaction fails (no changes to dependency graph are
done and all the changes done until reaching the package which would cause
dependency graph invalidity are rolled back):

.. code-block:: python

    try:
        with step_context.remove_package_tuples(package_tuple1, package_tuple2) as txn:
            print(txn.to_remove_nodes)
            print(txn.to_remove_edges)
            txn.commit()
            # or txn.abort() in case of cancelling the transaction.
    except CannotRemovePackage as exc:
         # The message carried in exception would be something like:
         #   "Cannot remove package <pkg>, removing this package would lead "
         #   "to removal of all direct dependencies of package <direct-requirement>"
        _LOGGER.info("Transaction for removal of packages was aborted: %s", str(exc))
    else:
        _LOGGER.info(
            "All the packages from %r were removed successfully from dependency graph",
            some_package_tuples
        )


Once all steps are executed, there is executed :ref:`libdependency_graph.so <libdependency_graph>`
which generates stack candidates based on traversals of the dependency graph. The produced stack
candidates are in parallel scored in next pipeline units - strides.

.. note::

  You can access additional step properties such as software environment, hardware environment, library usage to create complex steps removing based on observations stored in the knowledge base.

Strides
#######

Strides operate on stack candidates - see :class:`stack candidate
implementation
<thoth.adviser.python.pipeline.stack_candidates.StackCandidates>` and
:class:`stride context
<thoth.adviser.python.pipeline.stride_context.StrideContext>`. The input to a
stride is a fully resolved software stack encapsulated in :class:`stride
context <thoth.adviser.python.pipeline.stride_context.StrideContext>` (each and
every package is locked to a specific version coming from a specific Python
package index).

.. note::

  When to use a stride?

  If you want to:

  * Filter our some software stacks because of some bad aspect (e.g. a group of packages are not installable into the given runtime environment).
  * Prioritize some software stacks based on some characteristics (e.g. good performance).
  * De-prioritize some software stacks based on some characteristics (e.g. bad performance).
  * Notify user in the software stack justification about some fact (e.g. warning that Thoth does not have relevant data for some resovled packages).
  * Adding additional justification to the resolved stack (this will be shown to the user)

An example of a stride which penalizes packages with a CVE can be found below:

.. code-block:: python

  import logging
  from typing import Tuple

  from thoth.adviser.python.pipeline import Stride
  from thoth.adviser.python.pipeline import StrideContext
  # To remove a stack candidate, raise StrideRemoveStack:
  # from thoth.adviser.python.pipeline.exceptions import StrideRemoveStack

  _LOGGER = logging.getLogger(__name__)


  class CveScoring(Stride):
      """Penalization based on CVE being present in stack."""

      PARAMETERS_DEFAULT = {"cve_penalization": -0.2}

      def run(self, stride_context: StrideContext) -> None:
          """Score stacks with a CVE in a negative way."""
          for package_tuple in stride_context.stack_candidate:
              cve_records = self.graph.get_cve_records(package_name=package_tuple[0], package_version=package_tuple[1])
              for cve_record in cve_records:
                  _LOGGER.debug("Found a CVE for %r", package_tuple)
                  # Add additional fields to the produced justification for user:
                  cve_record.update(
                      {
                          "type": "WARNING",
                          "justification": f"Found a CVE for package {package_tuple[0]} in version {package_tuple[1]}",
                      }
                  )

                  # Penalize the resolved stack:
                  stride_context.adjust_score(
                      self.parameters["cve_penalization"], justification=[cve_record]
                  )

The stride implementation can raise :class:`StrideRemoveStack
<thoth.adviser.python.pipeline.step_context.StepContext>` which will cause
removal of the produced stack candidate:

.. code-block:: python

  import random

  from thoth.adviser.python.pipeline import Stride
  from thoth.adviser.python.pipeline import StrideContext
  from thoth.adviser.python.pipeline.exceptions import StrideRemoveStack

  class Bar(Stride):
      def run(stride_context: StrideContext) -> None:
          if random.choice([True, False]):
              raise StrideRemoveStack(
                  "It's heads, removing stack candidate (score: %f): %r",
                  stride_context.score,
                  stride_context.stack_candidate
               )

.. note::

  You can access additional stride properties such as software environment, hardware environment, library usage to create complex strides filtering or scoring stack candidates based on observations in Thoth's knowledge base.

Once all the strides are executed (due to limit for number of software stacks
produced or all the stacks were already generated), stack candidates are turned
into :class:`pipeline products
<thoth.adviser.python.pipeline.product.PipelineProduct>`.

Pipeline Architecture - Dynamic Pipeline Creation
###################################################

The dynamic pipeline creation is done in :class:`pipeline builder
<thoth.adviser.python.builder.PipelineBuilder>`. The main aim of this
builder is to construct pipeline sieves, steps and strides respecting
their relative order and adjust their parameters, if needed.

The pipeline builder has two main methods:

* :func:`get_adviser_pipeline_config <thoth.adviser.python.builder.PipelineBuilder.get_adviser_pipeline_config>` - this method constructs pipeline steps and strides for an adviser run

* :func:`get_dependency_monkey_pipeline_config <thoth.adviser.python.builder.PipelineBuilder.get_dependency_monkey_pipeline_config>` - this method constructs pipeline steps and strides for a Dependency Monkey run

.. note::

  Pipeline builder has attributes graph database, project (stating runtime environment) and library_usage which can be used during pipeline configuration creation.

.. image:: _static/pipeline.png
   :target: _static/pipeline.png
   :alt: Stack generation pipeline

If you take a look at the builder implementation, you can see that each sieve,
step and stride accepts also configuration (which can be `None` or a
dictionary).  Pipeline builder can parametrize these pipeline units based on
its input vectors (e.g. be less pedantic on security vulnerabilities for
testing stacks).

Creating adviser's pipeline configuration programmatically
##########################################################

If you would like to experiment with adviser and recommendations interactively
(e.g. from within Jupyter Notebooks), you can use prepared methods to do so:

.. code-block:: python

  from thoth.adviser.python import Adviser
  from thoth.adviser.enums import RecommendationType
  from thoth.adviser.python.pipeline import Pipeline
  import thoth.adviser.python.pipeline.sieves as sieves
  import thoth.adviser.python.pipeline.steps as steps
  import thoth.adviser.python.pipeline.strides as strides

  # Get top 10 stacks found, limit scoring to 100 stacks found for STABLE recommendations:
  adviser = Adviser(
      count=10,
      limit=100,
      recommendation_type=RecommendationType.STABLE,
  )

  # Add sieves, steps and strides for pipeline configuration as desired:
  pipeline = Pipeline(
      library_usage={},  # Provide if you have some.
      sieves=[
        (sieve.ExampleSieve1, {"param1": 3.14}),
        (sieve.ExampleSieve2, None),
      ],
      steps=[
        (steps.ExampleStep1, None),
      ],
      strides=[
        (strides.ExampleStride1, {"penalization": -0.2}),
        (strides.ExampleStride2, None),
      ],
  )
  report = adviser.compute_using_pipeline(pipeline=pipeline)


This is especially useful when developing or experimenting with new pipeline units.

.. note::

  In all cases, sieves, steps and strides should be atomic pieces and `they should do one thing and do it well <https://en.wikipedia.org/wiki/Unix_philosophy>`_.
