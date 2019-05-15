.. _pipeline:

Stack generation pipeline
-------------------------

In this section, one can find the developer's introduction to stack generation
pipeline used in Thoth's adviser to generate stacks.

The pipeline is used to prepare, generate, filter and score software stacks.
Input to the pipeline is Thoth's `Project` abstraction carrying information
about direct dependencies for an application together optional additional
vector stating runtime environment and hardware available. An optional
parameter is also library usage, which is an output of tool called `Invectio
https://github.com/thoth-station/invectio`_ (static source code analysis which
states which relevant parts of libraries are used). The output of the pipeline
is a list of generated `Project`s, but with dependencies locked to a specific
version based on pipeline results. The pipeline is dynamically created based on
attributes to the stack generation pipeline (direct dependencies, library
usage, runtime environment characteristics, hardware used, ...).

The pipeline consists of the following two types of units (see Thoth's
`PipelineUnitBase` base class):

* :class:`Step <thoth.adviser.python.pipeline.step.Step>`

* :class:`Stride <thoth.adviser.python.pipeline.stride.Stride>`

These units are provided as a list of steps or strides to :class:`Pipeline
<thoth.adviser.python.pipeline.pipeline.Pipeline>` constructor. They are
executed respecting their relative order in the supplied list.

Steps
#####

A :class:`Step <thoth.adviser.python.pipeline.step.Step>` abstracts away simple
operations on "paths" - paths stating serialized dependency graph into a list
of package tuples, where each package tuple (made out of package name, version
and index URL) states how a resolution might look like. A list of these lists
is in fact serialized dependency graph which is being traversed in dependency
graph implemented in :ref:`libdependency_graph.so <libdependency_graph>`.

Before a first step is executed, there is run initialization (called
"initialize stepping" in sources) which queries graph database (respecting
solver information) and returns back a list of paths for the given set of
direct dependencies of the supplied project.

A step then operates on a context called :class:`step context
<thoth.adviser.python.pipeline.step_context.StepContext>` which provides core
routines on paths and packages which are candidates for resolution (together
with all their transitive dependencies). The main aim of a step implementation
can be:

* Prioritize packages in the output project stream which have some impact on software stacks (e.g. make sure first stacks generated out of pipeline have packages or group of packages which have positive performance impact)

* Remove packages and paths which have bad impact on generated software stacks (e.g. some packages cannot run together because of API incompatibility which is captured in Thoth's knowledge base)

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
package index). Stride is then used to:

* Decide whether the resolved software stack should be included in the output (e.g. random sampling of generated software stacks on :ref:`on Dependency Monkey runs <dependency_monkey>`)

* Score the resulting software stack (e.g. performance based scoring) - once the stack generation pipeline is finished, the pipeline generates recommended pinned down software stacks

Pipeline Architecture - Dynamic Pipeline Creation
###################################################

How pipeline looks like - what steps and what strides (pipeline units) create pipeline, is determined dynamically based on:

#. Static analysis of user's source code using `Invectio <https://github.com/thoth-station/invectio/>`_ to find out which library parts are used by user's application so a specific pipeline units are picked to construct the pipeline

#. Direct dependencies of user's application

#. Hardware used to run the application

#. Software environment - environment in which the user's application runs in

#. Additional feature which is also one of:

  #. Recommendation type (e.g. testing, stable, latest, ...) - used for adviser specific stack generation pipelines (see below)

  #. Decision function - used in :ref:`Dependency Monkey <dependency_monkey>` to judge which software stack will be inspected on Amun service to gather more observations to Thoth's knowledge base or to save computational resources (see below)

This dynamic pipeline creation is done in :class:`pipeline builder
<thoth.adviser.python.builder.PipelineBuilder>`. The main aim of this
builder is to construct pipeline steps, respecting their relative order and
their parameters.

The pipeline builder has two main methods:

* :func:`get_adviser_pipeline_config <thoth.adviser.python.builder.PipelineBuilder.get_adviser_pipeline_config>` - this method constructs pipeline steps and strides for an adviser run

* :func:`get_dependency_monkey_pipeline_config <thoth.adviser.python.builder.PipelineBuilder.get_dependency_monkey_pipeline_config>` - this method constructs pipeline steps and strides for a Dependency Monkey run

.. note::

  Pipeline builder has attributes such as graph database which can be used to derive additional information. You can query graph database for observations to judge which pipeline units should be excluded or included together with their parameters.

.. image:: _static/pipeline.png
   :target: _static/pipeline.png
   :alt: Stack generation pipeline

If you take a look at the builder implementation, you can see that each step
and stride accepts also configuration (which can be `None` or a dictionary).
Pipeline builder can parametrize these pipeline units based on its input
vectors (e.g. be less pedantic on security vulnerabilities for testing
stacks).

Developing own pipeline units
#############################

As stated earlier, there are two core building blogs (units) of in a stack generation pipeline:

#. Steps
#. Strides

**When do I want to implement a step?**

Steps work on packages (one or multiple) or paths in dependency graph - they
adjust dependency graph structure *before the actual resoltion*. Thus a
use-case for a step would be:

#. You want to filter out packages from resolution (e.g. installation-time errors).

#. You want to penalize packages in resolved software stacks (e.g. security vulnerabilities).

#. You want to prioritize packages in resolved software stacks (e.g. good performance).

**When do I want to implement a stride?**

Strides operate on fully resolved software stacks - they accept a list of
pinned down packages which should be included in the final software stack. An
example ucases would be:

#. You want to filter our some software stacks because of some bad aspect (e.g. a group of packages are not installable into the given runtime environment).

