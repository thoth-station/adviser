.. _deployment:

Configuring and setting up adviser in a cluster
-----------------------------------------------

In the upcoming sections one can find information needed when configuring a
cluster deployment that adviser runs in.

Adviser provides hyperparameters that can be tweaked to gain more performance
or obtain better results when recommending a software stack. The upcoming
sections act as a reference guide on how to act in different scenarios when
certain issues are spotted in the cluster or if you wish to fine-tune adviser.

.. note::

  As adviser shares core components with Dependency Monkey, most of the details
  stated below also apply for Dependency Monkey.

Pre-requisities to run adviser
==============================

To run adviser code, you need CPython interpreter in version 3.6 or above. The
implementation uses native extensions (`fext
<https://github.com/thoth-station/fext>`_) to optimize some of the operations.

The version requirement for CPython interpreter enforces the built-in type
``dict`` to be ordered. This is an implementation detail in CPython 3.6 and
language feature onwards, but the code of adviser relies on this feature
(especially its core resolver algorithm).

The code was tested also on CPython 3.7 and CPython 3.8.

Allocating CPU time
===================

Adviser responds to ``SIGINT`` signal that is handled during the main
resolution and pipeline run. If a ``SIGINT`` is captured, adviser gracefully
stops the current pipeline run with resolution and gathers results obtained
until that point.

This behavior can be naturally used with Kubernetes/OpenShift liveness probes.

Memory management
=================

To avoid exploding memory consumption, adviser was designed with few features
in mind.

Adviser can do a fork from its main process and perform memory expensive
operations in a sub-process configured and triggered from the main process.
This behavior is turned off by default to simplify development and debugging
when running adviser locally. To enable
forking set ``THOTH_ADVISER_FORK=1``. When running adviser in the cluster, the
OOM killer will kill the memory expensive sub-process leaving the main process
untouched. The main process has a capability of detecting the OOM kill of the
sub-process and construct corresponding report.

Tweaking limit
##############

This parameter limits number of stacks that are produced and scored per adviser
run. In other words, it limits number of iterations needed to compute pipeline
products produced by the adviser pipeline.

Tweaking count
##############

Adviser's ``count`` parameter specifies how many stacks should be available for
the output. Internally, adviser keeps *count* top rated candidates to report
once the adviser finishes. It's usually a good idea to keep this number set to
1 for deployments. Numbers different than *count* could be considered when
experimenting with adviser or developing it. Naturally, this number cannot be
bigger than ``limit``.

When obtaining *latest* stack, this number can be set to ``1`` which will cause
adviser to immidiatelly terminate once it finds the first latest stack.

Setting seed
############

To make sure multiple adviser runs result in the same stack, it is a good idea
to set adviser's seed to the same value across mutliple adviser runs in a
deployment.  Note the resolution is stochastic in some sense (this also depends
on predictor used).

Also note the adviser runs depend on results obtianed from Thoth's knowledge
graph. If some relevant parts of the knowledge graph change, different results
might be produced by adviser even if the seed is set to a constant value across
multiple adviser runs.

Beam and it's width
###################

One of the core data structures keeping resolver's internal states is beam (see
:ref:`pipeline <pipeline>` and :ref:`predictor <predictor` docs for more info).
Beam width is the maximum number of elements stored at the same time and can be
configured using a hyperparameter during deployment.  There are few pros and
cons for large and small *width* numbers. The optimal beam width depends on the
stack size, CPU time allocated and memory available per adviser run in a
deployment.

If the beam width is set to a large number, it results in higher overhead
needed for maintaining internal data structure per resolver iteration/round
(see `fext <https://github.com/thoth-station/fext>`_). This overhead grows
linearly with beam width. Also, memory consumption is increased and more CPU
time is spent on maintaining the data structure and obtaining relevant resolver
states.

If the beam width is set to a small number, it will result in a smaller state
space explored (state space of all the possible stacks) possibly finding not
good-enough software stack candidate to recommend. In the worst case it can
result in no software stack resolved as candidates that would lead to a fully
resolved software stack might be removed from the beam (pushed away by
candidates that have higher score but do not lead to a fully resolved software
stack given the version range specification of dependencies).

An optimal number of beam width can be obtained empirically (or additional
analysis on top of adviser reports) based on software stacks that the system is
resolving.

Predictor
#########

Tweaking predictor configuration also falls into deployment specific
configuration. Predictor configuration is however specific per predictor
implementation so reach out to respective predictor documentation.

Development dependencies (dev flag)
###################################

In some cases, Thoth is recommending a software stack for application
deployments. Development dependencies are usually not installed in such cases
(if so, you should rething how the application is structured). By eliminating
developement dependencies the dependency graph explored on Thoth's side can be
smaller which can narrow down the exploration to dependencies that go to the
deployment. Naturally, this can have positive impact on the resulting software
stack recommended (a better one can be found given the state space explored).
