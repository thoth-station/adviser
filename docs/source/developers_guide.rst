Developer's guide to Thoth
--------------------------

The main goal of this document is to give a first touch on how to run, develop
and use Thoth as a developer.

A prerequisite for this document are the following documents:

* `General Thoth overview
  <https://github.com/thoth-station/thoth/blob/master/README.rst>`_

* `Basic usage of Pipenv <https://pipenv.readthedocs.io/en/latest/basics/>`_

* Basics of OpenShift - see for example `Basic Walkthrough
  <https://docs.openshift.com/container-platform/3.6/getting_started/developers_console.html>`_

Preparing Developer's Environment
=================================

You can clone repositories from `thoth-station organization
<https://github.com/thoth-station>`__ to your local directory.  It is preferred
to place repositories one next to anther as it will simplify import adjustments
stated later:

.. code-block:: console

  $ ls -A1 thoth-station/
  adviser
  amun-api
  amun-client
  amun-hwinfo
  analyzer
  ...
  user-api
  workload-operator
  zuul-test-config
  zuul-test-jobs

Using Pipenv and Thamos CLI
===========================

All of the Thoth packages use `Pipenv <https://pipenv.pypa.io/>`__ to
create a separated and reproducible environment in which the given component
can run. Almost every repository has its own ``Pipfile`` and ``Pipfile.lock``
file. The ``Pipfile`` file states direct dependencies for a project and
``Pipfile.lock`` file states all the dependencies (including the transitive
ones) pinned to a specific version.

If you have cloned the repositories, you can run the following command
to prepare a separate virtual environment with all the dependencies (including
the transitive ones):

.. code-block:: console

  $ thamos install --dev

  # Alternatively you can use Thamos CLI:
  $ thamos install --dev

As the environment is separated for each and every repository, you can now
switch between environments that can have different versions of packages
installed.

If you would like to install some additional libraries, just issue:

.. code-block:: console

  $ pipenv install <name-of-a-package>   # Add --dev if it is a devel dependency.

  # Alternatively, you can use Thamos CLI:
  $ thamos add <name-of-a-package>

The ``Pipfile`` and ``Pipfile.lock`` files get updated.

If you would like to run a CLI provided by a repository, issue the following
command:

.. code-block:: console

  # Run adviser CLI inside adviser/ repository:
  $ cd adviser/
  $ pipenv run python3 ./thoth-adviser --help

The command above automatically activates separated virtual environment created
for the `thoth-adviser <https://github.com/thoth-station/adviser>`__ and uses
packages from there.

To activate virtual environment permanently, issue:

.. code-block:: console

  $ pipenv shell
  (adviser)$

Your shell prompt will change (showing that you are inside a virtual
environment) and you can run for example Python interpret to run some of the
Python code provided:

.. code-block:: console

  (adviser)$ python3
  >>> from thoth.adviser import __version__
  >>> print(__version__)


Developing cross-library features
=================================

As Thoth is created by multiple libraries which depend on each other, it is
often desired to test some of the functionality provided by one library inside
another.

