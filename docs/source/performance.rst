.. _performance:

Performance indicators
----------------------

In the upcoming sections, you can find information on how to write performance
indicators, how to incorporate them into Thoth and how to inject them into
Thoth's recommendation pipeline.

You can also dive into an article published on this topic: `Microbenchmarks for
AI applications using Red Hat OpenShift on PSI in project Thoth
<https://developers.redhat.com/blog/2019/10/28/microbenchmarks-for-ai-applications-using-red-hat-openshift-on-psi-in-project-thoth/>`_.

Writing a performance script
============================

Performance related characteristics are automatically gathered on Thoth's
execution part - `Amun <https://github.com/thoth-station/amun-api>`__ which can
be triggered directly or using :ref:`dependency_monkey`. Amun accepts
``specification`` which is turned into a build and subsequent job which verifies
the given software stack in the given runtime environment as described in the
specification.

The performance script which is supplied to Amun should be directly executable
(e.g. ``python3 script.py``), it can print additional information onto
``stderr`` in any form (this output is captured by Amun for additional
analysis). The output written onto ``stdout`` *has to be* in a JSON format with
any keys and values the script wants to capture and required ``@parameters``
and ``@result`` keys (see bellow). Optional ``overall_score`` key states
"overall score" of the performance indicator.

The script *has to report* following keys to stdout in the resulting JSON:

* ``@parameters`` (type ``dict``) - parameters which define the given performance script (e.g. matrix size in case of matrix multiplication)
* ``@result`` (type ``dict``) - the actual result which was obtained during the performance indicator run
* ``name`` (type ``str``) - the name of performance indicator, this name has to match graph database model in thoth-storages (see bellow)
* ``framework`` (type ``str``) - name of the tested framework (e.g. ``tensorflow``, ``pytorch``, ...) all in lowercase (should conform to the package name)
* ``tensorflow_buildinfo`` (type ``dict``) - in case of TensorFlow performance indicator, the value under this key holds automatically gathered build information of the tested TensorFlow wheel file (available in `AICoE optimized builds <http://tensorflow.pypi.thoth-station.ninja>`_).
* ``overall_score`` (type ``float``) - the overall score which was computed by the performance indicator

The keys in the nested dictionaries of ``@parameters`` and ``@result`` have to
be unique (no same key in ``@result`` dictionary and ``@parameters``
dictionary) as they are serialized into a single graph database model
automatically.

Example:

.. code-block:: json

  {
    "name": "PiMatmul",
    "framework": "tensorflow",
    "tensorflow_aicoe_buildinfo": null,
    "tensorflow_upstream_buildinfo": null,
    "@parameters": {
      "dtype": "float32",
      "device": "cpu",
      "reps": 20000,
      "matrix_size": 512
    },
    "@result": {
      "rate": 0.009799366109955314,
      "elapsed": 27366.39380455017
    },
    "overall_score": 0.3
 }

Once you have created a performance script, add it to `performance
<https://github.com/thoth-station/performance>`__ repo and open a pull request.
Wait for a review by one of the code owners. Meanwhile, you can create a pull
request which creates related graph database model to have performance related
information available in Thoth's knowledge base - see section bellow.

Creating a performance indicator model
======================================

All the models are present in the `thoth-storages
<https://github.com/thoth-station/storages>`_ repository (see ``graph``
submodule). All the performance indicators have to derive from
``PerformanceIndicatorBase`` which already specifies some of the needed
properties that are automatically gathered on syncs to the graph database (such
as CPU time spent in kernel space, user space, number of context switches and
additional metadata).

An example of a model which captures results of the previous example would look
like:

.. code-block:: python

  from .models_base import model_property

  class PiModel(PerformanceIndicatorBase):

    dtype = model_property(type=str, index="exact")
    device = model_property(type=str, index="exact")
    reps = model_property(type=int, index="int")
    matrix_size = model_property(type=int, index="int")


Once the model is created and inserted into thoth-storages sources, register it
by adding it to ``ALL_PERFORMANCE_MODELS`` listing (see thoth-storages
sources). After that, run the script which will create RDF schema required to
adjust graph database schema:

.. code-block:: console

  # Inside thoth-storages repo:
  pipenv install --dev
  PYTHONPATH=. pipenv run python3 ./create_schema.py --output thoth/storages/graph/schema.rdf

After this step, commit related changes to Thoth's `storages repo
<https://github.com/thoth-station/storages>`_ - please open a pull request with
a link to the related performance indicator script created following the steps
above and wait for a review by one of the code owners.

You can also provide implementation on how to query results of the
performance indicator runs in the ``GraphDatabase`` adapter to have results of
performance indicators available in adviser's :ref:`pipeline`. Subsequently you
can provide implementation of step or stride in adviser's pipeline to respect
gathered performance related observations - see :ref:`pipeline` for more
information on how to do that.

Registering and running performance indicator in a deployment
=============================================================

After your performance indicator pull requests have been merged (in
`thoth-station/storages <https://github.com/thoth-station/storages>`_ repo and
`thoth-station/performance <https://github.com/thoth-station/performance>`__
repo), one of the Thoth's maintainers have to issue a new release of
`thoth-storages <https://pypi.org/project/thoth-storages/>`__ library which
carries the newly created model for your performance indicator. This release is
triggered by opening an issue on the repository by one of the Thoth's
maintainers. The release is performed automatically and all the components
which use this package as a dependency get automatic updates. Once these
updates are automatically merged to the ``master`` branch there is
automatically triggered a build in the Thoth's test environment, where you can
test it in a "pre-stage phase". To propagate built components into stage and
prod deployment, a proper release management has to be done.

Once all the relevant components are updated in the desired deployment, an
administrator of Thoth has to issue graph database schema update by triggering
related endpoint on `Management API
<https://github.com/thoth-station/management-api>`_. Once graph database schema
is updated, the performance indicator is registered to Thoth and is ready to be
executed.

You can use :ref:`dependency_monkey` or directly `Amun
<https://github.com/thoth-station/amun-api>`__ service to trigger the desired
performance indicator.

Summary
=======

#. Create a performance indicator in `thoth-station/performance repo <https://github.com/thoth-station/performance>`_.
#. Create a relevant graph model in `thoth-station/storages <https://github.com/thoth-station/storages>`_ and register it to ``ALL_PERFORMANCE_MODELS``.
#. Create a relevant query to graph database if you would like to query for results in adviser pipelines.
#. Issue a new release of ``thoth-storages`` Python package and let it be populated to the relevant Thoth components (the most important ones are `Management API <https://github.com/thoth-station/management-api>`_, `graph-sync-job <https://github.com/thoth-station/graph-sync-job>`_ and `adviser <https://github.com/thoth-station/adviser>`_).
#. Test your changes in test environment, let the change be populated to other Thoth deployments respecting Thoth's release management process.
#. Benefit from recommendations which include the gathered performance related characteristics obtained by running newly created performance indicator.
