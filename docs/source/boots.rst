.. _boots:

Boot pipeline unit type
-----------------------

A very first :ref:`pipeline unit <unit>` is called ":class:`boot
<thoth.adviser.boot.Boot>`" as it is started as a first pipeline unit. It's
main purpose is to check input, adjust input parameters, halt adviser in case
of any undesired conditions or to print any messages to logger (that will show
up in user logs).  As in case of all units, it has access to adviser context to
check any input values to the adviser (user input, parameters or
hyperparameters).

.. note::

  Each boot pipeline unit is called just once per resolution before the
  stack generation pipeline is started.

Main usage
==========

* Adjust input parameters to the resolution process.

* Halt adviser before any stack resolution is done based on input values

  * Any exception raised will halt adviser with an error message (created out
    of exception message) populated to the adviser JSON result except for
    eager stopping (see bellow)

* Print information into logs using ``logging``

  * Any information logged will show up in adviser run logs - logging respects
    log-level configuration which was set up during adviser startup based on
    request/adviser configuration

* Prematurely end resolution based on the the final state reached

  * Raising exception :class:`EagerStopPipeline
    <thoth.adviser.exceptions.EagerStopPipeline>` will cause stopping the whole
    resolver run

Real world examples
===================

* Any adjustments to input parameters done can result in a logged messages

  * If a user uses a Python package index in the ``Pipfile`` that was not
    enabled by Thoth administrator a boot unit can adjust ``Pipfile`` (e.g.
    remove Python package index) - this configuration change will be propagated
    Thoth's response in all integrations

  * If a user uses hardware (CPU/GPU) that is not known to Thoth's knowledge
    base, a boot unit can adjust this information (remove it completelly or,
    for example, find a similar GPU model for recommendations) and print an
    informative log message

* Gate an application build in the cluster based on configured Python package
  indexes

  * If a user uses a Python package index that was not enabled by Thoth
    administrator in the ``Pipfile`` a boot unit can raise an exception causing
    a halt

* Halting adviser in case of not sufficient runtime or buildtime information

  * If a user uses hardware (CPU/GPU) that is not known to Thoth's knowledge
    base, a boot unit can halt adviser

An example implementation
=========================

.. code-block:: python

  import logging

  from thoth.adviser import Boot


  _LOGGER = logging.getLogger(__name__)

  class ExampleBoot(Boot):
      """This is an example boot implementation."""

    def run(self) -> None:
        """Main entry-point for boot unit to demonstrate boot example."""
        cpu_family = self.context.project.runtime_environment.hardware.cpu_family

        if cpu_family is not None
            known_cpu_families = self.context.graph.get_cpu_family_all()
            if cpu_family not in known_cpu_families:
                _LOGGER.warning(
                    "CPU family used %s is not known, it will not be considered"
                    cpu_family
                )
                self.context.project.runtime_environment.hardware.cpu_family = None
                # Or you can raise an exception causing adviser halt:
                #  raise ValueError(f"CPU family used {cpu_family!r} is not known")


The implementation can also provide other methods, such as :func:`Unit.pre_run
<thoth.adviser.unit.Unit.post_run>`, :func:`Unit.post_run
<thoth.adviser.unit.Unit.post_run>` or :func:`Unit.post_run_report
<thoth.adviser.unit.Unit.post_run>` and pipeline unit configuration adjustment.
See :ref:`unit documentation <unit>` for more info.
