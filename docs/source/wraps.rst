.. _wraps:

Wrap pipeline unit type
-----------------------

The last pipeline unit type is named ":class:`wrap <thoth.adviser.wrap.Wrap>`".
This pipeline unit is called after a final state is accepted by :ref:`strides
<strides>`.

This pipeline unit was introduce for a sake of completeness. One of the
possible use cases is registering a callback during Thoth's adviser runs made
for experiments (for example `Thoth Jupyter Notebook experiments
<https://github.com/thoth-station/notebooks>`_) to let user hook in an action
once a software stack is resolved (but the software stack resolution pipeline
is still running).

.. note::

  Raising any exception in a wrap causes the pipeline resolution to halt, with
  a corresponding failure that reports the exception message.

The implementation can also provide other methods, such as :func:`Unit.pre_run
<thoth.adviser.unit.Unit.post_run>`, :func:`Unit.post_run
<thoth.adviser.unit.Unit.post_run>` or :func:`Unit.post_run_report
<thoth.adviser.unit.Unit.post_run>` and pipeline unit configuration adjustment.
See :ref:`unit documentation <unit>` for more info.
