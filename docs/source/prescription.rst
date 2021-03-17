.. _prescription:

Declarative prescription for resolver
-------------------------------------

The implementation allows to declaratively specify pipeline units that should
be included in the resolver pipeline without actually implementing any Python
classes. The document below describes core mechanics behind creating such
prescription for the resolver. Note the declarative prescription allows to
quickly provide pipeline units that assist the resolution process but have
limited expressive capabilities. For more sophisticated pipeline units one can
still use the programmable interface.

.. note::

  All the units created based on prescription live in their own namespace. Names
  cannot clash when different units of **different** type share the name. Also,
  they cannot clash with pipeline unit names provided by the Python
  implementation.

  However, it's recommended not to use same unit names for different units.

One can see prescriptions as `enhanced constraints
<https://pip.pypa.io/en/stable/user_guide/#constraints-files>`_ but on the server
side. This way constraints can be generalized and applied also for multiple projects
for which server-side resolution can provide guidance.

.. note::

  Prescription YAML specification provides unit abstractions that map to their
  Python code implementation. If you wish to create your own unit declaration in
  the YAML configuration suitable for your needs, just declare your YAML unit
  and provide its Python implementation. Core pipeline units can serve as
  a base for the implementation.

Prescription YAML v1
====================

Here is a core part of the prescription YAML document:

.. code-block:: yaml

  apiVersion: thoth-station.ninja/v1
  kind: prescription
  spec:
    release: 2021.03.30  # A calendar release of the prescription.
    units:
      boots: []
      pseudonyms: []
      sieves: []
      steps: []
      strides: []
      wraps: []
    wisdom:  # Any YAML serialized data that can be used in units using YAML anchors and aliases.

Each unit entry in the respective ``units`` section corresponding to a pipeline
unit type declaratively describes a unit and its action that should be done
when conditions are met.

The core scheme for a unit declaration is:

.. code-block:: yaml

 - name: UnitName       # A unique unit name.
   type: '<unit_type>'  # One of boot, sieve, step, stride, wrap, pseudonym.
   should_include:      # Section describing when the unit should be included.
     <should_include_section>
   run:
     <run_section>      # Section describing the actual unit logic when it is run.

Registering pipeline units - ``should_include``
===============================================

The document below describes how pipeline units can be configured for inclusion
in the resolution process. This section is shared for pipeline units of any type.

.. code-block:: yaml

  should_include:
    times: 1                           # How many times should be the pipeline unit included (accepts 0 or 1).
    adviser_pipeline: true             # Register in the adviser resolution, defaults to false if not provided.
    dependency_monkey_pipeline: true   # Register for Dependency Monkey resolution, defaults to false if not provided.
    dependencies:                      # Pipeline units that should be included in the configuration prior to including this unit. Defaults to no dependency restrictions if not provided.
      boots:
        - SomeBoot1
        - SomeBoot2
      pseudonyms:
      sieves:
      steps:
      strides:
      wraps:
    recommendation_types:              # Recommendation types for which the pipeline unit should be included if adviser_pipeline=true. Defaults to all available if not provided.
      - latest
      - performance
      - security
      - stable
      - testing
    decision_types:                    # Decision types for which the pipeline unit should be included if dependency_monkey_pipeline=true. Defaults to all available if not provided.
      - random
      - all
    runtime_environments:              # User's runtime environment used for which the resolution is triggered.
      operating_systems:               # Name and version of the user's operating system.
        - name: 'rhel'
          version: '8'
      hardware:                        # Hardware information present on the user's machine.
        # Included if any combination matches hardware configuration used.
        - cpu_families: [1]
          cpu_models: [2]
          gpu_models:
            - 'Nvidia GeForce GTX 1060'
      python_versions:                # Python interpreter version used to run the application.
        - '3.8'
        - '3.9'
      cuda_versions: ['9.0']
      platforms: ['linux-x86_64']
      openblas_versions: ['0.3.13']
      openmpi_versions: ['4.1']
      cudnn_versions: ['8.1.0']
      mkl_versions: ['2021.1.1']
      base_images:
        - 'quay.io/thoth-station/s2i-thoth-ubi8-py36:v1.0.0'  # Base image used for running the application.

The configuration options not stated do not enforce the given configuration.
For example, not stating ``python_version`` means that the pipeline unit will
not consider Python interpreter version running as a restriction to be
registered.

Boots
=====

See :ref:`boot pipeline unit <boots>` for more information on semantics.

.. code-block:: yaml

  name: BootUnit
  type: boot
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_name is provided.
      package_name: flask                           # Name of the package that needs to be present in the direct dependency listing to run this unit.

    stack_info:                                     # Information printed to the recommended stack report.
      - type: ERROR
        message: "Unable to perform this operation"
        link: https://thoth-station.ninja           # A link to stack info or a link to a web page.

    # Configuration of prematurely terminating the resolution process - the
    # message will be reported to the user. If this configuration option is not
    # set, the resolver will not terminate when running this unit.
    eager_stop_pipeline: "Terminating resolution as 'flask' is in direct dependencies."

     # Configuration of prematurely terminating the resolution process.
    not_acceptable: "Cannot include this package"

    log:
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"


Pseudonyms
==========

See :ref:`pseudonym pipeline unit <pseudonyms>` for more information on
semantics.

.. code-block:: yaml

  name: PseudonymUnit
  type: pseudonym
  should_include:                                   # See should_include section.
  run:
    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the pseudonym pipeline unit if no package_version is provided.
      package_version:
        name: flask                                 # Mandatory, name of the package for which pseudonym should be registered.
        version: '>1.0,<=1.1.0'                      # Version specifier for which the pseudonym should be run. If not provided, defauts to any version.
        index_url: 'https://pypi.org/simple'        # Package source index for which the pseudonym should be run. If not provided, defaults to any index.

    yield:
      # Pseudonym that should be registered.
      package_version:
        name: flask                                 # Mandatory, name of the pseudonym package.
        version: '==1.2.0'                          # Version of the pseudonym in a locked form.
        index_url: 'https://pypi.org/simple'        # Package source index where the pseudonym is hosted.

