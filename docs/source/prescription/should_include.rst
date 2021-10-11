.. _prescription_should_include:

Including a prescription unit
-----------------------------

Each pipeline unit states conditions that should be met in order to
be registered in the resolution process. This ``should_include`` part
is agnostic to the pipeline unit type (separation of the actual pipeline
unit logic).

.. image:: https://thoth-station.ninja/assets/adviser/pipeline_builder.gif
   :target: https://thoth-station.ninja/assets/adviser/pipeline_builder.gif
   :alt: Pipeline builder building the pipeline configuration.

.. note::

  For a complete schema `check the schema.py file in adviser's
  implementation <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__.

``should_include.times``
========================

Number of times the given unit should be included in the resolution process.

Possible values:

* ``1`` - the given pipeline unit should be included once in the resolution
  process if all the criteria for including it match (default)

* ``0`` - the given pipeline unit will not be included in the resolution
  process - the given pipeline unit is off even thought it is stated in the
  YAML file

``should_include.adviser_pipeline``
===================================

Boolean stating whether the given pipeline pipeline unit will be part of
"adviser" pipeline used for computing Thoth's recommendations.

Possible values:

* ``false`` - the given pipeline unit will not be part of the resolver pipeline
  when computing advises (default)

* ``true`` - the given pipeline unit will be part of the resolver pipeline
  when computing advises

``should_include.recommendation_types``
=======================================

A list of recommendation types that should be matched if the unit is registered
for the adviser resolution pipeline.

Alternatively, the list can be wrapped to a "not" statement which inverts
the logic.

If ``adviser_pipeline`` is set to ``false``, this configuration option has no
effect.

See `the listing of recommendation types available
<https://thoth-station.ninja/recommendation-types/>`__.

``should_include.dependency_monkey_pipeline``
=============================================

Boolean stating whether the given pipeline pipeline unit will base part of
:ref:`Dependency Monkey <dependency_monkey>` pipeline used for `data
acquisition and generation on Amun
<https://github.com/thoth-station/amun-api/>`__.

Possible values:

* ``false`` - the given pipeline unit will not be part of the resolver pipeline
  used for Dependency Monkey (default)

* ``true`` - the given pipeline unit will be part of the resolver pipeline
  when running Dependency Monkey

``should_include.decision_types``
=================================

A list of decision types that should be matched if the unit is registered for
the :ref:`Dependency Monkey <dependency_monkey>` resolution pipeline used for
`data acquisition on Amun <https://github.com/thoth-station/amun-api/>`__.

Alternatively, the list can be wrapped with a "not" statement which inverts
the logic.

If ``dependency_monkey_pipeline`` is set to ``false``, this configuration
option has no effect.

``should_include.authenticated``
================================

Configure inclusion of the given pipeline unit based on authenticated requests
to the recommendation engine.

Possible values:

* ``null`` - default, the pipeline unit will be registered regardless
  of authentication

* ``false`` - the pipeline unit will be registered only if *unauthenticated*
  request is done to the recommendation engine

* ``true`` - the pipeline unit will be registered only if *authenticated*
  request is done to the recommendation engine

``should_include.library_usage``
================================

Library calls that should be present to include the pipeline unit. This
creates an ability to include a pipeline unit only if some parts of a
library are used that affect the application.

.. note::

  *Example:*

  .. code-block:: yaml

    library_usage:
      # from flask import Flask
      flask:
        - flask.Flask
      # Match if anything is imported from tensorflow.keras.
      tensorflow:
        - tensorflow.keras.*

The use of libraries is statically checked on client side using
`invectio library <https://github.com/thoth-station/invectio>`__.

``should_include.dependencies``
===============================

Dependencies on other pipeline units. All the stated pipeline units have to be
registered (``should_include`` has to be evaluated as ``true``) as listed
dependencies are pre-requisites to register the stated pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    should_include:
      dependencies:
        boots:
          - thoth.ExampleBoot
          - CoreBoot

  This part of the ``should_include`` section is specific to a unit that states
  dependencies on two units of type :ref:`boot <boots>`. ``ExampleBoot`` is a boot
  pipeline unit from prescription named ``thoth`` and ``CoreBoot`` is a boot
  provided by the adviser Python implementation (corresponds to a name of the
  Python class).

