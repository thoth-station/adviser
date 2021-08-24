.. _prescription_boots:

Boot prescription pipeline unit
-------------------------------

Declaring :ref:`pipeline units of type boot <boots>`.

.. note::

  The pipeline unit is registered based on ``should_include``
  directive - :ref:`see documentation for more info <prescription_should_include>`.

The following example shows all the configuration options that can be applied
for a boot prescription pipeline unit type. See respective sections described
below for more info. Also note, the example shows all the options that can be
supplied and is not semantically valid:

.. code-block:: yaml

  name: BootUnit
  type: boot
  should_include:
    # See should_include section for more info.
  match:                                            # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_name is provided.
    package_name: flask                             # Name of the package that needs to be present in the direct dependency listing to run this unit.
  run:
    stack_info:                                     # Information printed to the recommended stack report.
      - type: ERROR
        message: Unable to perform this operation
        link: 'https://thoth-station.ninja'         # A link to stack info or a link to a web page.

    # Configuration of prematurely terminating the resolution process - the
    # message will be reported to the user. If this configuration option is not
    # set, the resolver will not terminate when running this unit.
    eager_stop_pipeline: Terminating resolution as 'flask' is in direct dependencies

     # Configuration of prematurely terminating the resolution process.
    not_acceptable: Cannot include this package

    log:
      message: Some text printed to log on pipeline unit run
      type: WARNING

.. note::

  For a complete schema `check the schema.py file in adviser's
  implementation <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__.

Boot ``match``
##############

Optional, the match section allows to define a name of the package that should
be present in direct dependencies to trigger run of the pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    name: BootUnit
    type: boot
    should_include:
      adviser_pipeline: true
    match:
      package_name: flask
    run:
      log:
        type: WARNING
        message: Found package 'flask' in the direct dependency listing

It is also possibly to match the given pipeline unit for multiple package
names by providing a match listing. In that case, multiple pipeline units with
different ``match`` configuration (but same ``run`` section) will be registered to
the resolution pipeline:

.. note::

  *Example:*

  .. code-block:: yaml

    name: BootUnit
    type: boot
    should_include:
      adviser_pipeline: true
    match:
    - package_name: flask
    - package_name: numpy
    run:
      log:
        type: WARNING
        message: Found package 'flask' or 'numpy' in the direct dependency listing

.. _boot_stack_info:

Boot ``run.stack_info``
#######################

Optional a list of information added to the "stack info" field that is
:ref:`specific for the application stack <stack_info>`.

Each entry in the list is specified by three attributes:

* ``type`` - any of ``INFO``, ``WARNING``, and ``ERROR`` specifying severity of the produced stack information
* ``message`` - a message in a free text form printed to users
* ``link`` - a link to a document describing more information in detail

The link can be in a form of a valid HTTP or HTTPS URL or a string which
:ref:`references justifications <jl>` available at
`thoth-station.ninja/justifications
<https://thoth-station.ninja/justifications>`__.

.. note::

  *Example:*

  .. code-block:: yaml

    name: BootUnit
    type: boot
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - performance
      runtime_environments:
        operating_systems:
        - name: rhel
          version: '8'
        python_version: '==3.6'
    run:
      stack_info:
      - type: WARNING
        message: It is recommended to switch to Python 3.8 to improve performance
        link: 'https://developers.redhat.com/blog/2020/06/25/red-hat-enterprise-linux-8-2-brings-faster-python-3-8-run-speeds/'

Boot ``run.eager_stop_pipeline``
################################

An optional string describing exception that should be raised during resolver
boot causing the resolution process to halt.

.. note::

  *Example:*

  .. code-block:: yaml

    name: BootUnit
    type: boot
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - security
      runtime_environments:
        operating_systems:
        - name: fedora
    run:
      eager_stop_pipeline: Security recommendation types are disabled for Fedora, use RHEL instead

.. _boot_run_log:

Boot ``run.log``
################

Print the given message to logs if the pipeline unit is included and run.

The log entry is specified by two attributes:

* ``type`` - any of ``INFO``, ``WARNING``, and ``ERROR`` specifying severity of the produced message
* ``message`` - a message in a free text form printed to resolver log

.. note::

  *Example:*

  .. code-block:: yaml

    name: BootUnit
    type: boot
    should_include:
      adviser_pipeline: true
      dependency_monkey_pipeline: true
    run:
      log:
        message: Using prescriptions in the resolution process
        type: INFO
