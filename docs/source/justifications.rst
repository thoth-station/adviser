.. _justifications:

Justifications by the recommendation engine
-------------------------------------------

When the recommendation engine produces advises, it also provides comments on
why the given recommendation was produced. These snippets are called
"justifications" and are a textual form to justify actions taken by the
recommendation engine.

Some of the justifications that can be produced by the recommendation
engine are available at `thoth-station.ninja/justifications
<https://thoth-station.ninja/justifications>`__. These are documents linked
from the :ref:`pipeline units <units>` present in the :ref:`pipeline
configuration <pipeline>` during the software stack resolution. Some of the
justifications can be produced directly by the :ref:`resolver <resolver>` or
:ref:`predictor <predictor>`.

Creating justification documents
================================

If you wish to create a justification, follow already existing template
available in `thoth-station.github.io repo
<https://github.com/thoth-station/thoth-station.github.io/blob/master/_j/_example.md>`__
and fill in missing parts.

Name the file name in a SEO friendly way and keep it short so that the URL
generated is as short as possible.

.. _jl:

Linking justification documents from adviser
============================================

To create a justification, you can use ``get_justification_link`` from
``thoth-common`` module. A common idiom is:

.. code-block:: python

  from thoth.common import get_justification_link as jl

  link = jl("my_justification")

The ``my_justification`` part directly corresponds to the name of the Markdown
file with justification as placed in the ``_j/`` directory (without
the ``.md`` suffix). The linked justification will be named
``my_justification.md`` and will be placed in `thoth-station.github.io/_j
<https://github.com/thoth-station/thoth-station.github.io/tree/master/_j>`__.
The justification document is automatically built on push to master and the
justification is automatically available in the justification listing.


.. _justification:

Adding justifications to the recommended software
=================================================

There are two possibilities how to provide justifications to the users. In both
cases, justifications should follow pre-defined schema already defined in
Thoth's adviser test-suite (see ``AdviserTestCase._JUSTIFICATION_SCHEMA`` in
``tests/base.py``).

.. _stack_info:

Justifications for recommended software stack
#############################################

The very first use of justification schema uses :ref:`step pipeline units
<steps>`. These units can return justification as part of their results and are
specific to the software stack resolved.

.. code-block:: python

    import logging

    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Tuple
    from typing import TYPE_CHECKING

    import attr
    from thoth.common import get_justification_link as jl
    from thoth.python import PackageVersion
    from thoth.storages.exceptions import NotFoundError
    from voluptuous import Required
    from voluptuous import Schema

    from thoth.adviser.step import Step
    from thoth.adviser.state import State

    _LOGGER = logging.getLogger(__name__)


    @attr.s(slots=True)
    class CvePenalizationStep(Step):
        """Penalization based on CVE being present in stack."""

        CONFIGURATION_DEFAULT = {"package_name": None, "cve_penalization": -0.2}
        CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): None, Required("cve_penalization"): float})
        _JUSTIFICATION_LINK = jl("cve")

        # ...

        def run(self, _: State, package_version: PackageVersion) -> Optional[Tuple[float, List[Dict[str, str]]]]:
            """Penalize stacks with a CVE."""
            try:
                cve_records = self.context.graph.get_python_cve_records_all(
                    package_name=package_version.name, package_version=package_version.locked_version,
                )
            except NotFoundError as exc:
                _LOGGER.warning("Package %r in version %r not found: %r", str(exc))
                return None

            if cve_records:
                return self.configuration["cve_penalization"], [{
                    "package_name": package_version.name,
                    "link": self._JUSTIFICATION_LINK,
                    "message": "Found at least one vulnerability for the given package:"
                }]

            return None

The value returned corresponds to a list of justifications that should be
reported when a software stack is resolved from the ``state`` taking the step
described in the pipeline unit (an action taken from a state to another state
as seen in :ref:`Markov Decision Process <introduction>`). Follow :ref:`steps
documentation <steps>` for more info.

Justifications on stack level
#############################

There is also a possibility to provide justifications on the stack level. These
justifications will always show up to the user with the recommended software
stack and are on the "stack level". An example of such justifications can be an
informative message about the direct dependencies used, software environment
used or hardware environment used - all these are not thought to the
recommended set of Python packages.

To do so, any pipeline unit can add justifications to the context before,
during or after the resolution process is done:


.. code-block:: python

  import logging
  import attr

  from thoth.adviser.boot import Boot
  from thoth.common import get_justification_link as jl

  _LOGGER = logging.getLogger(__name__)


  @attr.s(slots=True)
  class UbiBoot(Boot):
      """Remap UBI to RHEL.

      As UBI has ABI compatibility with RHEL, remap any UBI to RHEL.
      """

      _MESSAGE = "Using observations for RHEL instead of UBI, RHEL is ABI compatible with UBI"
      _JUSTIFICATION_LINK = jl("rhel_ubi")

      # ...

      def run(self) -> None:
          """Remap UBI to RHEL as Thoth keeps track of RHEL and UBI is ABI compatible."""
          if self.context.project.runtime_environment.operating_system.name == "ubi":
              _LOGGER.info("%s - see %s", self._MESSAGE, self._JUSTIFICATION_LINK)

              # >>> Add justification to the stack info
              self.context.stack_info.append(
                  {"type": "WARNING", "message": self._MESSAGE, "link": self._JUSTIFICATION_LINK}
              )
              # <<< Add justification to the stack info

              self.context.project.runtime_environment.operating_system.name = "rhel"