Suppose you would like to run `adviser
<https://github.com/thoth-station/adviser>`_ with a different version of
`thoth-python <https://github.com/thoth-station/python>`_ package (present in
the ``python/`` directory one level up from the adviser's directory). To do so,
the only thing you need to perform is to run the thoth-adviser CLI (in `adviser
<https://github.com/thoth-station/adviser>`_ repo) in the following way:


.. code-block:: console

  $ cd adviser/
  $ PYTHONPATH=../python pipenv run ./thoth-adviser provenance --requirements ./Pipfile --requirements-locked ./Pipfile.lock --files

The ``PYTHONPATH`` environment variable tells Python interpret to search for
sources first in the ``../python`` directory, this makes the following code:


.. code-block:: python

  from thoth.python import __version__

to first check sources present in ``../python`` and run code from there
(instead of running the installed ``thoth-python`` package from `PyPI
<https://pypi.org/>`__ inside virtual environment).

If you would like to run multiple libraries this way, you need to delimit them
using a colon:

.. code-block:: console

  $ cd adviser/
  $ PYTHONPATH=../python:../common pipenv run ./thoth-adviser --help

Debugging application and logging
=================================

All Thoth components use logging that is implemented in the `thoth-common
<https://thoth-station.ninja/docs/developers/common/>`__ package and is
initialized in ``init_logging()`` function (defined in ``thoth-common``
library). This library setups all the routines needed for logging (also sending
logs to external monitoring systems such as `Sentry <https://sentry.io>`_).

Besides the functionality stated above, the logging configuration can be
adjusted based on environment variables. If you are debugging some parts of the
Thoth application and you would like to get debug messages for a library, just
set environment variable ``THOTH_LOG_<library name>`` to ``DEBUG`` (or any
other `log level you would like to see
<https://docs.python.org/3/library/logging.html#logging-levels>`_, so
suppressing logs is also possible by setting log level to higher values like
``EXCEPTION`` or ``ERROR``). An example of a run can be:

.. code-block:: console

  $ cd adviser/
  $ THOTH_LOG_STORAGES=DEBUG THOTH_LOG_ADVISER=WARNING PYTHONPATH=../python pipenv run ./thoth-adviser provenance --requirements ./Pipfile --requirements-locked ./Pipfile.lock --files

The command above will suppress any debug and info messages in
``thoth-adviser`` (only warnings, errors and exceptions will be logged) and
increases verbosity of ``thoth-storages`` package to ``DEBUG``. Additionally,
you can setup logging only for a specific module inside a package by using for
example:

.. code-block:: console

  $ cd adviser/
  $ THOTH_LOG_STORAGES_GRAPH_POSTGRES=DEBUG THOTH_LOG_ADVISER=WARNING PYTHONPATH=../python pipenv run ./thoth-adviser provenance --requirements ./Pipfile --requirements-locked ./Pipfile.lock --files

By exporting ``THOTH_LOG_STORAGES_GRAPH_POSTGRES`` environment variable, you
set debug log level for file ``thoth/storages/graph/postgres.py`` provided by
``thoth-storages`` package. This way you can debug and inspect behavior only
for certain parts of the application. If a module has underscore in its name,
the environment variable has to have double underscores to explicitly escape it
(not to look for a logger defined in a sub-package).

The default log level is set to ``INFO`` to all Thoth components.

See `thoth-common library documentation
<https://thoth-station.ninja/docs/developers/common/>`_ for more info.

Testing application against Ceph and a knowledge graph database
===============================================================

If you would like to test changes in your application against data stored
inside Ceph, you can use the following command (if you have your ``gopass`` set
up):

.. code-block:: console

  $ eval $(gopass show aicoe/thoth/ceph.sh)

This will inject into your environment Ceph configuration needed for adapters
available in ``thoth-storages`` package and you can talk to Ceph instance.

In most cases you will need to set ``THOTH_DEPLOYMENT_NAME`` environment
variable which distinguishes different deployments.
we follow the pattern of ``(ClusterName)-(DeploymentName)`` to assign the
``THOTH_DEPLOYMENT_NAME`` environment variable. Ex: ``ocp4-stage``.
Names can be found in the corresponding Ceph bucket.

.. code-block:: console

  $ export THOTH_DEPLOYMENT_NAME=ocp4-stage

To browse data stored on Ceph, you can use ``awscli`` utility from `PyPI
<https://pypi.org/project/awscli/>`__ that provides ``aws`` command (use ``aws
s3`` as Ceph exposes S3 compatible API).

To run applications against Thoth's knowledge graph database, see
`documentation of thoth-storages library
<https://thoth-station.ninja/docs/developers/storages/>`_ which states how to
connect, run, dump or recreate Thoth's knowledge graph from a knowledge graph
backup.


Running application inside OpenShift vs local development
=========================================================

All the libraries are designed to run locally (for fast developer's experience
- iterating over features as fast as possible) as well as to run them inside a
cluster.

If a library uses OpenShift's API (such as all the operators), the
``OpenShift`` class implemented in ``thoth-common`` library takes care of
transparent discovery whether you run in the cluster or locally. If you would
like to run applications against OpenShift cluster from your local development
environment, use ``oc`` command to login into the cluster and change to project
where you would like to operate in:

.. code-block:: console

  $ oc login <openshift-cluster-url>
  ...
  $ oc project thoth-test-core

And run your applications (the configuration on how to talk to the cluster is
picked from OpenShift's/Kubernetes config). You should see a courtesy warning
by ``thoth-common`` that you are running your application locally.

To run an application from sources present in the local directory (for example
with changes you have made), you can open a pull request and issue ``/deploy``
command as a comment to the pull request opened.

If you would like to test application with unreleased packages inside OpenShift
cluster, you can do so by installing package from a Git repo and running the
``/deploy`` command on the opened pull request:

.. code-block:: console

  # To install thoth-common package from the master branch (you can adjust GitHub organization to point to your fork):
  $ pipenv install 'git+https://github.com/thoth-station/common.git@master#egg=thoth-common'

After that, you can open a pull request with adjusted dependencies. Note the
git dependencies **must not** be merged to the repository. Thoth will fail with
recommendations if it spots a VCS dependency in the application (it's a bad
practice to use such deps in prod-like deployments):

.. code-block:: console

  thamos.swagger_client.rest.ApiException: (400)
  Reason: BAD REQUEST
  HTTP response headers: HTTPHeaderDict({'Server': 'gunicorn/19.9.0', 'Date': 'Tue, 13 Aug 2019 06:28:21 GMT', 'Content-Type': 'application/json', 'Content-Length': '45257', 'Set-Cookie': 'ae5b4faaab1fe6375d62dbc3b1efaf0d=3db7db180ab06210797424ca9ff3b586; path=/; HttpOnly'})
  HTTP response body: {
    "error": "Invalid application stack supplied: Package thoth-storages uses a version control system instead of package index: {'git': 'https://github.com/thoth-station/storages' }",
  }

.. note::

  If you use an S2I build process with advises turned on, you can bypass the
  error by turning off recommendations, just set ``THOTH_ADVISE`` to ``0`` in
  the corresponding build config.

**Disclaimer:** Please, do **NOT** commit such changes into repositories. We
always rely on versioned packages with proper release management.

Scheduling workload in the cluster
==================================

You can use your computer to directly talk to cluster and schedule workload
there. An example case can be scheduling syncs of solver documents present on
Ceph. To do so, you can go to ``user-api`` repo and run Python3 interpreter
once your Python environment is set up:

.. code-block:: console

  $ # Go to a repo which has thoth-common and thoth-storages installed:
  $ cd thoth-station/user-api
  $ pipenv install --dev
  $ # Log in to cluster - your credentials will be used to schedule workload:
  $ oc login <cluster-url>
  $ # Make sure you adjust secrets before running Python interpreter in storages environment - you can obtain them from gopass:
  $ PYTHONPATH=. THOTH_MIDDLETIER_NAMESPACE=thoth-middletier-stage THOTH_INFRA_NAMESPACE=thoth-infra-stage KUBERNETES_VERIFY_TLS=0 THOTH_CEPH_SECRET_KEY="***" THOTH_CEPH_KEY_ID="***" THOTH_S3_ENDPOINT_URL=https://s3.url.redhat.com THOTH_CEPH_BUCKET_PREFIX=data THOTH_CEPH_BUCKET=thoth THOTH_DEPLOYMENT_NAME=ocp-stage pipenv run python3

After running the commands above, you should see Python interpreter's prompt,
run the following sequence of commands (you can use `help
<https://docs.python.org/3/library/functions.html#help>`_ built in to see more
information from function documentation):

.. code-block:: python

  >>> from thoth.storages import SolverResultsStore
  >>> solver_store = SolverResultsStore()
  >>> solver_store.connect()
  >>> from thoth.common import OpenShift
  >>> os = OpenShift()
  Failed to load in cluster configuration, fallback to a local development setup: Service host/port is not set.
  TLS verification when communicating with k8s/okd master is disabled
  >>> all_solver_document_ids = solver_store.get_document_listing()
  >>> [os.schedule_graph_sync_solver(solver_document_id, namespace="thoth-middletier-stage") for solver_document_id in all_solver_document_ids]

Once all the adapters get imported and instantiated, you can perform scheduling
of workload using the OpenShift abstraction, which will directly talk to
OpenShift to schedule workload in the cluster.
