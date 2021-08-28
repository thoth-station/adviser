.. _prescription:

Declarative prescriptions for resolver
--------------------------------------

The implementation of the resolver allows to declaratively specify
:ref:`pipeline units <unit>` that should be included in the :ref:`resolver
pipeline <pipeline>` during the resolution process without actually implementing
any code.  The document below describes core mechanics behind creating such
"prescriptions" for the resolver.

.. note::

  Check `thoth-station/prescriptions <https://github.com/thoth-station/prescriptions>`__
  repository that provides prescriptions for open-source Python packages.

  See also `this pull request
  <https://github.com/thoth-station/adviser/pull/1821>`__ for a reference on how
  to implement a specific pipeline unit type that extends resolver functionality.
  A high level overview can be found in `the following YouTube video
  <https://www.youtube.com/watch?v=oK1qYdhmquY>`__.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/dg6_WhUK5Ew" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

One can see prescriptions as `enhanced constraints
<https://pip.pypa.io/en/stable/user_guide/#constraints-files>`_ but on the
server side. This way constraints can be generalized and applied also for
multiple projects for which server-side resolution can provide guidance.

.. note::

  The declarative prescription interface allows to quickly provide pipeline units
  that assist the resolution process but have limited expressive capabilities.
  For more sophisticated pipeline units one can still use the programmable
  interface.

Examples to quickly write a new prescription
============================================

Here are few prescription examples to inspire for a quick creation of new prescriptions:

* `thoth.NoSemanticInterpositionWrap <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/_python36/no_semantic_interpositioning.yaml>`__ - add a justification to the resolved software stack considering runtime environment used

* `thoth.FlaskGitHubReleaseNotesWrap <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/fl_/flask/gh_release_notes.yaml>`__ - point users to a GitHub release notes page for a package

* `thoth.StackOverflowRequestsTagWrap <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/re_/requests/so_tags.yaml>`__ - point users to a specific StackOverflow tag related to a package

* `thoth.TensorFlowGPUCUDASieve <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/te_/tensorflow/tf_cuda.yaml>`__ - adjust resolution considering CUDA available on the host

* `thoth.TensorFlowRMSciPyStep <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/te_/tensorflow/tf_rm_scipy.yaml>`_ - remove a package accidentally stated in requirements in a release

* `thoth.TensorFlow21H5pyStep <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/te_/tensorflow/tf_21_h5py.yaml>`__ - remove certain versions of a library introducing overpinning issues

* `thoth.Pillow830TypeErrorStep <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/pi_/pillow/pillow830_typeerror.yaml>`__ - prevent resolving certain combination of packages causing runtime errors (incompatible versions spotted after a release)

* `thoth.GPUNoCUDABoot <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/_generic/gpu_no_cuda.yaml>`__ - warn about mis-configured runtime environment used

* `thoth.TorchGPUIndex <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/to_/torch/gpu_index.yaml>`__ - use CUDA 11.1 enabled builds from a different Python package index than PyPI

* `thoth.HTTPServerSecurityWarnings <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/_security_warnings/http_server.yaml>`__ - warn users if they use possibly dangerous parts of libraries in production environments

* `thoth.TensorFlowGPUPseudonym <https://github.com/thoth-station/prescriptions/blob/master/prescriptions/te_/tensorflow/tf_gpu.yaml>`__ - consider another package as an alternative to the one stated in the dependency graph based on GPU enabled runtime environment

Prescriptions structure
=======================

Prescriptions are written in a form of YAML files that are maintained in a Git
repository. An example of such a directory structure can be found at
`thoth-station/prescriptions <https://github.com/thoth-station/prescriptions/>`__.

A repository with prescriptions must state a metadata file keeping generic
information for prescriptions. This file is named
``_prescription_metadata.yaml`` and metadata stated in this file are inherited
to all units declared in sub-directories living besides the metadata file.

The content of the metadata file is (an `example
<https://github.com/thoth-station/prescriptions/blob/b12d31510134a08b47e621c08d8d69977641b903/prescriptions/_prescription_metadata.yaml>`__):

.. code-block:: yaml

  prescription:
    name: <name>
    release: <release>

The value stated in ``prescription.name`` acts as a namespace for prescriptions. If
you use multiple Git repositories with prescriptions, you do not need to worry about
any naming collisions unless you make sure these prescriptions live in a separate
namespace (have different values of ``prescription.name``).

The identifier stated in ``prescription.release`` states release information
about prescriptions.

.. note::

  Check the resolution log to see what prescriptions in which versions are used
  during the resolution process.

Each sub-directory keeps information about prescriptions. It is a convention to put
package specific prescriptions into sub-directories which match package names.
Any generic or package agnostic prescriptions can be placed into
sub-directories prefixed with and underscore (e.g. ``_generic``). The name of the
YAML files are then determined based on the unit semantics written there.

.. note::

  If you are a package maintainer or you would like to follow updates for a
  specific set of prescriptions, you can add yourself to `CODEOWNERS
  <https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/creating-a-repository-on-github/about-code-owners>`__
  file and follow updates only for a specific sub-directory.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/ocCVghdx7eM" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

Unit schema
===========

.. note::

  See `schema.py file in adviser's implementation
  <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__ for a more detailed schema overview.

Units are stated in ``units`` listing in the corresponding YAML file respecting
unit's base type:

.. code-block:: yaml

  units:
    boots: []
    pseudonyms: []
    sieves: []
    steps: []
    strides: []
    wraps: []

Each unit, regardless of its type, has the following schema:

.. code-block:: yaml

  name: '<unit_name>'
  type: '<unit_type>'
  should_include:
    <should_include_section>
  match:
    <match_section>
  run:
    <run_section>

The semantics behind entries:

``name``
########

Name of the unit that uniquely identifies the unit of the specific type within the
prescription namespace in which unit is declared.

All the units created based on prescription live in their own namespace that is
specified by the ``name`` of the prescription. This makes sure prescriptions do
not clash even if multiple prescriptions are supplied.

``type``
########

Each prescription pipeline unit can be of a base type ``boot``, ``pseudonym``,
``sieve``, ``step``, ``stride`` and ``wrap`` or any derived type from the base
types. The derived types provide certain additional functionality in opposite
to the base types. See corresponding prescription pipeline unit documentation
for available types.

``should_include``
##################

See :ref:`the following documentation <prescription_should_include>` for more info.

``match``
#########

This section is specific to a pipeline unit type used.

``run``
#######

This section is specific to a pipeline unit type used.
