Thoth Adviser
-------------

A recommendation engine and software stack generation for project `Thoth <https://github.com/thoth-station/>`__.

There are the following main goals of thoth-adviser (as of now):

1. Provide a tool that can compute recommendations in project `Thoth <https://thoth-station.ninja>`__.
2. Check provenance of installed packages (which package source indexes are used - this is not guaranteed by pip nor Pipenv).
3. A tool called "Dependency Monkey" that generates all the possible software stacks for a project respecting dependency resolution.

To interact with a deployed Thoth, you can use the
`Thamos CLI <https://github.com/thoth-station/thamos>`__.


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
<https://github.com/thoth-station/amun-api>`__ service. Simply when generating
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

See `Dependency Monkey
<https://thoth-station.ninja/docs/developers/adviser/dependency_monkey.html>`_
for more info.

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
a user's stack against its knowledge base. See provenance_checks
for more info.

Package source configuration
############################

When Thoth is deployed in your infrastracture that restricts packages installed
to only trusted package source indexes, you can disable untrusted package
source indexes by setting ``THOTH_WHITELISTED_SOURCES`` environment variable.
This variable holds a comma separated list of URLs pointing to whitelisted
package source indexes respecting
`PEP-0503 <https://www.python.org/dev/peps/pep-0503/>`__ standard (the URL
is with the ``/simple`` suffix).

This environment variable is automatically fed from Thoth's graph database
in a deployment. This way Thoth's operator has full control on what package
source indexes which are used by users of Thoth.

Installation and deployment
===========================

Adviser is built using OpenShift Source-to-Image and deployed
automatically with Thoth's deployment playbooks available in the `core
repository <https://github.com/thoth-station/core>`__.

In a Thoth deployment, adviser is run based on requests comming to the
`user API <https://github.com/thoth-station/user-api>`__ - each deployed adviser
is run per a user request. You can run adviser locally as well by installing it
and using its command line interface:

::

  pip3 install thoth-adviser
  thoth-adviser --help
  # Or use git repo directly for the latest code:
  # pip3 install git+https://github.com/thoth-station/adviser

When thoth-adviser is scheduled in a deployment, it is actually executed as a
CLI with arguments passed via environment variables.

See `thoth-storages repository <https://github.com/thoth-station/storages>`__
repository on how to run Thoth's knowledge graph locally and
example `notebooks <https://github.com/thoth-station/notebooks>`__ for experiments.

Adviser also considers environment variable ``THOTH_ADVISER_BLOCKED_UNITS`` that
states a comma separated list of pipeline units that should not be added to
the pipeline. This can be handy if an issue with a unit arises in a deployment - Thoth
operator can remove pipeline unit by adjusting adviser template and provide
this configuration without a need to deploy a new version of adviser.

Running adviser locally
=======================

Often it is useful to run adviser locally to experiment or verify your changes
in implementation. You can do so easily by running:

.. code-block:: console

  pipenv install
  PYTHONPATH=. pipenv run ./thoth-adviser --help

This command will run adviser locally - adviser will try to connect to a local
PostgreSQL instance and compute recommendations. `Browse docs here
<https://github.com/thoth-station/thoth-storages>`__ to see how to setup a local
PostgreSQL instance. Also, follow the developer's guide to get `more
information about developer's setup
<https://github.com/thoth-station/thoth/blob/master/docs/developers_guide.rst>`__.

