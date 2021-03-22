Welcome to Thoth's adviser documentation
----------------------------------------

Thoth's adviser is a recommendation engine for Python applications.

.. note::

  See ":ref:`Thoth's landing page <landing_page>`" to see generic info if you are new to Thoth.

Introductory sections
=====================

.. toctree::
   :maxdepth: 1

   introduction
   integration
   compatibility
   experimental_features
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
   manifest_changes


Pipeline units
==============

.. toctree::
   :maxdepth: 1

   unit
   boots
   pseudonyms
   sieves
   steps
   strides
   wraps
   prescription


Predictors
==========

.. toctree::
   :maxdepth: 1

   predictors/sampling
   predictors/random_walk
   predictors/latest
   predictors/hill_climbing
   predictors/annealing
   predictors/reinforcement_learning
   predictors/mcts
   predictors/temporal_difference_learning
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
