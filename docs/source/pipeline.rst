.. _pipeline:

Stack generation pipeline
-------------------------

In this section one can find developer's introduction to stack generation
pipeline used in Thoth's adviser to generate stacks.

The pipeline is used to prepare, generate, filter and score software stacks.
Input to the pipeline is Thoth's `Project` abstraction carrying information
about direct dependencies for an application together optional additional
vector stating runtime environment and hardware available. The output of
pipeline is a list of generated `Project`s, but with dependencies locked to a
specific version based on pipeline attributes.

The pipeline consists of the following two types of units (see Thoth's
`PipelineUnitBase` base class):

* Steps
* Strides

These units are provided as a list of steps or strides to `Pipeline`
constructor. They are executed respecting their relative order in the supplied
list.

Steps
#####

A step abstracts away simple operations on "paths" - paths stating serialized
dependency graph into a list of package tuples, where each package tuple (made
out of package name, version and index url) states how a resolution might look
like. A list of these lists is in fact serialized dependency graph which is
being traversed in :ref:`libdependency_graph.so <libdependency_graph>`.

Before a first step is executed, there is run initialization (called
"initialize stepping" in sources) which queries graph database (respecting
solver information) and returns back a list of paths for the given set of
direct dependencies of the supplied project.

A step then operates on a context called `StepContext` which provides core
routines on paths and packages which are candidates for resolution (together
with all their transitive dependencies). The main aim of a step implementation
can be:

* prioritize packages in the output project stream which has some impact on software stacks (e.g. make sure first stacks generated out of pipeline have packages which have positive performance impact)

* remove packages and paths which have bad impact on generated software stacks (e.g. some packages cannot run together because of API incompatibility)

Strides
#######

Strides operate on a stack candidates - see `StrideContext`. The input to a
stride is a fully resolved software stack (each and every package is locked to
a specific version coming from a specific Python package index). Stride is then
used to:

* decide whether the resolved software stack should be included in the output (e.g. random sampling of generated software stacks on Dependency Monkey)
* score the resulting software stack (e.g. performance based scoring)


Pipeline Architecture
=====================

.. image:: _static/pipeline.png
   :target: _static/pipeline.png
   :alt: Stack generation pipeline
