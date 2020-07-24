.. _sieves:

Sieve pipeline unit type
------------------------

The second pipeline unit type triggered after :ref:`boot type pipeline units
<boots>` is called ":class:`sieve <thoth.adviser.sieve.Sieve>`". The main
purpose of this pipeline unit is to filter out (hence "sieve") packages that
should not occur in the resulting stack. It's called on each and every package
that is resolved based on direct or transitive dependencies of the application
stack supplied.

The pipeline unit of type :class:`sieve <thoth.adviser.sieve.Sieve>` accepts a
generator of resolved package-versions (see ``PackageVersion`` abstraction in
``thoth-python`` library) and decides which of these package versions can be
included in the resulting stack. The generator of package-versions supplied is
sorted based on `Python's version specification
<https://www.python.org/dev/peps/pep-0440/>`_ starting from the latest release
down to the oldest one (respecting version string, not release date). The list
will be shrinked based on ``limit_latest_versions`` (if supplied to the
adviser) after pipeline sieve runs - this option reduces the state space
considered. If sieves accept more package versions than
``limit_latest_versions`` package versions they will be reduced to
``limit_latest_versions`` size.

It's guaranteed that the list will contain package-versions in a specific
(locked) version with information about the Python package index from where the
given dependency came from (tripled "package name", "locked package version"
and "index url" uniquely identify any Python package, see :ref:`compatibility
section <compatibility>` for additional info on Python package index specific
resolution). It's also guaranteed that the generator will contain packages of a
same type (same package name).

.. note::

  Each sieve can be run multiple times during the resolution. It can be run
  multiple times even on packages of a same type based on dependency graph
  resolution. An example can be package ``six`` that is a dependency of many
  packages in the Python ecosystem and each package can have different version
  range requirements on package ``six``.

Main usage
==========

* Filter out packages, package-versions respectively, which should not occur in
  the resulting software stack

  * Returning an empty list discards all the resolved versions

  * Raising exception :class:`NotAcceptable
    <thoth.adviser.exceptions.NotAcceptable>` has same effect as returning an
    empty list (compatibility with :ref:`step pipeline unit <steps>`)

* Prematurely end resolution based on the sieve reached

  * Raising exception :class:`EagerStopPipeline
    <thoth.adviser.exceptions.EagerStopPipeline>` will cause stopping the whole
    resolver run and causing resolver to return products computed so far

* Removing a library from a stack even though it is stated as a dependency by
  raising :class:`SkipPackage <thoth.adviser.exceptions.SkipPackage>`

.. note::

  Even if pipeline sieves discard all the versions for a certain package, the
  resolution can be still successful. An example can be discarding dependency
  ``tensorboard`` from a TensorFlow stack. Dependency ``tensorboard`` is
  present only in some releases of ``tensorflow`` package.

Real world examples
===================

* Filter out packages like `enum34 <https://pypi.org/project/enum34/>`_ from
  the resolved software stack that will not install into the given software
  environment (`enum34 <https://pypi.org/project/enum34/>`_ is a backport of
  `Enum <https://docs.python.org/3/library/enum.html>`_ to older Python
  releases so it will not be installed for Python3.4+, if `environment markers
  <https://www.python.org/dev/peps/pep-0496/>`_ are present and applied)

* Filtering packages that have installation issues into the requested software
  environment - an example can be legacy Python2 packages that fail
  installation in Python3 environments due to syntax errors in ``setup.py``

* Filtering packages that have runtime issues (a package installs but fails
  during application start - e.g. bad release)

* Filter out Python packages that use Python package index that is not allowed
  (restricted environments)

* Filter out packages that require native packages or ABI provided by a native
  package that are not present in the software environment used (see `Thoth's
  analyses of container images
  <https://github.com/thoth-station/package-extract>`_ that are aggregated into
  Thoth's knowledge base and available for Thoth's adviser)

* Filter out packages that are nightly builds or pre-releases in case of
  ``STABLE`` recommendation type or disabled pre-releases configuration option
  in ``Pipfile``

* A library maintainer added `enum34 package <https://pypi.org/project/enum34/>`_
  as a library dependency but did not restrict requirements to Python version with
  an environment marker:

  .. code-block:: console

     enum34>=1.0; python_version < '3.4'

  The resolver can skip this package based on a pipeline sieve specific to the
  library which would raise :class:`SkipPackage
  <thoth.adviser.exceptions.SkipPackage>` exception if the ``enum34`` would be
  used with newer Python version.

An example implementation
=========================

.. code-block:: python

  from typing import Generator
  from thoth.python import PackageVersion

  from thoth.adviser import Sieve

  class ExampleSieve(Sieve):
      """An example sieve implementation to demonstrate sieve purpose."""

      def run(self, package_versions: Generator[PackageVersion, None, None]) -> Generator[PackageVersion, None, None]:
          for package_version in package_versions:
            if self.context.project.prereleases_allowed:
                _LOGGER.info(
                    "Project accepts pre-releases, skipping cutting pre-releases step"
                )
                yield package_version

            if package_version.semantic_version.is_prerelease:
                _LOGGER.debug(
                    "Removing package %s - pre-releases are disabled",
                    package_version.to_tuple(),
                )
                continue

            yield package_version

The implementation can also provide other methods, such as :func:`Unit.pre_run
<thoth.adviser.unit.Unit.post_run>`, :func:`Unit.post_run
<thoth.adviser.unit.Unit.post_run>` or :func:`Unit.post_run_report
<thoth.adviser.unit.Unit.post_run>` and pipeline unit configuration adjustment.
See :ref:`unit documentation <unit>` for more info.
