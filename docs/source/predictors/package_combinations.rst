.. _package_combinations:

Package Combinations Predictor
------------------------------

.. note::

  Check :ref:`high level predictor docs <predictor>` for predictor basics.

Yet another predictor was designed for :ref:`Dependency Monkey
<dependency_monkey>` runs and is suitable for generating combinations of
certain packages in a software stack. An example use case can be a TensorFlow
stack with all the packages locked to a specific version except for NumPy which
should be tested in different versions. This predictor can also work when
multiple combinations should be consider - e.g.  `NumPy
<https://pypi.org/project/numpy>`__ with all the possible `absl-py
<https://pypi.org/project/absl-py>`__ packages.

When computing combinations of certain package or packages it is often a good
practice to pin versions of all the other packages to specific versions. This
can be accomplished on the requirements level (Pipfile) but this is in general
considered as a bad practice for this use case. Having dependencies locked on
pipeline unit level allows locking of a package only if it is about to be
resolved. On the other hand, locking packages on requirements level creates
request for the resolver to have the given requirement always present in the
stack. This can have negative impact on the tested software as the tested part
is not minimal and the required dependency can affect how dependency graph
looks like with respect to other dependencies as well.

See Amun inspection present in `thoth-station/dependency-monkey-zoo repository
<https://github.com/thoth-station/dependency-monkey-zoo/tree/master/tensorflow/inspection-2020-09-08.1>`__
which holds all the files required for scheduling and checking configuration
used for the :ref:`Dependency Monkey <dependency_monkey>` run using the package
combinations predictor.  This configuration was used to create all the version
combinations of ``six`` and ``urllib3`` that can occur in a
``tensorflow==2.1.0`` stack (to date the inspection was created). Most notable
parts are:

1. Pipfile holds just ``tensorflow==2.1.0`` as a requirement for the resolver.

2. The pipeline configuration present in the ``pipeline.conf`` pins packages to
   specific version on pipeline unit level in opposite to locking on the
   requirements level:

   .. code-block:: yaml

     steps:
     # Pin numpy to one version that can occur across all the stacks resolved:
     - configuration:
        only_once: false
        package_name: numpy
       name: OneVersionStride

3. Parameters passed to the predictor specify which package combinations should
   be considered during the resolution (thus predictor guides the resolution
   process to resolve these combinations):

  .. code-block:: yaml

    package_combinations:
    - six
    - urllib3

As can be seen, using the pipeline configuration and the predictor in a
specific way can lead to desired results - both can cooperate together.

The video below demonstrates the whole process in action:

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/S3hFn8KRsKc" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

The results presented in the video can be seen summarized `in this following
blog <https://developers.redhat.com/blog/2020/09/30/ai-software-stack-inspection-with-thoth-and-tensorflow/?sc_cid=7013a000002gbzfAAA>`__.
