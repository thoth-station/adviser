.. _unit:

A pipeline unit
---------------

All units are derived from :class:`Unit <thoth.adviser.unit.Unit>` that
provides a common base for implemented units of any type. The base class also
provides access to the input pipeline vectors and other properties that are
accessible by :class:`context abstraction <thoth.adviser.context.Context>`. See
:ref:`pipeline section <pipeline>` as a prerequisite for pipeline unit
documentation.

Note the instantiation of units is done once during pipeline creation - units
are kept instantiated once during stack generation pipeline run.

Registering a pipeline unit to pipeline
=======================================

If the pipeline configuration is not explicitly supplied, Thoth's adviser
dynamically creates pipeline configuration. This creation is done in a loop
where each pipeline unit class of a type (:ref:`boot <boots>`, :ref:`sieve
<sieves>`, :ref:`step <steps>`, :ref:`stride <strides>` and :ref:`wrap
<wraps>`) is asked for inclusion into the pipeline configuration - each
pipeline unit implementation is responsible for providing logic that states
when the given pipeline unit should be registered into the pipeline.

This logic is implemented as part of :func:`Unit.should_include
<thoth.adviser.unit.Unit.should_include>` class method:

.. code-block:: python

    from typing import Any
    from typing import Dict
    from typing import Optional

    from thoth.adviser import PipelineBuilderContext

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Optional[Dict[str, Any]]:
        """Check if the given pipeline unit should be included into pipeline."""
        if builder_context.is_adviser_pipeline() and not builder_context.is_included(cls):
            return {"configuration1": 0.33}

        return None

The :func:`Unit.should_include <thoth.adviser.unit.Unit.should_include>` class
method returns a value of ``None`` if the pipeline unit should not be
registered into the pipeline configuration or a dictionary stating pipeline
configuration that should be applied to pipeline unit instance (an empty
dictionary if no configuration changes are applied to the default pipeline
configuration but the pipeline unit should be included in the pipeline
configuration).

The pipeline configuration creation is done in multiple rounds so
:class:`PipelineBuilderContext
<thoth.adviser.pipeline_builder.PipelineBuilderContext>`, besides other
properties and routines, also provides
:func:`PipelineBuilderContext.is_included
<thoth.adviser.pipeline_builder.PipelineBuilderContext.is_included>` method
that checks if the given unit type is already present in the pipeline
configuration. As you can see, pipeline unit can become part of the pipeline
configuration multiple times based on requirements. See
:class:`PipelineBuilderContext
<thoth.adviser.pipeline_builder.PipelineBuilderContext>` for more information.

Unit configuration
==================

Each unit can have instance specific configuration. The default configuration
can be supplied using :py:attr:`Unit.CONFIGURATION_DEFAULT
<thoth.adviser.unit.Unit.CONFIGURATION_DEFAULT>` class property in the derived
pipeline configuration type. Optionally, a schema of configuration can be
defined by providing :py:attr:`Unit.CONFIGURATION_DEFAULT
<thoth.adviser.unit.Unit.CONFIGURATION_SCHEMA>` in the derived pipeline
configuration type - this schema is used to verify unit configuration
correctness on unit instantiation.

Pipeline unit configuration is then accessible via :func:`Unit.configuration
<thoth.adviser.unit.Unit.configuration>` property on a unit instance which
returns a dictionary with configuration - the default one updated with the one
returned by :func:`Unit.should_include
<thoth.adviser.unit.Unit.should_include>` class method.

Additional pipeline unit methods
================================

All pipeline unit types can implement the following methods that are triggered
in the described events:

* :func:`Unit.post_run <thoth.adviser.unit.Unit.post_run>` - called before running any pipeline unit with context already assigned
* :func:`Unit.post_run <thoth.adviser.unit.Unit.post_run>` - called after the resolution is finished
* :func:`Unit.post_run <thoth.adviser.unit.Unit.post_run>` - post-run method run after the resolving has finished - this method is called only if resolving with a report

Afterword for pipeline units
============================

All units can raise :class:`thoth.adviser.exceptions.EagerStopPipeline` to
immediately terminate resolving and causing the resolver to report back all the
products computed so far.

Pipeline units of type :class:`Sieve <thoth.adviser.sieve.Sieve>` and
:class:`Step <thoth.adviser.step.Step>` can also raise :class:`NotAcceptable
<thoth.adviser.exceptions.NotAcceptable>`, see :ref:`sieves <sieves>` and
:ref:`steps <steps>` sections for more info.

Raising any other exception in pipeline units causes resolver failure.

All pipeline units should be atomic pieces and `they should do one thing and do
it well <https://en.wikipedia.org/wiki/Unix_philosophy>`_. They were designed
to be small pieces forming complex resolution system.
