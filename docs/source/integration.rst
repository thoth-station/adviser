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
<https://thoth-station.ninja/docs/developers/thamos>`_.

OpenShift Python s2i build process
==================================

Thoth can be used in `OpenShift's s2i process
<https://docs.openshift.com/container-platform/3.11/using_images/s2i_images/python.html>`_
where it can produce recommendations targeting your specific hardware
configuration you use to run your application inside the cluster (e.g. specific
GPU available in the cluster).

You can find a list of base images which you can use with Thoth in `s2i-thoth
repository <https://github.com/thoth-station/s2i-thoth>`_ with detailed
instructions on how to use Thoth in the OpenShift's s2i process. The container
images are hosted at `quay.io/organization/thoth-station
<https://quay.io/organization/thoth-station>`_.

Thoth's s2i container images can be configured using environment variables
supplied to the build config:

* ``THOTH_ADVISE`` - always use the recommended stack by Thoth (even if
  ``Pipfile.lock`` is present in the repo)

* ``THOTH_ASSEMBLE_DEBUG`` - run s2i's assemble script in verbose mode

* ``THOTH_DRY_RUN`` - submit stack to Thoth's recommendation engine but do not
  use the recommended ``Pipfile.lock`` file, use the ``Pipfile.lock`` file
  present in the repo instead

* ``THOTH_FROM_MASTER`` - Use Thamos from git instead of a PyPI release - handy
  if the released Thamos has a bug which was fixed in the master branch

* ``THOTH_HOST`` - Thoth's host to reach out to for recommendations (defaults
  to prod deployment at khemenu.thoth-station.ninja)

* ``THOTH_ERROR_FALLBACK`` - fallback to the ``Pipfile.lock`` present in the
  repository if the submitted Thoth analysis fails

See also configuration options for Thoth's client present in `Thamos
documentation <https://thoth-station.ninja/docs/developers/thamos/>`_.

An example of such application can be found on `GitHub  - s2i TensorFlow
example <https://github.com/thoth-station/s2i-example-tensorflow>`_.

Kebechet - GitHub application
=============================

TODO: write a summary

Jupyter Notebooks
=================

TODO: write a summary
