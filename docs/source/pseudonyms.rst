.. _pseudonyms:

Pseudonym pipeline unit type
----------------------------

.. note::

  💊 :ref:`Check pseudonym prescription pipeline unit <prescription_pseudonyms>`
  for a higher-level abstraction.

This pipeline unit was introduced to provide "pseudonym" functionality. This
functionality is handy if you would like to create an alternative to the
package in the software stack. This alternative can be considered on package
name level or version level. Cross-index resolution (index level alternative)
is guaranteed by the resolution logic.

.. warning::

  ⚠️ Try to avoid creating alternatives if they do not produce valid alternatives
  or they result in too many new states. This has significant performance
  impact in the resolution process.

Each pseudonym is uniquely identified by
``unit_instance.configuration["package_name"]`` string derived out of
``Pseudonym.CONFIGURATION_DEFAULT["package_name"]`` that corresponds to the
package name for which the pipeline unit should be called.  This is an
optimization to the resolution process.

Main usage
==========

* Adding "aliases" to the software stack.

  * An example could be ``intel-tensorflow`` package that provides the same
    functionality as ``tensorflow``, hence ``intel-tensorflow`` can be
    considered as a valid alternative to the resolution process.

* Adding versions of packages that were not listed in the dependency listing of
  a library/application but are valid alternatives (underpinning issues).

Real world examples
===================

* Substitute all ``tensorflow`` packages in the software stack with their
  ``intel-tensorflow`` counterparts.

* Add TensorFlow in version 2.1.0 to the stack where TensorFlow in version
  2.2.0 would be resolved even though the application states
  TensorFlow==2.1.0 as a dependency - suitable for Dependency Monkey runs or
  performing "post-release" fixes in version range specifications
  (underpinning issues).

Justifications in the recommended software stacks
=================================================

Follow the :ref:`linked documentation for providing valuable information to
users on actions performed in pipeline units implemented <justifications>`.

An example implementation
=========================

.. code-block:: python

    import logging
    from typing import Any
    from typing import Dict
    from typing import Generator
    from typing import Optional
    from typing import Tuple
    from typing import Set
    from typing import TYPE_CHECKING

    import attr
    from thoth.python import PackageVersion

    from ..pseudonym import Pseudonym

    if TYPE_CHECKING:
        from ..pipeline_builder import PipelineBuilderContext

    _LOGGER = logging.getLogger(__name__)


    @attr.s(slots=True)
    class TensorFlowPseudonym(Pseudonym):
        """A TensorFlow pseudonym."""

        CONFIGURATION_DEFAULT: Dict[str, Any] = {"package_name": "tensorflow"}  # Operates on "tensorflow" package.

        _pseudonyms = attr.ib(type=Optional[Set[Tuple[str, str, str]]], default=None, init=False)

        def pre_run(self) -> None:
            """Initialize this pipeline unit before each run."""
            self._pseudonyms = None

        @classmethod
        def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
            """Register self."""
            if builder_context.is_adviser_pipeline() and not builder_context.is_included(cls):
                yield {}
                return None

            yield from ()
            return None

        def run(self, package_version: PackageVersion) -> Generator[Tuple[str, str, str], None, None]:
            """Map TensorFlow packages to intel-tensorflow alternatives."""
            if package_version.index.url != "https://pypi.org/simple":
                # Adjust only for PyPI index.
                return None

            if self._pseudonyms is None:
                # Be lazy with queries to the database.
                runtime_environment = self.context.project.runtime_environment
                self._pseudonyms = {i[1] for i in self.context.graph.get_solved_python_package_versions_all(
                    package_name="intel-tensorflow",
                    package_version=None,
                    index_url="https://pypi.org/simple",
                    count=None,
                    os_name=runtime_environment.operating_system.name,
                    os_version=runtime_environment.operating_system.version,
                    python_version=runtime_environment.python_version,
                    distinct=True,
                    is_missing=False,
                )}

            if package_version.locked_version in self._pseudonyms:
                yield "intel-tensorflow", package_version.locked_version, "https://pypi.org/simple"


The implementation can also provide other methods, such as :func:`Unit.pre_run
<thoth.adviser.unit.Unit.post_run>`, :func:`Unit.post_run
<thoth.adviser.unit.Unit.post_run>` or :func:`Unit.post_run_report
<thoth.adviser.unit.Unit.post_run>` and pipeline unit configuration adjustment.
See :ref:`unit documentation <unit>` for more info.
