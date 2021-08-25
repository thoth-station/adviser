.. _prescription_pseudonyms:

Pseudonym prescription pipeline unit
------------------------------------

Declaring :ref:`pipeline units of type pseudonym <pseudonyms>`.

.. note::

  The pipeline unit is registered based on ``should_include``
  directive - :ref:`see documentation for more info <prescription_should_include>`.

The following example shows all the configuration options that can be applied
for a pseudonym pipeline unit type. See respective sections described below for more
info:

.. code-block:: yaml

  name: PseudonymUnit
  type: pseudonym
  should_include:
    # See should_include section for more info.
  match:                                            # Criteria to trigger run of this pipeline unit.
    package_version:
      name: flask                                   # Mandatory, name of the package for which pseudonym should be registered.
      version: '>1.0,<=1.1.0'                       # Version specifier for which the pseudonym should be run. If not provided, defaults to any version.
      index_url: 'https://pypi.org/simple'          # Package source index for which the pseudonym should be run. If not provided, defaults to any index. Can be negated using "not".
      develop: false                                # If specified, match development or not development dependencies.
  run:
    log:                                            # Optional text printed to logs when the unit gets called.
      message: Some text printed to log on pipeline unit run
      type: WARNING
    stack_info:                                     # Information printed to the recommended stack report.
    - type: WARNING
      message: Hello, world!
      link: 'https://thoth-station.ninja'           # A link to justifications or a link to a web page.
    yield:
      # Pseudonym that should be registered.
      yield_matched_version: true                   # If set to true, use version that was matched instead of the one provided in the locked_version part.
      package_version:
        name: flask                                 # Mandatory, name of the pseudonym package.
        locked_version: '==1.2.0'                   # Version of the pseudonym in a locked form.
        index_url: 'https://pypi.org/simple'        # Package source index where the pseudonym is hosted.

The pseudonym is registered for the specified criteria. The unit derived out of
this declarative prescription will make sure the package yielded is known to
the resolver.

.. note::

  For a complete schema `check the schema.py file in adviser's
  implementation <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__.


Pseudonym ``run.log``
#####################

Print the given message to logs if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Pseudonym ``run.stack_info``
############################

See :ref:`boot's pipeline unit stack info <boot_stack_info>` which semantics is
shared with this unit.

Pseudonym ``match.package_version``
###################################

Package described in ``package_version`` field that should be matched by three
entries:

* ``name`` - mandatory, name of the package for which the pseudonym should be
  provided
* ``version`` - optional, version in a form of version specifier for which the
  pseudonym should be provided
* ``index_url`` - optional, Python package index URL for which the pseudonym
  should be provided; can be additionally negated using "not"
* ``develop`` - optional, if provided it additionally specifies if the dependency
  should or should not be a development dependency

It is also possibly to match the given pseudonym pipeline unit for multiple packages
by providing a match listing. In that case, multiple pipeline units with
different ``match`` configuration (but same ``run`` section) will be registered to
the resolution pipeline:

.. note::

  *Example:*

    .. code-block:: yaml

      name: PseudonymUnit
      type: pseudonym
      should_include:
        times: 1
        adviser_pipeline: true
      match:
      - package_version:
          name: tensorflow   # From any Python package index.
      - package_version:
          name: tensorflow-cpu
          index_url: "https://pypi.org/simple"
          develop: false     # Only if not development dependency.
      run:
        stack_info:
        - message: Considering also intel-tensorflow as an alternative to tensorflow and tensorflow-cpu
          type: INFO
          link: "https://pypi.org/project/intel-tensorflow"
        yield:
          yield_matched_version: true
          package_version:
            name: intel-tensorflow
            index_url: "https://pypi.org/simple"


Pseudonym ``run.yield``
#######################

Description of a package that should be yielded. Made out of two entries:

* ``yield_matched_version`` - yields version that was matched based on version
  specifier in the ``match`` section, defaults to ``false``
* ``package_version`` - description of a package that should be yielded

  * ``name`` - mandatory, name of the package that should be yielded
  * ``locked_version`` - optional, disjoint with ``yield_matched_version``;
    describes locked version of the package that should be yielded
  * ``index_url`` - optional, Python package index to be used to provide
    pseudonyms

If no version provided or no index explicitly set, all packages found in the
Thoth database are yielded (solved by Thoth's solver).

.. note::

  An example pipeline unit that suggests ``intel-tensorflow`` coming from PyPI
  as an alternative to ``tensorflow``:

  .. code-block:: yaml

    name: PseudonymUnit
    type: pseudonym
    should_include:
      times: 1
      adviser_pipeline: true
    match:
      package_version:
        name: tensorflow
        index_url: "https://pypi.org/simple"
    run:
      stack_info:
      - message: Considering also intel-tensorflow as an alternative to tensorflow
        type: INFO
        link: "https://pypi.org/project/intel-tensorflow"
      yield:
        yield_matched_version: true
        package_version:
          name: intel-tensorflow
          index_url: "https://pypi.org/simple"