The pseudonym is registered for the specified criteria. The unit derived out of
this declarative prescription will make sure the package yielded is known to
the resolver.

.. note::

  An example pipeline unit that suggests ``intel-tensorflow`` coming from PyPI as an alternative to ``tensorflow``:

  .. code-block:: yaml

    name: PseudonymUnit
    type: pseudonym
    should_include:
      times: 1
      adviser_pipeline: true
    run:
      match:
        package_name: tensorflow

      stack_info:
        - message: "Considering also intel-tensorflow as an alternative to tensorflow"
          type: "INFO"
          link: "https://pypi.org/project/intel-tensorflow"

      yield:
        package_version:
          name: intel-tensorflow
          index-url: "https://pypi.org/simple"

Sieves
======

See :ref:`sieve pipeline unit <sieves>` for more information on
semantics.

.. code-block:: yaml

  name: SieveUnit
  type: sieve
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the sieve pipeline unit if no package_version is provided.
      package_version:                              # Any package matching this criteria will be filtered out from the resolution.
        name: flask                                 # Name of the package for which the unit should be registered.
        version: '>1.0,<=1.1.0'                      # Version specifier for which the sieve should be run. If not provided, defauts to any version.
        index_url: 'https://pypi.org/simple'        # Package source index for which the sieve should be run. If not provided, defaults to any index.

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

.. note::

  An example pipeline unit that filters out ``pysaml2`` with the reported CVE.

  .. code-block:: yaml

    name: SieveUnit
    type: sieve
    should_include:
      times: 1
      adviser_pipeline: true
      recommendation_types:
        - security
        - stable
    run:
      match:
        package_version:
          name: pysaml2
          version: '<6.5.0'
          index_url: 'https://pypi.org/simple'

      stack_info:
        - type: WARNING
          message: "Not considering package pysaml2 based on vulnerability present"
          link: "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-21238"

Steps
=====

See :ref:`step pipeline unit <steps>` for more information on
semantics.

.. code-block:: yaml

  name: StepUnit
  type: step
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_version is provided.
      package_version:                              # Any package matching this criteria will be filtered out from the resolution.
        name: flask                                 # Name of the package for which the unit should be registered.
        version: '>1.0,<=1.1.0'                      # Version specifier for which the sieve should be run. If not provided, defaults to any version.
        index_url: 'https://pypi.org/simple'        # Package source index for which the sieve should be run. If not provided, defaults to any index.

      state:                                        # Optional, resolver internal state to match for the given resolution step.
        resolved_dependencies:
          - name: werkzeug                          # Dependencies that have to be present in the resolved state.
            locked_version: "1.0.0"
            index_url: 'https://pypi.org/simple'

    score: 0.42                                     # Score assigned to the step performed in the resolution.
    justification:
      - type: INFO
        message: "Hello, Thoth!"
        link: https://thoth-station.ninja

    not_acceptable: "Bad package inclusion"         # Block including certain package during the resolution.

    # Configuration of prematurely terminating the resolution process.
    eager_stop_pipeline: "Stop pipeline"

    multi_package_resolution: false                 # Run this pipeline multiple times when matched mutliple times. Defaults to false if not provided.

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.


.. note::

  An example pipeline unit that filters out any ``tensorflow~=2.4.0`` when
  ``numpy==1.19.1`` is in already resolved dependencies.

  .. code-block:: yaml

    name: StepUnit
    type: step
    should_include:
      times: 1
      adviser_pipeline: true
    run:
      match:
        package_version:
          # Considering builds available also on other indexes than PyPI.
          name: tensorflow
          version: '~=2.4.0'

        state:
          resolved_dependencies:
            - name: numpy
              locked_version: "==1.19.1"
              index_url: 'https://pypi.org/simple'

      not_acceptable: "NumPy==1.19.5 is causing issues when used with TensorFlow 2.4"
      multi_package_resolution: true

      stack_info:
        - type: WARNING
          message: "NumPy==1.19.5 is causing issues when used with TensorFlow 2.4"
          link: "https://thoth-station.ninja/j/tf_24_np.html"


Strides
=======

See :ref:`strides pipeline unit <strides>` for more information on
semantics.

.. code-block:: yaml

  name: StrideUnit
  type: stride
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_version is provided.
      state:                                        # Optional, resolver internal state to match for the given stride.
        resolved_dependencies:
          - name: werkzeug                          # Dependencies that have to be present in the resolved state.
            version: "~=1.0.0"
            index_url: 'https://pypi.org/simple'

    not_acceptable: "Bad package inclusion"         # Block resolving the given stack.

    # Configuration of prematurely terminating the resolution process.
    eager_stop_pipeline: "Stop pipeline"

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

Wraps
=====

See :ref:`wrap pipeline unit <wraps>` for more information on
semantics.

.. code-block:: yaml

  name: WrapUnit
  type: wrap
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_version is provided.
      state:                                        # Optional, resolver internal state to match for the given stride.
        resolved_dependencies:
          - name: werkzeug                          # Dependencies that have to be present in the resolved state.
            version: ">=1.0.0,<2.5.0"
            index_url: 'https://pypi.org/simple'

    not_acceptable: "Bad package inclusion"         # Block resolving the given stack.

    # Configuration of prematurely terminating the resolution process.
    eager_stop_pipeline: "Stop pipeline"

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

    justification:
      - type: INFO
        message: "Hello, Thoth!"
        link: https://thoth-station.ninja
