Thoth-Station
-------------

.. raw:: html

  <p style="text-align:right;"><i>Resurrected ancient deities helping humans with software development.</i></p>

.. image:: https://thoth-station.ninja/images/thoth-station.png
   :alt: Thoth Station logo
   :align: center
   :width: 70%

.. note::

  🧭 **Quick navigation**

  *I want to …*

  🐍 :ref:`start using Thoth <integration>`

  🦉 :ref:`add wisdom to the recommendation engine using prescriptions <prescription>`

  🤝 :ref:`get in touch <landing_page>`

  📊 `experiment with datasets available <https://github.com/thoth-station/datasets/>`__

  🐛 `report a bug or service issues <https://github.com/thoth-station/support/issues/new/choose>`__

Introductory sections
=====================

.. toctree::
   :maxdepth: 1

   introduction
   integration
   compatibility
   experimental_features
   landing_page
   developers_guide
   architecture
   deployment


Resolver and stack resolution pipeline
======================================

.. toctree::
   :maxdepth: 1

   pipeline
   resolver
   predictor
   justifications
   security
   manifest_changes


Pipeline units
==============

.. toctree::
   :maxdepth: 1

   unit

Pipeline unit types
###################

.. toctree::
   :maxdepth: 1

   boots
   pseudonyms
   sieves
   steps
   strides
   wraps

Prescriptions
#############

.. toctree::
   :maxdepth: 1

   Introduction to prescriptions <prescription>
   prescription/should_include
   prescription/boots
   prescription/pseudonyms
   prescription/sieves
   prescription/steps
   prescription/strides
   prescription/wraps


Predictors
==========

.. toctree::
   :maxdepth: 1

   Random state space sampling <predictors/sampling>
   Random walk in dependency graph <predictors/random_walk>
   Approximating latest <predictors/latest>
   Hill climbing <predictors/hill_climbing>
   predictors/annealing
   predictors/reinforcement_learning
   Monte Carlo Tree Search <predictors/mcts>
   Temporal Difference Learning <predictors/temporal_difference_learning>
   predictors/neural_network
   predictors/package_combinations


Other functionality provided by thoth-adviser implementation
============================================================

.. toctree::
   :maxdepth: 1

   dependency_monkey
   provenance_checks
   performance


Crossroad
=========

* `Documentation for thamos <../thamos>`_
* `Documentation for thoth-analyzer <../analyzer>`_
* `Documentation for thoth-common <../common>`_
* `Documentation for thoth-lab <../lab>`_
* `Documentation for thoth-package-analyzer <../package-analyzer>`_
* `Documentation for thoth-package-extract <../package-extract>`_
* `Documentation for thoth-python <../python>`_
* `Documentation for thoth-solver <../solver>`_
* `Documentation for thoth-storages <../storages>`_
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :maxdepth: 3

   thoth.adviser


This documentation corresponds to implementation in version |version|,
documentation was generated on |today|.
