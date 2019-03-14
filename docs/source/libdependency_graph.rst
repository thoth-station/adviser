.. _libdependency_graph:

Resolver design document
------------------------

This document describes the current and past implementations of Thoth’s
software stack resolution algorithm which is implemented on top of JanusGraph
database. The main reason for creating this resolution algorithm are two
fundamental requirements from Thoth side:

* Provide a fast mechanism on how to generate software stacks for scoring (recommendations)
* Provide a fast mechanism on how to generate software stacks which should be used in Thoth’s Amun service (service for software stack validation and scoring)

Queries to the graph database
=============================

Packages and their dependencies were obtained from the graph database
(JanusGraph). A query to JanusGraph database for transitive dependencies
retrieves a path to each package starting from each direct dependency. Given
the following dependencies (where A, B, C, D, E, F, G are packages in specific
versions):

* A depends on B
* A depends on C
* B depends on D
* D depends on E
* C depends on F
* B depends on G

The graph database query for retrieving transitive dependencies for direct
dependency A returns a list of lists stating which package depends on which
(until the end of dependency chaining is hit):


.. code-block:: console

  [
    [A, B, D, E],
    [A, B, G],
    [A, C, F]
  ]

The cyclic dependencies are handled in the query (the last item in the chain
references back the item which started the cycle).

The actual query implemented in Thoth does not return values of packages. Based
on our performance observations, due to serialization, deserialization and
JanusGraph server-side cache, it is much more efficient to retrieve identifiers
of these packages and ask for the actual package name, package version and
source index URL later on in parallel for each item in the dependency chain
(note that packages in the resulting query occur multiple times based on
packages which introduced them).

We are now primarily focused on Python ecosystem, we use pip’s internal
resolution algorithm to resolve dependencies. JanusGraph allows to submit code
which should be executed during the traversal in JanusGraph, but this code has
to be JVM compatible (e.g. Java, Groovy scripts) - because of this reason we
cannot directly submit pip’s internal resolution algorithm written in Python.
Moreover, we are interested in resolved stacks, which require maintaining a
context used during the actual graph traversal.  Python Implementation The very
first implementation is written in Python and can be found in the Thoth’s
adviser repository.

The key idea is in creation in-memory N-ary graph constructed based on queries
to JanusGraph. This graph is subsequently traversed and the result of each full
traversal yields a fully pinned down stack.

.. image:: _static/dependency_graph.png
   :target: _static/dependency_graph.png
   :alt: DependencyGraph

By traversing the graph and reaching the leaf nodes, we generate software
stacks. Example stacks generated during the traversal:


* A1, C1, B1, D1
* A1, C2, B2, D2

The main downside for the Python implementation were memory consumption and
time spent in traversals to generate stacks. These issues were targeted in the
new C++ implementation which is described in the following paragraph.

C/C++ Implementation
====================

The next implementation was done in C/C++ and exposes its functionality as as a
library which is loaded from the Python code. The Python code uses C bindings
available via ctypes to communicate with the C implementation (see the Python
adapter for the created so library). The exposed C API than talks to the
underlying C++ implementation.

The stack generation is done in a standalone process which writes results into
a pipe. The pipe is used as inter-process communication - the Python process
reads stacks as produced by the C/C++ library into a pipe, scores them and
constructs the resulting adviser report with the recommended scores,
justification and additional metadata.

The use of pipe was chosen as to advantage with easy inter-process
communication. The C/C++ implementation operates on top of numbers which
represent packages in specific versions, mapping of packages to a specific type
(substituted with a number) and a list capturing structure between packages.
These numbers are easy to serialize and deserialize when the IPC via pipe is
done. Moreover, it makes the C/C++ implementation reusable (not tightly bound
to a Python resolving, but in any N-ary graph traversal we will need later).

One of the benefits of using a separate process are also the OOM issues. If the
stack producer goes out of memory, it gets killed (in the OpenShift) and the
main scoring process can report partial results to users.

Let’s suppose we have the same packages as described in the Python
implementation above. The C++ implementation does not create immediately the
whole dependency graph in memory to perform traversals, but rather expands
traversed nodes of transitive dependencies when needed. Moreover, using raw
numbers which map to packages and package types makes the implementation more
memory efficient.

A mapping is performed in the following manner:


* Each package is mapped to a number
* Each package of a same type has assigned same “type” number
* Paths as returned from the graph database are turned into a list of pairs where each pair states a package on the first position and its dependency on the second position

An example can be the dependency graph from the previous section:

.. image:: _static/dependency_graph.png
   :target: _static/dependency_graph.png
   :alt: DependencyGraph

Here, there are grouped same packages (same package names, but different
package versions and/or package source indexes) of type “a” (this can be for
example package “numpy” in version 1, 2 and 3) into one node of N-ary graph. In
the C/C++ implementation these packages have assigned the same type identifier
(for example 0) which groups them into the same package type category. With the
same pattern, there are grouped packages of type “b” (versions 1, 2) into the
same category identified by a number (for example 1) and so on. This mapping is
called “dependency_types” in the C/C++ implementation. An example mapping for
each package can be:

A1: 0; A2: 0; A3: 0;
B1: 1; B2: 1;
C1: 2; C2: 2; C3: 2;
D1: 3; D2: 3;

Another mapping used in the C/C++ implementation is mapping of packages in
specific version from a specific Python source index (this triplett uniquely
distinguishes packages in the Python ecosystem). For the example above, the
mapping can be:

A1: 0; A2: 1; A3: 2;
B1: 3; B2: 4;
C1: 5; C2: 6;
D1: 7; D2: 8;

The last parameter to the C/C++ implementation (omitting medata information
such as sizes of arrays submitted to C/C++ implementation) is a list of number
pairs. The first pair states a package and the second pair states its
dependency. Basically this array represents serialized paths as returned from
the graph traversal query. An example can be:

[  [0; 5]; [0; 6]; [1; 5]; [1; 6]; [1; 2], … ]

In this case, the first item in the array [0; 5] represents the fact A1 depends
on C1, [1; 6] represents dependency between A2 and C2 and so on.

These parameters are then used to construct the dependency graph as shown above
dynamically during traversal as well as to perform resolution checks (such as
no two packages of a same type can be installed at the same type - e.g. C1 and
C2).

Library implementation
======================

The library is present in the
``thoth/adviser/python/bin`` directory. You can find all the relevant files
(``Makefile``, ``Dockerfile``) to build this library. The repository is by
default shipped with an ``*.so`` file (the file produced by ``Makefile``) and
subsequently loaded by the adviser implementation using Python's ctypes. This
library is executed as a standalone process which writes stacks into a pipe
from which they are consumed in the main adviser's Python process and
scored/submitted to Amun for inspections.

To build this library on your own, you can use ``make``:

::

   make

Also make sure the C++ STL ABI is compatible when you are deploying adviser,
otherwise you can encounter issues like the following:

::

  OSError: /lib64/libstdc++.so.6: version `CXXABI_1.3.8' not found (required by /opt/app-root/src/thoth/adviser/python/bin/libdependency_graph.so)

To target this issue, there was created a containerized build, which can be
done using:

::

  make container-build

This build will produce the ``libdependency_graph.so`` file in a container (use
base image you would like to be compatible with) and copied to host for use.

