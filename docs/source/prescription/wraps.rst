.. _prescription_wraps:

Wrap prescription pipeline unit
-------------------------------

Declaring :ref:`pipeline units of type wrap <wraps>`.

.. note::

  The pipeline unit is registered based on ``should_include``
  directive - :ref:`see documentation for more info <prescription_should_include>`.

The following example shows all the configuration options that can be supplied
to a wrap pipeline unit type. See respective sections described below for more
info.

.. code-block:: yaml

  name: WrapUnit
  type: wrap
  should_include:
    # See should_include section for more info.
  match:                                            # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_version is provided.
    state:                                          # Optional, resolver internal state to match for the given stride.
      resolved_dependencies:
      - name: werkzeug                              # Dependencies that have to be present in the resolved state.
        version: ">=1.0.0,<2.5.0"                   # Version specifier for matching version ranges.
        index_url: 'https://pypi.org/simple'        # Index URL used for consuming the package. Can be negated using "not".
  run:
    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"
    stack_info:                                     # Information printed to the recommended stack report.
    - type: WARNING
      message: "Hello, world"
      link: https://thoth-station.ninja             # A link to justifications or a link to a web page.
    justification:
      - type: INFO
        message: "Hello, Thoth!"
        link: https://thoth-station.ninja
    advised_manifest_changes:
      - apiVersion: "apps.openshift.io/v1"
        kind: DeploymentConfig
        patch:
          op: add
          path: "/spec/template/spec/containers/0/env/0"
          value:
            name: "WORKDIR"
            value: "/home/workdir"

.. note::

  For a complete schema `check the schema.py file in adviser's
  implementation <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__.

Wrap ``match``
##################

See :ref:`stride's match <stride_match>` that has shared semantics.

.. note::

  *Example:*

  .. code-block:: yaml

    name: WrapUnit
    type: wrap
    should_include:
      adviser_pipeline: true
      recommendation_types:
      # Only warn here, in case of performance the corresponding resolution step can be penalized.
      - latest
      - testing
      library_usage:
        tensorflow:
        - tensorflow.keras.layers.Embedding
    match:
    # Matching multiple criteria.
    - state:
        resolved_dependencies:
        - name: tensorflow
          version: "<=2.4.0"
    - state:
        resolved_dependencies:
        - name: tensorflow-cpu
          version: "<=2.4.0"
    - state:
        resolved_dependencies:
        - name: tensorflow-gpu
          version: "<=2.4.0"
    run:
      stack_info:
      - type: WARNING
        message: "TensorFlow in version <=2.4 is slow when tf.keras.layers.Embedding is used"
        # Can be replaced with just "tf_42475".
        link: "https://thoth-station.ninja/j/tf_42475.html"

Wrap ``run.log``
################

Print the given message to the resolution log if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Wrap ``run.stack_info``
#######################

See :ref:`stack info <boot_stack_info>` which semantics is shared with this unit.

Note stack info is added only once even if the pipeline unit is
run multiple times during the resolution process.

Wrap ``run.justification``
##########################

A justification added if the given wrap is matched and run. This justification
is similar to the one :ref:`as provided by step <step_run_justification>`. It
is added to the resolved stack if the match criteria are met.

Wrap ``run.advised_manifest_changes``
#####################################

Suggested changes to the manifest files used for application deployment.

.. note::

  *Example:*

  A pipeline unit that adjusts environment variables if ``intel-tensorflow`` is resolved.

  .. code-block:: yaml

    name: WrapUnit
    type: wrap
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: intel-tensorflow
    run:
      advised_manifest_changes:
      - apiVersion: apps.openshift.io/v1
        kind: DeploymentConfig
        patch:
          op: add
          path: /spec/template/spec/containers/0/env/0
          value:
            name: OMP_NUM_THREADS
            value": "1"
      stack_info:
      - type: INFO
        message: Adjst OMP_NUM_THREADS environment variable to make sure application behaves correctly in containerized environments
        link: 'https://www.openmp.org/spec-html/5.0/openmpse50.html'


See :ref:`manifest_changes` section for more info and semantics.

GitHub release notes prescription pipeline unit
-----------------------------------------------

A specific type of wrap pipeline unit that adds links to GitHub release page.
See `the linked demo for more info
<https://www.youtube.com/watch?v=oK1qYdhmquY>`__.

.. note::

  *Example:*

  .. code-block:: yaml

    units:
      wraps:
      - name: FlaskGitHubReleaseNotesWrap
        type: wrap.GHReleaseNotes  # Mind the type.
        should_include:
          adviser_pipeline: true
          # See should_include section for more options.
        match:
          state:
            resolved_dependencies:
            - name: flask
              version: '>=0.0.0'
              index_url: 'https://pypi.org/simple'
        run:
          release_notes:
            organization: pallets
            repository: flask
            # tag_version_prefix: v


The example above will link to GitHub release info if the listed package is in
the resolved stack.

See :ref:`stride's match <stride_match>` that has shared semantics for matching
resolved dependencies.

The ``run.release_notes`` part states organization and repository on GitHub
that is used as an information to construct URL to the release notes hosted on
GitHub. If the project uses a prefix (such as ``v``) in the release tag,
``tag_version_prefix`` directive can be specified.

An example link generated for
`flask in version 1.1.0 <https://github.com/pallets/flask/releases/tag/1.1.0>`__.
