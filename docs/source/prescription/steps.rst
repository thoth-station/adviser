.. _prescription_steps:

Step prescription pipeline unit
-------------------------------

Declaring :ref:`pipeline units of type step <steps>`.

.. note::

  The pipeline unit is registered based on ``should_include``
  directive - :ref:`see documentation for more info <prescription_should_include>`.

The following example shows all the configuration options that can be applied
for a step pipeline unit type. See respective sections described below for more
info. Also note, the example shows all the options that can be supplied and is
not semantically valid (not all options can be supplied at the same time):

.. code-block:: yaml

  name: StepUnit
  type: step
  should_include:
    # See should_include section for more info.
  match:                                            # Criteria to trigger run of this pipeline unit.
    package_version:                                # Matching criteria for a package that is about to be included to the resolver's state.
      name: flask                                   # Optional name of the package for which the unit should be registered. If name is not provided, the unit is run for any package matching also other directives.
      version: '>1.0,<=1.1.0'                       # Version specifier for which the unit should be run. If not provided, defaults to any version.
      index_url: 'https://pypi.org/simple'          # Package source index for which the unit should be run. If not provided, defaults to any index. Can be negated using "not".
      develop: false                                # If specified, match development or not development dependencies.
    state:                                          # Optional, resolver internal state to match for the given resolution step.
      resolved_dependencies:
      - name: werkzeug                              # Dependencies that have to be present in the resolved state. The semantics for each entry is same as for package_version directive.
        version: '==1.0.0'
        index_url: 'https://pypi.org/simple'
        develop: false
  run:
    score: 0.42                                     # Optional score assigned to the step performed in the resolution.
    justification:
    - type: INFO
      message: Hello, Thoth!
      link: 'https://thoth-station.ninja'

    not_acceptable: Bad package inclusion           # Block including certain package during the resolution.

    # Configuration of prematurely terminating the resolution process.
    eager_stop_pipeline: Stop pipeline

    multi_package_resolution: false                 # Run this pipeline multiple times when matched mutliple times. Defaults to false if not provided.

    log:                                            # Optional text printed to logs when the unit gets called.
      message: Some text printed to log on pipeline unit run
      type: WARNING

    stack_info:                                     # Information printed to the recommended stack report.
    - type: WARNING
      message: Hello, world!
      link: 'https://thoth-station.ninja'           # A link to justifications or a link to a web page.

