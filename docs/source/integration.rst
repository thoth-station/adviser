.. _integration:

Integrating with Thoth
----------------------

Project Thoth can give advises to your software stacks. To consume Thoth's
recommendations, there are multiple ways on how to integrate:

* Command line interface - Thamos CLI
* Kebechet (GitHub application)
* Jupyter Notebooks
* OpenShift s2i build process
* Thamos library (not fully supported yet as API might change)


Pre-requirements for your project
=================================

To let Thoth manage your Python application, your application has to use
`Pipenv <https://pipenv.readthedocs.io/>`__ to manage virtual environment and
application dependencies. Pipenv's two main files, ``Pipfile`` and
``Pipfile.lock``, has to be placed in the root of your Python application
directory.

If you use ``requirements.txt``, the easiest way how to convert to Pipenv's
``Pipfile`` and ``Pipfile.lock`` is to run the following command:

.. code-block:: console

  pipenv install --requirements requirements.txt

And add both file produced, ``Pipfile`` and ``Pipfile.lock``, into your Git
repository.

It's also possible to use `pip <https://pip.pypa.io/en/stable/user_guide/>`__
format as well as format used by
`pip-tools <https://pypi.org/project/pip-tools/>`__. To use these formats,
you will need to adjust ``requirements_format`` configuration option in your
``.thoth.yaml`` configuration file.

.. note::

  It's recommended to use Pipenv files if possible. Pipenv introduces more consistent
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
`Thamos <https://thoth-station.ninja/docs/developers/thamos>`__ (Thoth's CLI
and library):

.. code-block:: console

  pip3 install -U thamos

And configure your project to use Thoth's recommendations and ask for them:

.. code-block:: console

  cd your/project/path
  thamos config
  thamos advise

Before you ask for an advise, make sure your Pipenv's files ``Pipfile`` and
optionally ``Pipfile.lock`` are present in the root directory of your project
or respecting overlays directory configuration:

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

  thamos install --deploy --dev
  # Or directly:
  # thamos advise --install --dev

Please follow `Thamos documentation for more info
<https://thoth-station.ninja/docs/developers/thamos>`__. Also check
`thoth-station/cli-examples repository <https://github.com/thoth-station/cli-examples>`__
that demonstrates example applications that use Thamos CLI.

OpenShift Python s2i build process
==================================

Thoth can be used in `OpenShift's s2i process
<https://docs.openshift.com/container-platform/3.11/using_images/s2i_images/python.html>`__
where it can produce recommendations targeting your specific hardware
configuration you use to run your application inside the cluster (e.g. specific
GPU available in the cluster).

.. note::

  Check `thoth-station/s2i-example-migration
  <https://github.com/thoth-station/s2i-example-migration>`__ with a
  step-by-step tutorial on how to port an already existing Python s2i
  application to Thoth.

You can find a list of base images which you can use with Thoth in `s2i-thoth
repository <https://github.com/thoth-station/s2i-thoth>`__ with detailed
instructions on how to use Thoth in the OpenShift's s2i process. The container
images are hosted at `quay.io/organization/thoth-station
<https://quay.io/organization/thoth-station>`__.

.. note::

  You can use a tool called `thoth-s2i
  <https://github.com/thoth-station/s2i>`__ that can automatically migrate your
  existing s2i application to use Thoth.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/FtW1PAuI3nk" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

Thoth's s2i container images can be configured using environment variables
supplied to the build config. Follow `thoth-station/s2i-thoth
<https://github.com/thoth-station/s2i-thoth>`__ repository with all the
required instructions to setup OpenShift S2I. See also configuration options
for Thoth's client present in `Thamos documentation
<https://thoth-station.ninja/docs/developers/thamos/>`__ that apply in the
build process as it uses Thamos under the hood.

To see available S2I runtime environments for which backend can give you
advises, issue:

.. code-block:: console

  thamos s2i

An example of an S2I application powered by Thoth S2I can be found in
`thoth-station/s2i-example <https://github.com/thoth-station/s2i-example>`__
repository.

Kebechet - GitHub application
=============================

Here is are few easy steps describing how you can add Kebechet to your GitHub
project:

* Install `Thamos <https://pypi.org/project/thamos>`__ CLI tool:

  .. code-block:: console

    pip3 install thamos  # keep in mind: requires Python 3.6+!!

* Go to the repository that should be managed by Thoth which already has ``Pipfile`` present:

  .. code-block:: console

     cd ~/git/repo/

* Setup Thamos configuration:

  .. code-block:: console

     thamos config

That’s it - thamos would create a "``.thoth.yaml``" file for you. This file can
be added to your Git repository and GitHub application can take care of your
project.

Next, you can adjust managers you want to have enabled on your repository.
Here, for example, we want ``version`` and ``update`` manager to run on the
demo repo so the configuration is:

.. code-block:: yaml

    managers:
        - name: update
          configuration:
            labels: [bot, kebechet]
        - name: version
          configuration:
            labels: [bot, kebechet]
            changelog_file: true

Kebechet cares about the managers you add under the manager section. You will
find how to define the manager config under each of the manager readme -
`kebechet/managers
<https://github.com/thoth-station/kebechet/tree/master/kebechet/managers>`__.

Now that you are done with the setup of which managers you want to be run on
your project, you are done with the major part.  We would next install the
GitHub app to ensure we receive webhooks from the repository, please install
`Khebhut <https://github.com/marketplace/khebhut>`__, which is an alias for
Kebechet.  That's it, Kebechet is now ready to maintain your Python project.

Container image build analyses
==============================

To help us improving recommendations, you can use integrations with container
image build systems that can report information about builds to Thoth to
improve recommendations. Simply, we aggregate information about build failures,
learn from them and improve the recommendation engine so that it will provide
you a Python stack that can be assembled.

If you use OpenShift builds, you can install a component called build-watcher
which will send us relevant information so that we can improve Thoth's
recommendation engine. Follow instructions that can be found in
`thoth-station/build-watcher
<https://github.com/thoth-station/build-watcher/>`__ repository for more info.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/bSkjSU0S5vs" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

When using `AICoE-CI <https://github.com/AICoE/aicoe-ci>`__, build information
are automatically sent to Thoth backend.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/4ENk4pf5CpY" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

Jupyter Notebooks
=================

Follow documentation in `thoth-station/jupyterlab-requirements
<https://github.com/thoth-station/jupyterlab-requirements>`__ repository for
more info.
