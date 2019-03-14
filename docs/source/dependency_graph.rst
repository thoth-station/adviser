.. _dependency_graph:

Dependency Graph
----------------

Adviser's implementation uses internal structure called "Dependency Graph" for
generating possible software stacks. This generation is done for:
1. Computing recommendations by scoring computed software stacks - the stack with the highest score is the best possible software stack for an application.
2. Generating samples of software stacks for Dependency Monkey - these stacks are validated and scored (e.g. performance index) in the `Amun <https://github.com/thoth-station/amun-api>`_ service.

The dependency graph is implemented as an N-ary graph. You can imagine the
graph as a generic binary tree, except:
1. Each node is constructed of N pakages in some specific versions (not binary nodes, but N-ary nodes).
2. There can be cycles (thus graph and not a tree).

The resolution itself can be done using two sources (see CLI help for configuration info):
1. The graph database used in the Thoth project - this database states relevant packages in the Python ecosystem with relations between them (what dependency in what version is required with previously resolved versions using `solver <https://github.com/thoth-station/solver>`_).
2. `PyPI <https://pypi.org>`_ (or any Python Warehouse instance) - the resolution is done against the "upstream" (ecosystem as a whole) so one can resolve any dependencies in the PyPI ecosystem and compute possible software stacks.

The advantage of using Thoth's database is the fact that this database states
observations about packages and software stacks so that the database itself can
help with better resolution mechanism (the latet is not always the best
choice). In this case the graph database is also helping with offline
resolution (Python is a dynamic programming language, what dependencies will be
installed can be determined during installation - e.g. based on operating
system).


Development of Dependency Graph
###############################

If you are a developer and would like to speed up your work, dependency graph
has a capability to be pickled onto disk and loaded back into memory on demand.
To control this behavior you can use ``THOTH_ADVISER_FILEDUMP`` environment
variable stating file into which the constructed graph should be deserialized
(in case of this file does not exist) or loaded into back into memory (if file
exists). Besides that, you can also supply environment variable
``THOTH_ADVISER_NO_DIGESTS`` set to ``1`` if you do not care about package
hashes in resulting Pipfile.lock files.