#. You want to prioritze some software stacks based on some characteristics (e.g. good performance).

#. You want to de-prioritize some software stacks based on some characteristics (e.g. bad performance).

#. You want to notify user in the software stack justification about some fact (e.g. warning that Thoth does not have relevant data for some resovled packages).

In both cases, steps and strides should be atomic pieces and `they should do
one thing and do it well <https://en.wikipedia.org/wiki/Unix_philosophy>`_.

Steps are instantiated once and each one is run once for step context passed
between them - the execution respects relative positioning of steps in the step
lists as created by pipeline builder.

Strides are instantiated once per a pipeline run, so they can keep state on
stacks which were passed during pipeline run. As in case of steps, the relative
positioning of strides (as ordered by pipeline builder) is respected.

Developing own pipeline step
============================

To implement a pipeline step, simply derive from :class:`StepContext
<thoth.adviser.python.pipeline.step_context.StepContext>` and implement the
``run`` method:

.. code-block:: python

  import logging
  import random

  from thoth.adviser.python.pipeline import Step
  from thoth.adviser.python.pipeline import StepContext
  from thoth.adviser.python.pipeline.exceptions import CannotRemovePackage

  _LOGGER = logging.getLogger(__name__)


  class Foo(Step):
      """An example Foo step which is removing some packages randomly."""

      def run(step_context: StepContext) -> None:
            """Remove packages randomly from dependency graph."""
            for package_tuple in step_context.iter_all_dependencies_tuple():
                if not random.choice([True, False]):
                   _LOGGER.info("Package %r will not be removed", package_tuple)
                   continue

                try:
                   with step_context.change(graceful=False) as step_change:
                       step_change.remove_package_tuple(package_tuple)
                       _LOGGER.info("Package %r was removed", package_tuple)
                except CannotRemovePackage as exc:
                   _LOGGER.info("Package %r cannot be removed: %s", package_tuple, str(exc))

The context manager used when accessing :func:`StepContext
<thoth.adviser.python.pipeline.step_context.StepContext.change>` is acting as a
transaction on top of dependency graph. You can stack multiple removals of
packages. Once the context is left, all the packages are removed in order they
were scheduled to be removed. If some of the packages causes invalidity to
dependency graph, the transaction fails (no changes to dependency graph are
done and all the changes done until reaching the package which would cause
dependency graph invalidity are rolled back):

.. code-block:: python

    try:
        with step_context.change(graceful=False) as step_change:
            for package_tuple in some_package_tuples:
               step_change.remove_package_tuple(package_tuple)
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

.. note::

  Pipeline step has attribute to access graph database which can be used to derive additional information from Thoth's knowledge base. Taking benefits of using asyncio when querying graph database might be a good idea.

In the example above we have shown how to remove a package or set of packages
from dependency graph. The following example shows how to adjust dependency
graph in a way, so that packages which have good impact on software stack will
be prioritized to occur in the resulting pinned down software stack and
packages which have bad impact on the resulting application are removed or
de-prioritized:

.. code-block:: python

   import logging

   from ..step import Step
   from ..step_context import StepContext
   from ..units import get_cve_records

   _LOGGER = logging.getLogger(__name__)


   class CvePenalization(Step):
       """Penalization based on CVE being present in stack."""

       # These are default parameters, they can be adjusted in the pipeline
       # builder as desired (e.g. based on recommendation type requested).
       PARAMETERS_DEFAULT = {"cve_penalization": -0.2}

       def run(self, step_context: StepContext) -> None:
           """Penalize stacks with a CVE."""
           for package_tuple in step_context.iter_all_dependencies_tuple():
               cve_records = self.graph.get_cve_records(
                   package_name=package_tuple[0],
                   package_version=package_tuple[1],
                   index_url=package_tuple[2]
                )
                if cve_records:
                   _LOGGER.debug("Found a CVEs for %r: %r", package_tuple, cve_records)
                   # Positive score adjusts dependency graph in a way positive
                   # the "positive" packages will occur in the resolved stacks
                   # sooner (will take precedence):
                   step_context.score_package_tuple(
                       package_tuple, self.parameters["cve_penalization"]
                   )

.. note::

  You can access additional step properties such as runtime sorfware information, hardware information (runtime environment), library usage to create complex steps adjusting dependency graph.

Make sure your implementation fits into project structure, that is, place your
step implementation into thoth/adviser/python/pipeline/steps/ directory.

Developing own pipeline stride
==============================

To develop a pipeline stride, derive from :class:`Stride
<thoth.adviser.python.pipeline.stride.Stride>` and implement the ``run`` method
as shown bellow:

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

  Pipeline stride has attributes such as graph database which can be used to derive additional information from Thoth's knowledge base. Taking benefits of using asyncio when querying graph database might be a good idea.

In the example below, we are creating a scoring stride, which scores based on library usage:

.. code-block:: python

  from thoth.adviser.python.pipeline import Stride
  from thoth.adviser.python.pipeline import StrideContext

  class UsagePrioritization(Stride):
      def run(stride_context: StrideContext) -> None:
          for package_tuple in stride_context.stack_candidate:
            if self.graph.has_good_usage(package_tuple):
                stride_context.adjust_score(
                   +2.0,
                   justification=[{
                       "type": "INFO",
                       "justification": f"Package {package_tuple} is popular",
                   }]
                )

.. note::

  You can access additional stride properties such as runtime sorfware information, hardware information (runtime environment), library usage to create complex strides filtering or scoring software stacks.

Implementations of all strides live in
``thoth/adviser/python/pipeline/strides/``. Make sure you place implementation
there to respect project structure and integrate with other parts of adviser.
