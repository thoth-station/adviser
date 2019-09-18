Thoth Adviser
-------------

A recommendation engine for project `Thoth <https://github.com/thoth-station/>`_.

There are the following main goals of thoth-adviser (as of now):

1. Provide a tool that can compute recommendations in project `Thoth <https://thoth-station.ninja>`_.
2. Check provenance of installed packages (which package source indexes are used - this is not guaranteed by pip nor Pipenv).
3. A tool called "Dependency Monkey" that generates all the possible software stacks for a project respecting dependency resolution.

To interact with a deployed Thoth, you can use the
`Thamos CLI <https://github.com/thoth-station/thamos>`_.


Dependency Monkey
=================

Dependency Monkey is a functionality that allows you to generate all the
possible software stacks for your project. Given the input (direct dependencies
of your project), Dependency Monkey creates N-ary dependency graph (as
described above) stating all the dependencies of your direct
dependencies/libraries as well as dependencies of all the transitive
dependencies in your application stack.

The primary use-case for Dependnecy Monkey is to generate software stacks that
are subsequently validated and scored in the `Amun
<https://github.com/thoth-station/amun-api>`_ service. Simply when generating
all the possible software stacks, we can find the best software stack for an
application by validating it in a CI (or Amun in case of Thoth), running the
application in the specific runtime environment (e.g. Fedora 28 with installed
native packages - RPMs) on some specific hardware configuration. Generating and
scoring all the possible software stacks is, however, most often not doable in
a reasonable time. For this purpose, Dependency Monkey can create a sample of
software stacks (see the ``distribution`` and ``seed`` parameters) that can be
taken as representatives. These representatives are scored and aggregated data
are used for predicting the best application stack (again, generated and run
through CI/Amun to make predictions more accurate by learning over time).

See :ref:`dependency_monkey` for more info.

Advises and Recommendations
===========================

In Thoth's terminology, advises and recommendations are the same. Based on
aggregated knowledge stored in the graph database, provide the best application
stack with reasoning on why the given software stack is used. There is reused
the N-ary dependency graph implementation stated above to compute possible
candidates of software stacks and based on data aggregated, there is performed
scoring of software stacks based on solely package-level data (e.g. the given
package cannot be installed into the given runtime environment) or software
stack information - the combination of packages cannot be assembled together or
there were spotted issues when the same packages were used together in some
specific versions.

Provenance Checks
=================

As Thoth aggregates information about packages available, it can verify
a user's stack against its knowledge base. See :ref:`provenance_checks`
for more info.

Package source configuration
############################

When Thoth is deployed in your infrastracture that restricts packages installed
to only trusted package source indexes, you can disable untrusted package
source indexes by setting ``THOTH_WHITELISTED_SOURCES`` environment variable.
This variable holds a comma separated list of URLs pointing to whitelisted
package source indexes respecting
`PEP-0503 <https://www.python.org/dev/peps/pep-0503/>`_ standard (the URL
is with the ``/simple`` suffix).

This environment variable is automatically fed from Thoth's graph database
in a deployment. This way Thoth's operator has full control on what package
source indexes which are used by users of Thoth.

Installation and deployment
===========================

Adviser is built using OpenShift Source-to-Image and deployed
automatically with Thoth's deployment playbooks available in the `core
repository <https://github.com/thoth-station/core>`_.

In a Thoth deployment, adviser is run based on requests comming to the
`user API <https://github.com/thoth-station/user-api>`_ - each deployed adviser
is run per a user request. You can run adviser locally as well by installing it
and using its command line interface:

::

  pip3 install thoth-adviser
  thoth-adviser --help
  # Or use git repo directly for the latest code:
  # pip3 install git+https://github.com/thoth-station/adviser

When thoth-adviser is scheduled in a deployment, it is actually executed as a
CLI with arguments passed via environment variables.

See `Dgraph <https://github.com/thoth-station/dgraph-thoth-config>`_
repository on how to run a Dgraph instance locally and
example `notebooks <https://github.com/thoth-station/notebooks>`_ which can feed
your Dgraph instance for experiments.

Running adviser locally
=======================

Often it is useful to run adviser locally to experiment or verify your changes
in implementation. You can do so easily by running:

.. code-block:: console

  pipenv install
  PYTHONPATH=. GRAPH_TLS_PATH=<graph-tls-path> GRAPH_SERVICE_HOST=<graph-service-host> pipenv run ./thoth-adviser --help

This command will set `<graph-service-host>` (Dgraph
deployed in test environment) as your source for advises and information for
resolver to correctly resolve dependencies. Feel free to use `a local
Dgraph instance`, as explaind here<https://github.com/thoth-station/thoth-storages>,
if it suits your needs. Also, follow the developer's guide to get `more
information about developer's setup
<https://github.com/thoth-station/thoth/blob/master/docs/developers_guide.rst>`_.

As adviser is very memory intense application, it is recommended to run it in a
container with memory limit set for large application stacks. To do so, use
`s2i` utility to build the container and then run it as show below:

.. code-block:: console

  s2i build . centos/python-36-centos7 thoth-adviser
  docker run -m 8G -e THOTH_ADVISER_SUBCOMMAND=advise -e GRAPH_SERVICE_HOST=<graph-service-host> thoth-adviser
