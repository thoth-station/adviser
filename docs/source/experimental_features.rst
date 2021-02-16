.. _experimental_features:

Resolver's experimental features
--------------------------------

By using Thoth as a recommendation engine, you can enable some experimental
features. These experimental features diverge from the ones provided by the
official Python packaging, but can be nifty in some cases.

All the experimental features require using `Pipenv
<https://docs.pipenv.org/>`__ files (``Pipfile`` and ``Pipfile.lock``) and are
enabled by stating them in the ``[thoth]`` specific section.

.. note::

  You can use `micropipenv <https://github.com/thoth-station/micropipenv>`__ to
  convert resulting Pipfile/Pipfile.lock files to requirement files if you wish
  to use `pip-tools <https://pypi.org/project/pip-tools>`__ or raw pip.

To maintain compatibility with Pipenv, any changes done in ``[thoth]`` section
are not checked for changes (the ``--deploy`` flag which verifies hash of
Pipfile during deployment). This means you can perform any changes to Thoth
specific configuration and they will not block using Pipenv. Also Pipenv
ignores ``[thoth]`` section. This section simply acts as a set of hints for
Thoth resolver to resolve specific set of packages based on the configuration.
Generally, these options will result in different stacks resolved in
comparision to using other resolvers (such as Pipenv, pip-tools, ...).

Selectively enabling pre-releases
=================================

This is implementation of `PEEP-0007 Pipenv draft
<https://github.com/pypa/pipenv/pull/4607>`__. As Pipenv allows only turning
on/off pre-releases for all the packages in the dependency graph, this option
enables users to selectively turn on/off pre-releases for any package in the
dependency graph - transitive as well as direct packages.

This can be useful if some packages should be present as pre-releases or they
do not have any release yet, except for pre-releases. See the `upstream
discussion <https://github.com/pypa/pipenv/issues/1760>`__.

The following configuration will enable resolving pre-releases that match
`tensorflow>=2.3`:

.. code-block:: toml

  [[source]]
  url = "https://pypi.org/simple"
  verify_ssl = true
  name = "pypi"

  [packages]
  tensorflow = ">=2.3"

  [dev-packages]

  [requires]
  python_version = "3.9"

  [pipenv]
  allow_prereleases = false

  [thoth.allow_prereleases]
  tensorflow = true

It is important to make sure the Pipenv specific ``allow_prereleases``
configuration option is set to ``false`` (it is by default) Otherwise, all
packages in the dependency graph will be treated as pre-releases and
``[thoth.allow_prereleases]`` section will be ignored.

It is also possible to allow pre-releases for packages that occur in the
dependency graph but are not direct dependencies of the application stack:

.. code-block:: toml

  [[source]]
  url = "https://pypi.org/simple"
  verify_ssl = true
  name = "pypi"

  [packages]
  tensorflow = "*"

  [dev-packages]

  [requires]
  python_version = "3.9"

  [pipenv]
  allow_prereleases = false

  [thoth.allow_prereleases]
  numpy = true

In this case, also pre-releases of NumPy will be considered during the
dependency resolution if NumPy occurs in the stack (a transitively dependency
of the application stack) and NumPy pre-releases are available.

Strict index configuration
==========================

By default, Thoth suggests which Python package indexes should be used to
consume recommended Python packages. If you wish to explicitly state Python
package indexes from where your packages should be consumed, you can enforce
this behavior by providing ``disable_index_adjustment = true`` experimental
feature as follows:

.. code-block:: toml

  [[source]]
  url = "https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple/"
  verify_ssl = true
  name = "aicoe-tensorflow"

  [packages]
  tensorflow = "*"

  [dev-packages]

  [requires]
  python_version = "3.9"

  [thoth]
  disable_index_adjustment = true

Using the Pipfile shown above will enforce resolver to look for packages only
on explicitly configured Python indexes, that is ``aicoe-tensorflow`` index in
the example above. Note that all the packages, direct as well as transitive
packages need to be hosted on the specified index in order to resolve the whole
application stack. If that's not the case, the resolution process will fail.

If you wish to consume some packages from one index and others from another
index, you can provide multiple Python package sources as shown below:

.. code-block:: toml

  [[source]]
  url = "https://pypi.org/simple"
  verify_ssl = true
  name = "pypi"

  [[source]]
  url = "https://tensorflow.pypi.thoth-station.ninja/index/manylinux2010/AVX2/simple/"
  verify_ssl = true
  name = "aicoe-tensorflow"

  [packages]
  tensorflow = {version="*", index="aicoe-tensorflow"}

  [dev-packages]

  [requires]
  python_version = "3.9"

  [thoth]
  disable_index_adjustment = true

Based on the configuration shown above, the resolver will restrict TensorFlow
packages only to those hosted on ``aicoe-tensorflow`` (and will not take into
account any other Python package indexes known where TensorFlow package is
hosted) and the remaining packages will be looked up on ``aicoe-tensorflow``
index as well as on ``pypi`` index as configured. No other Python package
indexes will be considered during the resolution process. Note you can specify
Python package index to be used per dependency, see `Pipenv configuration
<https://pipenv.pypa.io/en/latest/advanced/#specifying-package-indexes>`__.
Also note, Pipenv does not enforce this configuration as it treats Python
package indexes as mirrors (see :ref:`compatibility` section for more info).
