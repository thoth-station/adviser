thoth-adviser
-------------

A recommendation engine for project `Thoth <https://github.com/thoth-station/>`_.

There are three main goals of thoth-adviser (as of now):

1. Provide a library that coverts basic operations in Python ecosystem (such as operations with package index sources, project specific operations on libraries used).
2. Provide a tool that can compute recommendations in project `Thoth <https://github.com/thoth-station/thoth>`_.
3. Check provenance of installed packages (which package source indexes are used - this is not guaranteed by pip nor Pipenv).

To interact with a deployed Thoth, you can use the
`Thamos CLI <https://github.com/thoth-station/tamos>`_.

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

Recommendations
===============

TBD.


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
