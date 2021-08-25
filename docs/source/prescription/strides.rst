.. _prescription_strides:

Stride prescription pipeline unit
---------------------------------

Declaring :ref:`pipeline units of type stride <strides>`.

.. note::

  The pipeline unit is registered based on ``should_include``
  directive - :ref:`see documentation for more info <prescription_should_include>`.

The following example shows all the configuration options that can be supplied
to a stride pipeline unit type. See respective sections described below for more
info.

.. code-block:: yaml

  name: StrideUnit
  type: stride
  should_include:
    # See should_include section for more info.
  match:                                            # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_version is provided.
    state:                                          # Optional, resolver internal state to match for the given stride.
      resolved_dependencies:
      - name: werkzeug                            # Dependencies that have to be present in the resolved state.
        version: "~=1.0.0"                        # Version specifier specifying version range.
        index_url: 'https://pypi.org/simple'      # Index URL used when consuming the release. Can be negated using "not".
  run:
    log:                                            # Optional text printed to logs when the unit gets called.
      message: Some text printed to log on pipeline unit run
      type: WARNING
    stack_info:                                     # Information printed to the recommended stack report.
    - type: WARNING
      message: Hello, world
      link: https://thoth-station.ninja             # A link to justifications or a link to a web page.
    not_acceptable: Bad package inclusion           # Block resolving the given stack.
    # Configuration of prematurely terminating the resolution process.
    eager_stop_pipeline: "Stop pipeline"

.. note::

  For a complete schema `check the schema.py file in adviser's
  implementation <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__.

.. _stride_match:

Stride ``match``
####################

A state that needs to be met to trigger the given stride pipeline unit. The state
states resolved dependencies where each entry in the resolved dependency
listing is described as:

* ``name`` - optional package name that has to be stated in the resolved
  dependency listing
* ``version`` - optional package version in a form of version specifier that
  has to be stated in the resolved dependency listing
* ``index_url`` - optional package index from which the given package is
  consumed, can be negated using "``not``"
* ``develop`` - optional, if provided it additionally specifies if the
  dependency should or should not be a development dependency

To run the given stride, all the packages in the resolved dependency listing
need to be present in the resolved software stack.

It is possible to provide a listing of matching criteria to run the given
pipeline unit multiple times - the run part will be reused for each ``match``
entry stated.

Stride ``run.log``
##################

Print the given message to the resolution log if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Stride ``run.stack_info``
#########################

See :ref:`boot's stack info <boot_stack_info>` which semantics is shared with this unit.

Stride ``run.not_acceptable``
#############################

If the given pipeline unit is registered and matched, it will discard the
resolved stack matched from the resolver's results reported.

Stride ``run.eager_stop_pipeline``
##################################

If the given pipeline unit is registered and matched, it will cause the whole
resolution process to halt and report back results computed, if any. If no results
are available, the resolution process will fail as no software stack is produced.