.. note::

  For a complete schema `check the schema.py file in adviser's
  implementation <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__.

.. _step_match:
Step ``match``
##############

Match the given step performed in the resolution process. A step is described
by state stating required resolved dependencies so far and package that is
about to be resolved (added to the resolved dependencies listing):

* ``package_version`` - package that is about to be resolved by adding it to
  the resolver's state

  * ``name`` - optional, name of the package
  * ``version`` - optional, version in a form of version specifier
  * ``index_url`` - optional, Python package index URL, can be negated using
    ``not``
  * ``develop`` - optional, if provided it additionally specifies if the
    dependency should or should not be a development dependency


* ``state`` - internal resolver's state with resolved dependencies

A state that needs to be met to trigger the given step pipeline. The state
can state:

* ``resolved_dependencies`` - optional listing of resolved dependencies:

  * ``name`` - optional package name that has to be stated in the resolved
    dependency listing
  * ``version`` - optional package version in a form of version specifier that
    has to be stated in the resolved dependency listing
  * ``index_url`` - optional package index from which the given package is
    consumed, can be negated using ``not``
  * ``develop`` - optional boolean stating whether the package is or is not in
    the development dependency listing

* ``package_version_from`` where each entry describes packages that introduced
  the matched package. Each entry can state directives as in
  ``package_version``. If multiple entries are stated, each entry has to
  introduce matched ``package_version`` as a dependency.

To run the given step, all the packages in the resolved dependency listing need
to be present in the resolved software stack. Also both ``state`` and
``package_version`` need to be matched.

It is possible to provide a listing of matching criteria to run the given
pipeline unit multiple times - the run part will be reused for each ``match``
entry stated.

.. note::

  *Example:*

  .. code-block:: yaml

    # Match when torch (not dev) in a 1.9.0 compatible release from PyPI is
    # about to be included into resolver's state with torchvision==0.9.0 from PyPI.
    match:
      package_version:
        name: torch
        version: "~=1.9.0"
        index_url: "https://pypi.org/simple"
        develop: false
      state:
        resolved_dependencies:
        - name: torchvision
          version: "==0.9.0"
          index_url: "https://pypi.org/simple"

  .. code-block:: yaml

    # Match when torch in a 1.9.0 compatible release *not* from PyPI is about to
    # be included into resolver's state with torchvision==0.9.0 *not* from PyPI.
    match:
      package_version:
        name: torch
        version: "~=1.9.0"
        index_url:
          not: "https://pypi.org/simple"
      state:
        resolved_dependencies:
        - name: torchvision
          version: "==0.9.0"
          index_url:
            not: "https://pypi.org/simple"

  .. code-block:: yaml

    match:
    # Match when resolving tensorflow as a dependency of seldon and
    # flask is already in the resolved dependency listing:
    - package_version:
        name: tensorflow
      state:
      - resolved_dependencies:
          name: flask
        package_version_from:
          name: seldon
    # Or match when resolving tensorflow as a dependency of seldon and
    # connexion is already in the resolved dependency listing:
    - package_version:
        name: tensorflow
      state:
      - resolved_dependencies:
          name: connexion
        package_version_from:
          name: seldon

Step ``run.log``
################

Print the given message to the resolution log if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Step ``run.stack_info``
#######################

See :ref:`stack info <boot_stack_info>` which semantics is shared with this unit.

Note the stack info is added only once even if the pipeline unit is
run multiple times during the resolution process.

Step ``run.multi_package_resolution``
#####################################

A boolean stating whether the given unit should be run if criteria match multiple
times per resolution run. Defaults to false.

See :ref:`multi package resolution flag in steps <multi_package_resolution>`.

.. _step_run_justification:
Step ``run.justification``
##########################

Optional justification added to the resolved stack when the pipeline unit is
run. This justification is added only if no ``not_acceptable`` and no
``eager_stop_pipeline`` are supplied - if the given step is a valid step in the
resolution process. See :ref:`justification` for more info on how to write
justifications and their semantics.

Each entry in the list is specified by three attributes:

* ``type`` - any of ``INFO``, ``WARNING``, and ``ERROR`` specifying severity of
  the produced justification
* ``message`` - a message in a free text form printed to users
* ``link`` - a link to a document describing more information in detail

The link can be in a form of a valid HTTP or HTTPS URL or a string which
:ref:`references justifications <jl>` available at
`thoth-station.ninja/justifications
<https://thoth-station.ninja/justifications>`__.

.. note::

  *Example:*

  .. code-block:: yaml

    name: StepUnit
    type: step
    should_include:
      times: 1
      adviser_pipeline: true
    match:
      package_version:
        index_url: 'https://thoth-station.ninja/simple'
    run:
      score: +0.1
      justification:
      - type: INFO
        message: Builds available on index thoth-station.ninja/simple take precedence
        link: 'https://thoth-station.ninja/'

Step ``run.score``
##################

Optional score to penalize or prioritize resolving the given stack.
Score has to be from interval -1.0 to +1.0 inclusively. This score corresponds
to :ref:`the reward signal <introduction>`.

Step ``run.not_acceptable``
###########################

Make the given step not acceptable in the resolution process. This option is
suitable to avoiding resolution of certain combination of packages - resolver
will try to find another resolution path to satisfy requirements.

.. note::

  *Example:*

  A pipeline unit that filters out any ``tensorflow~=2.4.0`` when
  ``numpy==1.19.1`` is in already resolved dependencies.

  .. code-block:: yaml

    name: StepUnit
    type: step
    should_include:
      adviser_pipeline: true
    match:
      package_version:
        name: numpy
        version: "==1.19.1"
        index_url: 'https://pypi.org/simple'
      state:
        resolved_dependencies:
        - name: tensorflow
          version: '~=2.4.0'
    run:
      multi_package_resolution: true
      not_acceptable: "NumPy==1.19.5 is causing issues when used with TensorFlow 2.4"
      stack_info:
      - type: WARNING
        message: "NumPy==1.19.5 is causing issues when used with TensorFlow 2.4"
        link: "https://thoth-station.ninja/j/tf_24_np.html"

