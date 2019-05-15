.. _dependency_graph:

Dependency Graph
----------------

Adviser's implementation uses an internal structure called "Dependency Graph" for
generating possible software stacks. This generation is done for:

#. Computing recommendations by scoring computed software stacks - the stack with the highest score is the best possible software stack considered for an application (Thoth's advises).

#. Generating samples of software stacks for :ref:`Dependency Monkey <dependency_monkey>` - these stacks are validated and scored (e.g. performance index) on the `Amun <https://github.com/thoth-station/amun-api>`_ service.

The dependency graph is implemented as an N-ary graph. You can imagine the
graph as a generic binary tree, except:

#. Each node is constructed of N packages in some specific versions (not binary nodes, but N-ary nodes).

#. There can be cycles (thus graph and not a tree).

The resolution itself can be done using two sources (see CLI help for configuration info):

#. The graph database used in the Thoth project - this database states relevant packages in the Python ecosystem with relations between them (what dependency in what version is required with previously resolved versions using `solver <https://github.com/thoth-station/solver>`_).

#. `PyPI <https://pypi.org>`_ (or any `PEP-503 compliant <https://www.python.org/dev/peps/pep-0503/>`_ instance) - the resolution is done against the "upstream" (ecosystem as a whole) so one can resolve any dependencies in the PyPI ecosystem and compute possible software stacks.

The advantage of using Thoth's database is the fact that this database states
observations about packages and software stacks so that the database itself can
help with better resolution mechanism (the latest is not always the best
choice). In this case, the graph database is also helping with offline
resolution (Python is a dynamic programming language, what dependencies will be
installed can be determined during installation - e.g. based on operating
system).


Development of Dependency Graph
###############################

If you are a developer and would like to speed up your work, dependency graph
has a capability to be pickled onto disk and loaded back into memory on demand.
To control this behavior you can use ``THOTH_ADVISER_FILEDUMP`` environment
variable stating file into which the constructed graph should be deserialized
(in case of this file does not exist) or loaded back into memory (if file
exists). Besides that, you can also supply environment variable
``THOTH_ADVISER_NO_DIGESTS`` set to ``1`` if you do not care about package
hashes in resulting ``Pipfile.lock`` files.
