thoth-adviser
-------------

.. image:: https://api.codacy.com/project/badge/Grade/5f0c2a98fe4247cf803080c9c8f36bb8
   :alt: Codacy Badge
   :target: https://app.codacy.com/app/thoth-station/adviser?utm_source=github.com&utm_medium=referral&utm_content=thoth-station/adviser&utm_campaign=Badge_Grade_Dashboard

A recommendation engine for project `Thoth <https://github.com/thoth-station/>`_.

There are four main goals of thoth-adviser (as of now):

1. Provide a library that coverts basic operations in Python ecosystem (such as operations with package index sources, project specific operations on libraries used).
2. Provide a tool that can compute recommendations in project `Thoth <https://github.com/thoth-station/thoth>`_.
3. Check provenance of installed packages (which package source indexes are used - this is not guaranteed by pip nor Pipenv).
4. A tool called "Dependency Monkey" that generates all the possible software stacks for a project respecting dependency resolution.

To interact with a deployed Thoth, you can use the
`Thamos CLI <https://github.com/thoth-station/thamos>`_.

Dependency Graph
================

Adviser's implementation uses internal structure called "Dependency Graph" for
generating possible software stacks. This generation is done for:
1. Computing recommendations by scoring computed software stacks - the stack with the highest score is the best possible software stack for an application.
2. Generating samples of software stacks for Dependency Monkey - these stacks are validated and scored (e.g. performance index) in the `Amun <https://github.com/thoth-station/amun-api`_ service.

The dependency graph is implemented as an N-ary graph. You can imagine the
graph as a generic binary tree, except:
1. Each node is constructed of N pakages in some specific versions (not binary nodes, but N-ary nodes).
2. There can be cycles (thus graph and not a tree).

The resolution itself can be done using two sources (see CLI help for configuration info):
1. The graph database used in the Thoth project - this database states relevant packages in the Python ecosystem with relations between them (what dependency in what version is required with previously resolved versions using `solver <https://github.com/thoth-station/solver>`_).
2. `PyPI <https://pypi.org>`_ (or any Python Warehouse instance) - the resolution is done against the "upstream" (ecosystem as a whole) so one can resolve any dependencies in the PyPI ecosystem and compute possible software stacks.

The advantage of using Thoth's database is the fact that this database states
observations about packages and software stacks so that the database itself can
help with better resolution mechanism (the latet is not always the best
choice). In this case the graph database is also helping with offline
resolution (Python is a dynamic programming language, what dependencies will be
installed can be determined during installation - e.g. based on operating
system).


Development of Dependency Graph
###############################

If you are a developer and would like to speed up your work, dependency graph
has a capability to be pickled onto disk and loaded back into memory on demand.
To control this behavior you can use ``THOTH_ADVISER_FILEDUMP`` environment
variable stating file into which the constructed graph should be deserialized
(in case of this file does not exist) or loaded into back into memory (if file
exists). Besides that, you can also supply environment variable
``THOTH_ADVISER_NO_DIGESTS`` set to ``1`` if you do not care about package
hashes in resulting Pipfile.lock files.

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
native packages - RPMs) on some specific hardware conifguration. Generating and
scoring all the possible software stacks is, however, most often not doable in
a reasonable time. For this purpose, Dependnecy Monkey can create a sample of
software stacks (see the ``distribution`` and ``seed`` parameters) that can be
taken as representatives. These representatives are scored and aggregated data
are used for predicting the best application stack (again, generated and run
through CI/Amun to make predictions more accurate by learning over time).

See `Dependency Monkey design document for more info
<https://github.com/thoth-station/adviser/blob/master/docs/dependency_monkey.md>`_.

Advises and Recommendations
===========================

In Thoth's terminology, advises and recommendations are the same. Based on
aggregated knowledge stored in the graph database, provide the best application
stack with reasoning on why the given software stack is used. There is reused
the N-ary dependency graph implementation stated above to compute possible
candidates of software stacks and based on data aggregated, there is performed
scoring of software stacks based on solaly package-level data (e.g. the given
package cannot be installed into the given runtime environment) or software
stack information - the combination of packages cannot be assembled together or
there were spotted issues when the some packages were used together in some
specific versions.