Step ``run.eager_stop_pipeline``
################################

If the given pipeline unit is registered and matched, it will cause the whole
resolution process to halt and report back results computed, if any. If no results
are available, the resolution process will fail as no software stack is produced.

.. _skip_package_step:
SkipPackage step prescription pipeline unit
--------------------------------------------

This pipeline unit skips including the given package in the resolved stack
considering also state of the resolver. If the state is not relevant for
skipping the matched package, use :ref:`SkipPackage sieve <skip_package_sieve>`
instead.

Running this pipeline unit will make sure that the matched ``package_version``
and all its dependencies will be removed from the dependency graph. In other
words, sub-graph introduced by the matched ``package_version`` will be
completely removed.

The pipeline unit considers what packages introduced the package that is
supposed to be removed and optionally other packages that are already present
in the resolved dependencies listing. Use this unit if you wish to exclude
accidentally included dependencies.

.. note::

  *Example:*

  A pipeline unit that removes SciPy package from the stack if SciPy was introduced
  by the given TensorFlow version.

  .. code-block:: yaml

    name: SkipPackageStepUnit
    type: step.SkipPackage
    should_include:
      adviser_pipeline: true
    match:
      package_version:
        name: scipy
      state:
        package_version_from:
        - name: tensorflow
          version: '>=2.1,<=2.3'
          index_url: https://pypi.org/simple
          develop: false
    run:
      stack_info:
      - type: WARNING
        message: TensorFlow in versions >=2.1<=2.3 stated SciPy as a dependency but it is not used in the codebase
        link: 'https://github.com/tensorflow/tensorflow/issues/35709'

The described pipeline unit shares most of the directives with the step prescription pipeline unit.
However, it does not allow declaring:

* ``run.not_acceptable``
* ``run.score``
* ``run.justification``
* ``run.eager_stop_pipeline``


AddPackage step prescription pipeline unit
------------------------------------------

This pipeline unit allows adding packages to the dependency graph even though they were not stated in requirements.
The unit is suitable for fixing underpinning issues.

.. note::

  *Example:*

  A pipeline unit that adds pandas package to the stack if SciPy was introduced
  by the given TensorFlow version and Matplotlib is already resolved.

  .. code-block:: yaml

    name: AddPackageStepUnit
    type: step.AddPackage
    should_include:
      adviser_pipeline: true
      # See should_include section for more options.
    match:
      package_version:
        name: scipy
        version: '~1.7.1'
        index_url: 'https://pypi.org/simple'
      state:
        package_version_from:
        - name: tensorflow
          version: '>=2.1,<=2.3'
          index_url: https://pypi.org/simple
          develop: false
        resolved_dependencies:
        - name: matplotlib
    run:
      stack_info:
      - type: INFO
        message: Injecting Pandas to the dependency graph
        link: 'https://thoth-station.ninja'
      log:
        type: INFO
        message: Injecting Pandas to the dependency graph
      package_version:
        name: pandas
        locked_version: ==1.3.2
        index_url: 'https://pypi.org/simple'
        develop: false

AddPackageStep ``match``
########################

See :ref:`Step match <step_match>` that has shared semantics.

Step ``run.stack_info``
#######################

See :ref:`boot's stack info <boot_stack_info>` which semantics is shared with this unit.

Note the stack info is added only once even if the pipeline unit is
run multiple times during the resolution process.

Step ``run.log``
################

Print the given message to the resolution log if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Step ``run.package_version``
############################

Specification of a package that should be added to the dependency graph. All the fields are mandatory:

* ``name`` - name of the package
* ``locked_version`` - locked package version (must start with ``==``)
* ``index_url`` - Python package index URL from where the package is supposed to be installed
* ``develop`` - add the given package to default or development dependencies of the project

Note the given package in the specified version has to be already analyzed by
the system so that resolver can inject this dependency and possibly all its
dependencies into the dependency graph. The Python package index has to be also
know and enabled on the deployment side. If these conditions are not met, the
pipeline unit will not register the requested package to the dependency graph.
