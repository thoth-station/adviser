.. _manifest_changes:

Advised manifest changes
------------------------

Any pipeline unit type can also generate manifest changes that should be
applied to make sure the application works properly. An example of a manifest
change could be an environment variable that should be supplied to the
application on deployment.

Each resolver state provides ``advised_manifest_changes`` attribute that can be
adjusted. Usually, this is done in a :ref:`Wrap pipeline unit type <wraps>` to
make sure the resolved application has correct environment setup to build the
application and run it.

An example of a wrap pipeline unit that suggests a manifest change - add
environment variable ``OMP_NUM_THREADS`` if ``intel-tensorflow`` is resolved to
the deployment config.

.. code-block:: python

  from typing import TYPE_CHECKING
  from typing import Optional, Dict, Any

  from ...state import State
  from ...wrap import Wrap

  if TYPE_CHECKING:
      from ..pipeline_builder import PipelineBuilderContext

  class ExampleWrap(Wrap):

      CONFIGURATION_DEFAULT = {"package_name": "intel-tensorflow"}  # call this wrap for intel-tensorflow

      _ADVISED_MANIFEST_CHANGES = [
          {
              "apiVersion": "apps.openshift.io/v1",
              "kind": "DeploymentConfig",
              "patch": {
                  "op": "add",
                  "path": "/spec/template/spec/containers/0/env/0",
                  "value": {"name": "OMP_NUM_THREADS", "value": "1"},
              },
          }
      ]

      @classmethod
      def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[Any, Any]]:
          """Include this pipeline unit only if it hasn't been included."""
          if builder_context.is_included(cls):
             return None

          return {}

      def run(self, state: State) -> None:
          """Advise manifest changes for intel-tensorflow."""
          state.advised_manifest_changes.append(self._ADVISED_MANIFEST_CHANGES)

The ``advised_manifest_changes`` attribute holds a list of changes that should
be applied. Each change is a list of JSON Patch objects - each item in the JSON
Patch object is evaluated until it succeeds. See `RFC-6902 for more info
<https://tools.ietf.org/html/rfc6902>`__.
