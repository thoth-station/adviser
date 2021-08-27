.. _prescription_sieves:

Sieve prescription pipeline unit
--------------------------------

Declaring :ref:`pipeline units of type sieve <sieves>`.

.. note::

  The pipeline unit is registered based on ``should_include``
  directive - :ref:`see documentation for more info <prescription_should_include>`

The following example shows all the configuration options that can be applied
for a sieve pipeline unit type. See respective sections described below for more
info.

.. code-block:: yaml

  name: SieveUnit
  type: sieve
  should_include:
    # See should_include section for more info.
  match:                                            # Criteria to trigger run of this pipeline unit.
    package_version:                                # Any package matching this criteria will be filtered out from the resolution.
      name: flask                                   # Name of the package that should be filtered out and an alternative should be found.
      version: '>1.0,<=1.1.0'                       # Version specifier for which the sieve should be run. If not provided, defauts to any version.
      index_url: 'https://pypi.org/simple'          # Package source index for which the sieve should be run. If not provided, defaults to any index. Can be negated using "not".
      develop: false                                # If specified, match development or not development dependencies.
  run:
    log:                                            # Optional text printed to logs when the unit gets called.
      message: Some text printed to log on pipeline unit run
      type: WARNING
    stack_info:                                     # Information printed to the recommended stack report.
    - type: WARNING
      message: Hello, world
      link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

.. note::

  For a complete schema `check the schema.py file in adviser's
  implementation <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__.

This pipeline unit removes specific releases. If no releases remain, the resolver
will try to find another resolution. If you wish to completely remove requirement
on a package, check :ref:`SkipPackageSieve <skip_package_sieve>`.

Sieve ``match.package_version``
###############################

Specifies a package version that should be matched to execute the given unit during
the resolution pipeline run.

The package is described by:

* ``name`` - name of the Python package that should be matched, any package
  name matched if not provided
* ``version`` - version in a form of version specification to be matched, any
  version matched if not provided
* ``index_url`` - URL of the Python package index from where the given package
  is consumed, matches any index if not provided; can be negated using "not"
* ``develop`` - optional, if provided it additionally specifies if the dependency
  should or should not be a development dependency

.. note::

  *Example:*

  .. code-block:: yaml

    name: SieveUnit
    type: sieve
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - security
    match:
      package_version:
        index_url: 'https://pypi.org/simple'
    run:
      stack_info:
      - type: WARNING
        message: "Filtering out all the packages from PyPI for security reasons"
        link: "https://pypi.org/simple"

It is also possible to match the same pipeline unit for multiple match criteria
provided by providing match listing. In that case, multiple pipeline units with
different ``match`` configuration (but same ``run`` section) will be registered to
the resolution pipeline:

.. note::

  *Example:*

  .. code-block:: yaml

    name: SieveUnit
    type: sieve
    should_include:
      adviser_pipeline: true
    match:
    - package_version:
        name: gnumpy
    - package_version:
        name: dumpy
    - package_version:
        name: bumpy
    - package_version:
        name: pansas
    run:
      stack_info:
      - type: WARNING
        message: "Filtering out known typo-squatted packages"
        link: "https://pypi.org/simple"

Sieve ``run.log``
#################

Print the given message to logs if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Sieve ``run.stack_info``
########################

See :ref:`boot's pipeline unit stack info <boot_stack_info>` which semantics is
shared with this unit.


.. _skip_package_sieve:
SkipPackage sieve prescription pipeline unit
--------------------------------------------

A derived sieve type that skips a package in the dependency graph.
Skipping the given package causes that the skipped dependency and the whole
sub-graph of dependencies introduced by the skipped dependency is removed. This
unit can be used to remove accidentally added requirements.

.. note::

  *Example:*

  .. code-block:: yaml

    name: SkipPackageSieve
    type: sieve.SkipPackage   # Mind the type.
    should_include:
       # See should_include section for more info.
    match:
       package_name: scipy
    run:
      log:
        message: Package SciPy removed from the stack
        type: WARNING

      stack_info:
      - type: WARNING
        message: Package SciPy removed from the stack
        link: "https://github.com/tensorflow/tensorflow/issues/35709"


All the directives from the base sieve are applicable with the same semantics
also for ``sieve.SkipPackage``. The difference is in the pipeline unit semantics;
note the ``type`` to differentiate the derived type from the base sieve type.

If you wish to skip a package considering also other dependencies, check
:ref:`step of type step.SkipPackage <skip_package_step>`.