Referencing unknown units evaluates always to ``false``.

If no dependencies are stated, the given pipeline unit is not dependent on
any pipeline unit.

``should_include.dependencies.boots``
#####################################

A list of :ref:`boot pipeline units <prescription_boots>` that need to be
present in the resolution process. Referenced by respective unit name and
optional prescription name for referencing units from prescriptions (see above
for more info).

``should_include.dependencies.pseudonyms``
##########################################

A list of :ref:`pseudonym pipeline units <prescription_pseudonyms>` that need
to be present in the resolution process.  Referenced by respective unit name
and optional prescription name for referencing units from prescriptions (see
above for more info).

``should_include.dependencies.sieves``
######################################

A list of :ref:`sieve pipeline units <prescription_sieves>` that need to be
present in the resolution process.  Referenced by respective unit name and
optional prescription name for referencing units from prescriptions (see above
for more info).

``should_include.dependencies.steps``
#####################################

A list of :ref:`step pipeline units <prescription_steps>` that need to be
present in the resolution process.  Referenced by respective unit name and
optional prescription name for referencing units from prescriptions (see above
for more info).

``should_include.dependencies.strides``
#######################################

A list of :ref:`stride pipeline units <prescription_strides>` that need to be
present in the resolution process.  Referenced by respective unit name and
optional prescription name for referencing units from prescriptions (see above
for more info).

``should_include.dependencies.wraps``
#####################################

A list of :ref:`wrap pipeline units <prescription_wraps>` that need to be
present in the resolution process.  Referenced by respective unit name and
optional prescription name for referencing units from prescriptions (see above
for more info).

``should_include.labels``
=========================

Labels introduce a mechanism to register pipeline units only for requests that
state the given label. An example can be a CI system that is asking for an
advise and labels the request with ``requester=ci``. In such a case, the
resolution engine includes pipeline units that are specific to the CI system
with the corresponding label set. Other pipeline units that do not provide any
labels are included by default.

If multiple labels are stated on a pipeline unit prescription, the prescription
pipeline unit is registered if *any* label matches.

.. note::

  *Example:*

  Register the given pipeline unit if ``team=thoth`` or ``requester=ci``
  were provided:

  .. code-block:: yaml

    labels:
      team: thoth
      requester: ci

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/eoJIfQip_6M" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

This feature can be used to centralize knowledge about packages that should
be resolved under certain conditions (ex. `supported releases in
a product <https://www.youtube.com/watch?v=4vIpVxe7-9c>`__).

``should_include.runtime_environments``
=======================================

Matching runtime environment configurations for which pipeline units should be
included in the resolution process. This configuration section is meant for
units that are specific to hardware or software available.

``should_include.runtime_environments.operating_systems``
#########################################################

A list of operating systems for which the pipeline unit should be included.
Each entry optionally states ``name`` (operating system name) and ``version``
(operating system version). Not providing any of the two means matching *any*
value.

.. note::

  *Example:*

  .. code-block:: yaml

    operating_systems:
      - name: rhel     # matches Red Hat Enterprise Linux in any version
      - name: fedora   # matches Fedora in version 33
        version: 33

``should_include.runtime_environments.hardware``
################################################

Matching hardware available when running the application. This
configuration basically creates a matrix of hardware that should be
available on user's side to register the given pipeline unit in the
resolution process.

Alternatively, the list can be wrapped with a "not" statement which inverts
the logic.

.. note::

  *Example:*

  .. code-block:: yaml

    hardware:
      # Matches any GPU available:
      - gpu_models:
          not: null

      # Matches no GPU available:
      - gpu_models: null

      # Matches any combination of CPU models 8/9 and CPU families 1/2.
      - cpu_families: [1, 2]
        cpu_models: [9, 8]

      # Matches CPU family 1, CPU model 9 running on GPU "Foo" or GPU "Bar",
      - cpu_families: [1]
        cpu_models: [9]
        gpu_models:
          - Foo
          - Bar

      # Matching any CPU family except for 1.
      - cpu_families:
          not: [1]

      # Matching CPU flags - all flags must be available on the CPU to register the unit.
      - cpu_flags: ["avx2", "avx512"]

      # Do NOT register the unit if AVX2 or AVX512 are available.
      - cpu_flags:
         not: ["avx2", "avx512"]