TBD: add more info

Provenance Checks
=================

The provenance check is done against Pipenv and Pipenv.lock that are expected
as an input. The output is a structured report (with metadata) that states
issues found in the application stack. There are currently reported the
following issues:

1. ``ERROR``/``ARTIFACT-DIFFERENT-SOURCE`` - reported if a package/artifact **is** installed from a different package source index in comparision to the configured one
2. ``INFO``/``ARTIFACT-POSSIBLE-DIFFERENT-SOURCE`` - reported if a package/artifact **can be** installed from a different package source index in comparision to the configured one
3. ``WARNING``/``DIFFERENT-ARTIFACTS-ON-SOURCES`` - there are present different artifacts on the package source indexes and configuration does not state explicitly which package source index should be used for installing package - this warning recommends explictly stating package source index to guarantee the expected artifacts are used
4. ``ERROR``/``MISSING-PACKAGE`` - the given package was not found on package source index (the configured one or any of other package source indexes available)
5. ``ERROR``/``INVALID-ARTIFACT-HASH`` - the artifact hash that is used for the downloaded package was not found on the package source index - possibly the artifact has changed over time (dangerous) or was removed from the package source index

The provenance check is done against computed hashes present in the
Pipfile.lock respecting package source index configuration.

There are also performed checks on configured package source indexes which
can report the following issues:

1. ``ERROR``/``SOURCE-NOT-WHITELISTED`` - a package source index configured was not whitelisted (see bellow)
2. ``WARNING``/``INSECURE-SOURCE`` - a package source index configured does not use SSL/TLS verification casuing insecure connections

The implementation respects `PEP-0503 <https://www.python.org/dev/peps/pep-0503/>`_ specification.

If you have your own `Warehouse <https://warehouse.pypa.io/>`_ instance
deployed for managing Python packages, you can configure
``THOTH_ADVISER_WAREHOUSES`` environment variable to point on it (a comma
separated list). This is to optimize traffic - instead of directly scanning
the ``simple`` index, there will be used `JSON API
<https://warehouse.pypa.io/api-reference/json/>`_ exposed by the Warehouse.

See `Pipenv documentation <https://pipenv.readthedocs.io/en/latest/advanced/#specifying-package-indexes>`_
for more info on how to specify package indexes.

Provenance issues reported by example
#####################################

1. ``ERROR``/``ARTIFACT-DIFFERENT-SOURCE``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I have configured TensorFlow to be installed from
`AICoE index <https://index-aicoe.a3c1.starter-us-west-1.openshiftapps.com>`_
with optimized TensorFlow builds for my specific hardware with specific
configuration (e.g. Kafka support). The Python's resolution did not respect
this configuration and fallbacked to the public PyPI.

Note: Python packaging does not treat different package sources as different
sources of packages, but rather treats them as mirrors. If installing a
package from one package source index fails, there is perfomed a fallback to
another one. Pipenv has configuration option to specify source package index
to be used per package, but it is just a "hint" which should be tried first -
the actual artifact a user ends up with might come from a different package
index (based on sources listing in Pipenv) without any warning reported to
user.

2. ``INFO``/``ARTIFACT-POSSIBLE-DIFFERENT-SOURCE``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I have configured at least two source package indexes - let's say the public
`PyPI <https://pypi.org>`_ and Red Hat's 
`AICoE index <https://index-aicoe.a3c1.starter-us-west-1.openshiftapps.com>`_.
I have explicitly specified package TensorFlow to be installed from the AICoE
index. If this warning is reported, it means that the PyPI index has exactly
the same artifact (based on artifact hash) that is available on the AICoE index.
That means that these artifact can be installed from AICoE index as well as from
PyPI. As artifact hashes match, this report is not treated as an error, but is
rather informative to the user.

