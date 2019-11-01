.. _resolver:

Thoth's offline resolver
------------------------

As Python is a dynamic programming language, the actual resolution of Python
software stacks might take a time (you've probably `encountered this already
<https://github.com/pypa/pipenv/issues/2873>`_). One of the reasons behind it
is the fact that all packages need to be downloaded and installed to verify
version range satisfaction during the installation. This is also one of the
reasons Thoth builds its knowledge base - Thoth pre-computes dependencies
in the Python ecosystem so that resolving can be done offline without
interacting with outside world.


A note to Thoth's Python resolver
=================================

Thoth stores pre-computed dependency graph in its knowledge base. Besides
the graph structure kept, it also evaluates
`environment markers <https://www.python.org/dev/peps/pep-0496/>`_ in the
solver runs (hence solvers are based on software environments which are used
from configuration entries and can be recommended as well)

Software stacks returned by Thoth are fully compliant with Python's packaging
resolution algorithm as done by pip or Pipenv except for environment markers.
If software environment in which the application runs is fully specified, Thoth
can use pre-computed results of environment markers and the recommended
software stack does not include sub-graphs which would normally be reported by
pip/Pipenv when done a generic resolution (e.g. `enum34
<https://pypi.org/project/enum34/>`_ is often included with environment marker
``python_version<"3.4"``. If Thoth is resolving software stacks for Python 3.6,
it already knows enum34 will not be installed so any of its dependencies, if
any, will not be installed as well). This helps to narrow down to software that
is really used in the deployed environment.

Environment markers applied on direct dependencies are not evaluated during
resolution.