See `CPU database available in adviser's implementation
<https://github.com/thoth-station/adviser/blob/master/thoth/adviser/data/cpu_db.yaml>`__
for a full listing of CPUs available and flags they provide.

``should_include.runtime_environments.python_version``
######################################################

Python version specifier that needs to be matched for including the
given pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    # Match when running 3.8 or 3.9:
    python_version: ">=3.8,<=3.9"

  *Example:*

  .. code-block:: yaml

    # Match when NOT running 3.8:
    python_version: "!=3.8"

If this configuration option is not provided, it defaults to any
Python version.

Python version is always in form of ``<major>.<minor>``. Patch versions
are not considered.

``should_include.runtime_environments.cuda_version``
####################################################

Nvidia CUDA versions that need to be matched for including the given
pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    # Match when running from CUDA 9.0 to 9.2.
    cuda_version: ">=9.0,<=9.2"

    # Match if CUDA is available:
    cuda_version: ">=0.0"

    # Match if no CUDA is available:
    cuda_version: null

  If this configuration option is not provided, it defaults to any
  CUDA version - even if none available.

A special value of ``null`` means no CUDA version available.

``should_include.runtime_environments.platforms``
#################################################

A list of platforms for which the given pipeline unit should be registered.

Alternatively, the list can be wrapped with a "not" statement which inverts
the logic.

.. note::

  *Example:*

  .. code-block:: yaml

    platforms:
      - linux-x86_64

    platforms:
      # Any except for linux-x86_64
      not: [linux-x86_64]

If this configuration option is not supplied, it defaults to *any* platform.

``should_include.runtime_environments.openblas_version``
########################################################

`OpenBLAS <https://www.openblas.net/>`__ versions that need to be
matched for including the given pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    # Match when running OpenBLAS 0.3.0, 0.3.13.
    openblas_version: ">=0.3.0,<=0.3.13"

If this configuration option is not provided, it defaults to any OpenBLAS
version - even none available.

``should_include.runtime_environments.openmpi_version``
#######################################################

`OpenMPI <https://www.open-mpi.org/>`__ versions that need to be matched for
including the given pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    # Match when running OpenMPI from 4.0.5 to 4.1.0.
    openmpi_version: ">=4.0.5,<=4.1.0"

If this configuration option is not provided, it defaults to any OpenMPI
version - even none available.

``should_include.runtime_environments.cudnn_version``
#####################################################

Nvidia cuDNN versions that need to be matched for including the given
pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    # Match when running cuDNN from 7.6.5 to 8.0.5.
    cudnn_version: ">=7.6.5,<=8.0.5"

If this configuration option is not provided, it defaults to any cuDNN version
- even none available.

``should_include.runtime_environments.mkl_version``
###################################################

`Intel MKL
<https://software.intel.com/content/www/us/en/develop/articles/oneapi-math-kernel-library-release-notes.html>`__
versions that need to be matched for including the given pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    # Match when running MKL 2021.1
    mkl_version: "==2021.1"

If this configuration option is not provided, it defaults to any MKL
version - even none available.

``should_include.runtime_environments.base_images``
###################################################

A list of base images that are used as a runtime environment when running the
application. These base images map to `Thoth's S2I container images
<https://github.com/thoth-station/s2i-thoth>`__ or container images produced by
the `AICoE-CI pipeline <https://github.com/AICoE/aicoe-ci>`__.

Alternatively, the list can be wrapped with a "not" statement which inverts
the logic (the given container image is *not* used).

The container image tag can be omitted, in such cases, any tag is matched.

Container image tags can be also specified by prefix, for example ``v1.*`` matches
any tags that are prefixed with ``v1.`` (ex. ``v1.0.0``, ``v1.1.2``, etc).

.. note::

  *Example:*

  .. code-block:: yaml

    base_images:
      # Match UBI8 Python 3.8 container environment or UBI8 Python 3.6 container
      # environment in specific versions.
      - quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0
      - quay.io/thoth-station/s2i-thoth-ubi8-py36:v0.8.1

    base_images:
      # Do not match UBI8 Python 3.8 container environment and UBI8 Python 3.6
      # container environment in specific versions.
      not:
        - quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0
        - quay.io/thoth-station/s2i-thoth-ubi8-py36:v0.8.1

    base_images:
      # Match UBI8 Python 3.8 container environment (any tag) or UBI8 Python 3.6 container
      # environment in tags 2.2.
      not:
        - quay.io/thoth-station/s2i-thoth-ubi8-py38
        - quay.io/thoth-station/s2i-thoth-ubi8-py36:v2.2.*

    base_images:
      # Do not match UBI8 Python 3.8 container environment and in any v1 tag release.
      not:
        - quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.*