3. ``WARNING``/``DIFFERENT-ARTIFACTS-ON-SOURCES``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I install TensorFlow without specifying explicitly which package source index
should be used. As I configured two package source indexes - AICoE index and
the public PyPI index, both have TensorFlow available, however these packages
(the built artifacts) differ. The provenance check is suggesting to
explicitly specify which package source index should be used when installing
TensorFlow so that which TensorFlow build is used is not dependent on
hardware and time when the actual TensorFlow resolution is done.

4. ``ERROR``/``MISSING-PACKAGE``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The package stated in the Pipfile or Pipfile.lock was not found on
index - eigher on the configured one for package or on any other source
package index stated in the sources listing.

5. ``ERROR``/``INVALID-ARTIFACT-HASH``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The hash of artifact was not found - this can happen if the hash was
changed by hand in the Pipfile.lock, the artifact is not present on package
index anymore or the artifact has changed so it is no longer the expected
package based on artifact hash. Running ``pipenv install --deploy`` will fail
in production (e.g. when OpenShift's s2i is run).

Package source configuration
############################

When Thoth is deployed in your infrasture that restricts packages installed
to only trusted package source indexes, you can disable untrusted package
source indexes by setting ``THOTH_WHITELISTED_SOURCES`` environment variable.
This variable holds a comma separated list of URLs pointing to whitelisted
package source indexes respecting
`PEP-0503 <https://www.python.org/dev/peps/pep-0503/>`_ standard (the URL
is with the ``/simple`` suffix).

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

Running adviser locally
=======================

Often it is useful to run adviser locally to experiment or verify your changes in implementation. You can do so easily by running:

.. code-block:: console

  $ pipenv install
  $ PYTHONPATH=. JANUSGRAPH_SERVICE_HOST=janusgraph.test.thoth-station.ninja pipenv run ./thoth-adviser --help

This command will set `janusgraph.test.thoth-station.ninja` (JanusGraph deployed in test environment) as your source for advises and information for resolver to correctly resovle dependencies. Feel free to use `a local JanusGraph instance <https://github.com/thoth-station/janusgraph-thoth-config#running-janusgraph-instance-locally>`_ if it suits your needs. Also, follow the developer's guide to get `more information about developer's setup <https://github.com/thoth-station/thoth/blob/master/docs/developers_guide.rst>`_ .

As adviser is very memory intense application, it is recommended to run it in a container with memory limit set for large application stacks. To do so, use `s2i` utility to build the container and then run it as show below:

.. code-block:: console

  $ s2i build . centos/python-36-centos7 thoth-adviser
  $ docker run -m 8G -e THOTH_ADVISER_SUBCOMMAND=advise -e JANUSGRAPH_SERVICE_HOST=janusgraph.test.thoth-station.ninja thoth-adviser

libdependency_graph.so
======================

The adviser implementation uses a library written in C/C++ that can effectively
produce software stacks for scoring (adviser) or for inspection jobs
(dependency monkey). This library is present in the
``thoth/adviser/python/bin`` directory. You can find all the relevant files
(``Makefile``, ``Dockerfile``) to build this library. The repository is by
default shipped with an ``*.so`` file (the file produced by ``Makefile``) and
subsequently loaded by the adviser implementation using Python's ctypes. This
library is executed as a standalone process which writes stacks into a pipe
from which they are consumed in the main adviser's Python process and
scored/submitted to Amun for inspections.

To build this library on your own, you can use ``make``:

::

   make

Also make sure the C++ STL ABI is compatible when you are deploying adviser,
otherwise you can encounter issues like the following:

::

  OSError: /lib64/libstdc++.so.6: version `CXXABI_1.3.8' not found (required by /opt/app-root/src/thoth/adviser/python/bin/libdependency_graph.so)

To target this issue, there was created a containerized build, which can be
done using:

::

  make container-build

This build will produce the ``libdependency_graph.so`` file in a container (use
base image you would like to be compatible with) and copied to host for use.

