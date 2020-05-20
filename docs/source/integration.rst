.. _integration:

Integrating with Thoth
----------------------

Project Thoth can guide you on your software stacks. To consume Thoth's
recommendations, there are multiple ways on how to integrate:

* Command line interface - Thamos CLI
* Kebechet (GitHub application)
* Jupyter Notebooks
* OpenShift s2i build process
* Thamos library (not fully supported yet as API might change)


Pre-requirements for your project
=================================

To let Thoth manage your Python application, your application has to use
`Pipenv <https://pipenv.readthedocs.io/>`_ to manage virtual environment and
application dependencies. Pipenv's two main files, ``Pipfile`` and
``Pipfile.lock``, has to be placed in the root of your Python application
directory.

If you use ``requirements.txt``, the easiest way how to convert to Pipenv's
``Pipfile`` and ``Pipfile.lock`` is to run the following command:

.. code-block:: console

  pipenv install --requirements requirements.txt

And add both file produced, ``Pipfile`` and ``Pipfile.lock``, into your Git
repository.

It's also possible to use `pip <https://pip.pypa.io/en/stable/user_guide/>`_
format as well as format used by
`pip-tools <https://pypi.org/project/pip-tools/>`_. To use these formats,
you will need to adjust ``requirements_format`` configuration option in your
``.thoth.yaml`` configuration file.

.. note::

  It's recommended to use Pipenv if possible. Pipenv introduces more consistent
  files that track Python package indexes used as well as artifact hashes in the
  lock file explicitly.

By switching to ``pip``/``pip-compile`` file format the behaviour of file lookup
is following (sorted based on priority):

* if ``requirements.txt`` and ``requirements.in`` files are present,
  ``requirements.txt`` file is used as a lockfile and ``requirements.in`` states
  direct dependencies (``pip-tools`` behavior)

* if just ``requirements.in`` file is present, it is used as a file
  containing direct dependencies (``pip-tools`` behaviour)

* if just ``requirements.txt`` file is present, it is used as a file
  containing direct dependencies (raw ``pip`` behaviour)

Thoth's output of ``requirements.txt`` uses implicitly hashes of artifacts -
equivalent to ``pip-compile --generate-hashes``. It is required to state artifact
hashes if ``requirements.txt`` is treated as a lockfile.


Command Line Interface - Thamos CLI
===================================

The easiest way how to get recommendations from Thoth service is to install
`Thamos <https://thoth-station.ninja/docs/developers/thamos>`_ (Thoth's CLI and
library):

.. code-block:: console

  pip3 install -U thamos

And configure your project to use Thoth's recommendations and ask for them:

.. code-block:: console

  cd your/project/path
  thamos config
  thamos advise

Before you ask for an advise, make sure your Pipenv's files ``Pipfile`` and
optionally ``Pipfile.lock`` are present in the root directory of your project:

.. code-block:: console

  ls -la your/project/path
  ..
  .thoth.yaml
  ..
  Pipfile
  Pipfile.lock
  ..

Once Thoth responds back with recommendations, you can install your
dependencies using:

.. code-block:: console

  pipenv install --deploy --dev

Please follow `Thamos documentation for more info
<https://thoth-station.ninja/docs/developers/thamos>`_. Also check
`thoth-station/cli-examples repository <https://github.com/thoth-station/cli-examples>`__
that demonstrates an example application that using Thamos CLI.

OpenShift Python s2i build process
==================================

Thoth can be used in `OpenShift's s2i process
<https://docs.openshift.com/container-platform/3.11/using_images/s2i_images/python.html>`_
where it can produce recommendations targeting your specific hardware
configuration you use to run your application inside the cluster (e.g. specific
GPU available in the cluster).

.. note::

  Check `thoth-station/s2i-example-migration
  <https://github.com/thoth-station/s2i-example-migration>`_ with a
  step-by-step tutorial (also with a pre-recorded screencast with a
  voice-over) on how to port an already existing Python s2i application to
  Thoth.

You can find a list of base images which you can use with Thoth in `s2i-thoth
repository <https://github.com/thoth-station/s2i-thoth>`_ with detailed
instructions on how to use Thoth in the OpenShift's s2i process. The container
images are hosted at `quay.io/organization/thoth-station
<https://quay.io/organization/thoth-station>`_.

.. note::

  You can use a tool called `thoth-s2i <https://github.com/thoth-station/s2i`_
  that can automatically migrate your existing s2i application to use Thoth.

Thoth's s2i container images can be configured using environment variables
supplied to the build config:

* ``THOTH_ADVISE`` - always use the recommended stack by Thoth (even if the
  lock file is present in the repo)

* ``THOTH_PROVENANCE_CHECK`` - verify stack provenance - the provenance check
  is triggered only if the lock file is not comming from Thoth's recommendation
  engine (otherwise the stack has already verified provenance)

* ``THOTH_ASSEMBLE_DEBUG`` - run s2i's assemble script in verbose mode

* ``THOTH_DRY_RUN`` - submit stack to Thoth's recommendation engine but do not
  use the recommended lock file, use the lock file present in the repo instead

* ``THOTH_FROM_MASTER`` - Use Thamos from git instead of a PyPI release - handy
  if the released Thamos has a bug which was fixed in the master branch

* ``THOTH_HOST`` - Thoth's host to reach out to for recommendations (defaults
  to prod deployment at khemenu.thoth-station.ninja)

* ``THOTH_ERROR_FALLBACK`` - fallback to the lock file present in the
  repository if the submitted Thoth analysis fails

See also configuration options for Thoth's client present in `Thamos
documentation <https://thoth-station.ninja/docs/developers/thamos/>`_.

An example of such application can be found on `GitHub  - s2i TensorFlow
example <https://github.com/thoth-station/s2i-example>`_.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/FtW1PAuI3nk" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

Kebechet - GitHub application
=============================

TODO: write a summary

Jupyter Notebooks
=================

TODO: write a summary
