.. _wraps:

Wrap pipeline unit type
-----------------------

.. note::

  💊 :ref:`Check wrap prescription pipeline unit <prescription_wraps>` for
  a higher-level abstraction.

The last pipeline unit type is named ":class:`wrap <thoth.adviser.wrap.Wrap>`".
This pipeline unit is called after a final state is accepted by :ref:`strides
<strides>`.

.. note::

  Based on internal optimizations done for faster resolution process, wraps do
  not need to be called for all the states resolved and accepted by strides. If
  a final state will not be considered as part of the pipeline result
  respecting ``count`` parameter (number of software stacks returned based on
  their score), wrap pipeline units are not called.

The wrap pipeline unit can perform logic on already accepted final state. A
possible use case for wrap pipeline unit can be addition of another
justification based on the packages resolved. This is handy if you want to add
a justification that does not impact stack score or its inclusion to the
pipeline products (otherwise, a step pipeline unit should be used).

.. note::

  Raising any exception in a wrap causes the pipeline resolution to halt, with
  a corresponding failure that reports the exception message.

Main usage
==========

* Add justification to the final pipeline product without affecting the product
  score or inclusion of the product into the final results

* Additionally adjust runtime environment recommended back to user

* Register a callback function that should be called once a certain software stack
  is found

Real world examples
===================

* Notify about Intel's MKL thread configuration for containerized deployments.

* Recommend using Python 3.8 when running on RHEL 8, shipped `Python 3.8 can add
  some performance improvement
  <https://developers.redhat.com/blog/2020/06/25/red-hat-enterprise-linux-8-2-brings-faster-python-3-8-run-speeds/>`_.

Triggering unit for a specific package
======================================

To help with scaling the recommendation engine when it comes to number of
pipeline units possibly registered, it is a good practice to state to which
package the given unit corresponds. To run the pipeline unit for a specific
package, this fact should be reflected in the pipeline unit configuration by
stating ``package_name`` configuration option. An example can be a pipeline
unit specific for TensorFlow packages, which should state ``package_name:
"tensorflow"`` in the pipeline configuration.

If the pipeline unit is generic for any package, the ``package_name``
configuration has to default to ``None``.

Justifications in the recommended software stacks
=================================================

Follow the :ref:`linked documentation for providing valuable information to
users on actions performed in pipeline units implemented <justifications>`.

An example implementation
=========================

.. code-block:: python

  from typing import Any
  from typing import Dict
  from typing import Generator
  from typing import TYPE_CHECKING

  from thoth.adviser.state import State
  from thoth.adviser.wrap import Wrap

  if TYPE_CHECKING:
      from ..pipeline_builder import PipelineBuilderContext


  class NoSemanticInterpositionWrap(Wrap):
      """A wrap that recommends to switch to Python 3.8 on RHEL 8.2."""

      CONFIGURATION_DEFAULT: Dict[str, Any] = {"package_name": None}  # The pipeline unit is not specific to any package.

      _JUSTIFICATION = [
        {
            "type": "INFO",
            "message": "Consider using UBI or RHEL 8.2 with Python 3.8 that has optimized Python interpreter with "
            "performance gain up to 30%",
        }
    ]

      @classmethod
      def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any]]:
          """Include this wrap in adviser for RHEL/UBI 8.2."""
          if builder_context.is_included(cls):
              yield from ()
              return None

          if not builder_context.is_adviser_pipeline():
              yield from ()
              return None

          if (
              builder_context.project.runtime_environment.operating_system.name in ("rhel", "ubi")
              and builder_context.project.runtime_environment.operating_system.version == "8.2"
              and builder_context.project.runtime_environment.python_version != "3.8"
          ):
              yield {}
              return None

          yield from ()
          return None

      def run(self, state: State) -> None:
          """Recommend using Python3.8 on RHEL/UBI 8.2."""
          state.add_justification(self._JUSTIFICATION)

The implementation can also provide other methods, such as :func:`Unit.pre_run
<thoth.adviser.unit.Unit.post_run>`, :func:`Unit.post_run
<thoth.adviser.unit.Unit.post_run>` or :func:`Unit.post_run_report
<thoth.adviser.unit.Unit.post_run>` and pipeline unit configuration adjustment.
See :ref:`unit documentation <unit>` for more info.
