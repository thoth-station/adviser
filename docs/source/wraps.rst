.. _wraps:

Wrap pipeline unit type
-----------------------

The last pipeline unit type is named ":class:`wrap <thoth.adviser.wrap.Wrap>`".
This pipeline unit is called after a final state is accepted by :ref:`strides
<strides>`.

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

An example implementation
=========================

.. code-block:: python

  from typing import Any
  from typing import Dict
  from typing import Optional
  from typing import TYPE_CHECKING

  from thoth.adviser.state import State
  from thoth.adviser.wrap import Wrap

  if TYPE_CHECKING:
      from ..pipeline_builder import PipelineBuilderContext


  class NoSemanticInterpositionWrap(Wrap):
      """A wrap that recommends to switch to Python 3.8 on RHEL 8.2."""

      _JUSTIFICATION = [
        {
            "type": "INFO",
            "message": "Consider using UBI or RHEL 8.2 with Python 3.8 that has optimized Python interpreter with "
            "performance gain up to 30%",
        }
    ]

      @classmethod
      def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
          """Include this wrap in adviser for RHEL/UBI 8.2."""
          if builder_context.is_included(cls):
              return None

          if not builder_context.is_adviser_pipeline():
              return None

          if (
              builder_context.project.runtime_environment.operating_system.name in ("rhel", "ubi")
              and builder_context.project.runtime_environment.operating_system.version == "8.2"
              and builder_context.project.runtime_environment.python_version != "3.8"
          ):
              return {}

          return None

      def run(self, state: State) -> None:
          """Recommend using Python3.8 on RHEL/UBI 8.2."""
          state.add_justification(self._JUSTIFICATION

The implementation can also provide other methods, such as :func:`Unit.pre_run
<thoth.adviser.unit.Unit.post_run>`, :func:`Unit.post_run
<thoth.adviser.unit.Unit.post_run>` or :func:`Unit.post_run_report
<thoth.adviser.unit.Unit.post_run>` and pipeline unit configuration adjustment.
See :ref:`unit documentation <unit>` for more info.