``should_include.runtime_environments.abi``
###########################################

A list of ABI that have to be present in the runtime environment.

Alternatively, the list can be wrapped with a "not" statement which inverts
the logic.

.. note::

  *Example:*

  .. code-block:: yaml

    abi:
      # Include the given pipeline unit if the following two image symbols are
      # present in the environment.
      - GLIBC_2.4
      - GNUTLS_3_6_6

  .. code-block:: yaml

    abi:
      # Include the given pipeline unit if the following image symbol
      # is **not** present in the environment.
      not:
        - GLIBC_2.4

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/L_-ulzMSf1o" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

``should_include.runtime_environments.rpm_packages``
####################################################

A list of RPM packages that should or should *not* be present
in the runtime environment in order to register the given pipeline unit.

An RPM package can be specified using the following fields:

* ``package_identifier`` - fully qualified package
  identifier (e.g. ``gcc-c++-8.3.1-5.1.el8.x86_64``)

* ``package_name`` - name of the package ``gcc-c++`` (mandatory)

* ``epoch`` - used for clarifying version history

* ``package_version`` - package version identifier (e.g. ``8.3.1``)

* ``release`` - RPM package release (e.g. ``5.1.el8``)

* ``arch`` - architecture (e.g. ``x86_64``)

* ``src`` - boolean describing whether the given package is a source
  distribution (e.g. ``false``)

See `RPM packaging guide <https://rpm-packaging-guide.github.io/>`__ for more
information on *NEVRA* (Name-Epoch-Version-Release-Architecture).

If any field is not provided (except for ``package_name`` which is mandatory)
any value on the runtime environment side is evaluated as matching.

.. note::

  *Example:*

  .. code-block:: yaml

    rpm_packages:
      # Include the given pipeline unit if git is present (any version)
      # and gcc+c++ based on package specification supplied.
      - package_name: git
      - arch: x86_64
        epoch: null
        package_identifier: gcc-c++-8.3.1-5.1.el8.x86_64
        package_name: gcc-c++
        package_version: 8.3.1
        release: 5.1.el8
        src: false

  .. code-block:: yaml

    rpm_packages:
      # Include the given pipeline unit if git is **not** present in the
      # runtime environment.
      not:
        - package_name: git

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/7Xo4eQ8TNSM" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

``should_include.runtime_environments.python_packages``
#######################################################

A list of Python packages that should or should *not* be present
in the runtime environment in order to register the given pipeline unit.

Information about Python package can be specified using the following fields.

* ``name`` - mandatory, name of the package (e.g. ``jupyterhub``)

* ``version`` - package version specifier (e.g. ``~=1.4.1``)

* ``location`` - a regular expression describing where the given package should
  be installed. An example use of this option is detecting Python packages
  that are installed inside Python s2i environment. The regular expression is
  matched using
  `re.fullmatch <https://docs.python.org/3/library/re.html#re.fullmatch>`__.

If ``version`` is not provided, any version present registers
the given pipeline unit.

If ``location`` is not provided, any location is considered. Note that the detection
of Python packages does not enforce their availability on ``PYTHONPATH``.

.. note::

  *Example:*

  .. code-block:: yaml

    python_packages:
      # Register if jupyterhub~=1.4.1 is present in s2i virtualenv
      # and micropipenv<=1.1.0 is installed regardless of its location.
      - name: jupyterhub
        version: "~=1.4.1"
        location: "^/opt/app-root/.*"
      - name: micropipenv
        version: <=1.1.0

  .. code-block:: yaml

    python_packages:
      # Include the given pipeline unit if jupyterhub is **not** present in the
      # runtime environment.
      not:
        - name: jupyterhub

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/y02mxZxm-5U" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

`See also addition <https://www.youtube.com/watch?v=30w35P7Jqbg>`__ to the
video listed above.
