Developer's guide to Thoth
--------------------------

The main goal of this document is to give a first touch on how to run, develop
and use Thoth as a developer.

A prerequisite for this document are the following documents:

* `General Thoth overview
  <https://github.com/thoth-station/thoth/blob/master/README.rst>`_

* `Basic usage of Pipenv <https://pipenv.readthedocs.io/en/latest/basics/>`_

* Basics of OpenShift - see for example `Basic Walkthrough
  <https://docs.openshift.com/online/getting_started/basic_walkthrough.html>`_

Preparing Developer's Environment
=================================

Use Ansible script `git-clone-repos.yaml` present in the `Core repository
<https://github.com/thoth-station/core/blob/master/git-clone-repos.yaml>`_ and
follow instructions present on the `following page
<https://url.corp.redhat.com/clone-thoth>`_.

Once you finish cloning the GitHub repositories, the directory structure in
your desired directory should state all the active repositories under the
`Thoth-Station organization on GitHub <https://github.com/thoth-station>`_:

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

These all are the repositories cloned to the most recent master branch (see
also `git-update-repos.yaml
<https://github.com/thoth-station/core/blob/master/git-update-repos.yaml>`_
Ansible script to update repositories after some time).

Using Pipenv
============

All of the Thoth packages use `Pipenv <https://pipenv.kennethreitz.org/>`_ to
create a separated and reproducible environment in which the given component
can run. Almost every repository has its own ``Pipfile`` and ``Pipfile.lock``
file. The ``Pipfile`` file states direct dependencies for a project and
``Pipfile.lock`` file states all the dependencies (including the transitive
ones) pinned to a specific version.

If you have cloned the repositories via the provided Ansible script, the
Ansible scripts prepares the environment for you. It runs the following command
to prepare a separate virtual environment with all the dependencies (including
the transitive ones):

.. code-block:: console

  $ pipenv install --dev

As the environment is separated for each and every repository, you can now
switch between environments that can have different versions of packages
installed.

If you would like to install some additional libraries, just issue:

.. code-block:: console

  $ pipenv install <name-of-a-package>   # Add --dev if it is a devel dependency.

The ``Pipfile`` and ``Pipfile.lock`` file get updated.

If you would like to run a CLI provided by a repository, issue the following
command:

.. code-block:: console

  # Run adviser CLI inside adviser/ repository:
  $ cd adviser/
  $ pipenv run python3 ./thoth-adviser --help

The command above automatically activates separated virtual environment created
for the `thoth-adviser <https://github.com/thoth-station/adviser>`_ and uses
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
<https://pypi.org/>`_ inside virtual environment).

If you would like to run multiple libraries this way, you need to delimit them
using a colon:

.. code-block:: console

  $ cd adviser/
  $ PYTHONPATH=../python:../common pipenv run ./thoth-adviser --help

Debugging application and logging
=================================

All Thoth components use logging that is implemented in the ``thoth-common``
package and is initialized in ``init_logging()`` function (defined in
``thoth-common`` library). This library setups all the routines needed for
logging (also sending logs to external monitoring systems such as `Sentry
<https://sentry.io>`_).

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
  $ THOTH_LOG_STORAGES_GRAPH_DGRAPH=DEBUG THOTH_LOG_ADVISER=WARNING PYTHONPATH=../python pipenv run ./thoth-adviser provenance --requirements ./Pipfile --requirements-locked ./Pipfile.lock --files

By exporting ``THOTH_LOG_STORAGES_GRAPH_DGRAPH`` environment variable, you set
debug log level for file ``thoth/storages/graph/postgres.py`` provided by
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
``THOTH_DEPLOYMENT_NAME`` environment variable. Ex: ocp-stage
Some of the older deployments were `thoth-test-core`, `thoth-core-upshift-stage`,
 and etc. These can be found in ceph bucket.

 __Disclaimer__: Older deployments would be deprecated and removed. Please check
 the existence of the deployment in ceph before using.

.. code-block:: console

  $ export THOTH_DEPLOYMENT_NAME=ocp-stage

To browse data stored on Ceph, you can use ``awscli`` utility from `PyPI
<https://pypi.org/project/awscli/>`_ that provides ``aws`` command (use ``aws
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
with changes you have made), you can use the following command to upload
sources to OpenShift and start a build:

.. code-block:: console

  $ cd adviser/
  $ oc start-build adviser --from-dir=. -n <namespace>

You will see (for example in the OpenShift console) that the build was
triggered from sources.

To see available builds (that match component name), issue the following once
you are logged in and present in the right project:

.. code-block:: console

  $ oc get builds

If you would like to test application with unreleased packages inside OpenShift
cluster, you can do so by installing package from a Git repo and running the
``oc build`` command above:

.. code-block:: console

  # To install thoth-common package from the master branch (you can adjust GitHub organization to point to your fork):
  $ pipenv install 'git+https://github.com/thoth-station/common.git@master#egg=thoth-common'

After that, you can start build using ``oc start-build <build-name>
--from-dir=. -n <namespace>``. Note however that most of the Thoth's
buildconfigs use Thoth to recommend application stacks. As you are using a Git
version, this recommendation will fail with an error similar to this one:

.. code-block:: console

  thamos.swagger_client.rest.ApiException: (400)
  Reason: BAD REQUEST
  HTTP response headers: HTTPHeaderDict({'Server': 'gunicorn/19.9.0', 'Date': 'Tue, 13 Aug 2019 06:28:21 GMT', 'Content-Type': 'application/json', 'Content-Length': '45257', 'Set-Cookie': 'ae5b4faaab1fe6375d62dbc3b1efaf0d=3db7db180ab06210797424ca9ff3b586; path=/; HttpOnly'})
  HTTP response body: {
    "error": "Invalid application stack supplied: Package thoth-storages uses a version control system instead of package index: {'git': 'https://github.com/thoth-station/storages' }",
  }

To bypass this error you need to temporary turn off these recommendations by
setting ``THOTH_ADVISE`` to ``0`` in the corresponding buildconfig:

.. code-block:: console

  oc edit bc <build-name> -n <namespace>

Please set the environment variable ``THOTH_ADVISE`` back to ``1`` after you
test your changes.

Also not that files ``Pipfile`` and ``Pipfile.lock`` get updated. Please, do
NOT commit such changes into repositories (we always rely on versioned
packages).

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
<https://docs.python.org/3/library/functions.html#help>` built in to see more
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
OpenShift's master to schedule workload in the cluster.
