.. _security_advises:

Thoth Security Advises
======================

Thoth allows users to request security advises. When a security based advise is
requested the pipeline unit ``SecurityIndicatorsStep`` [#security_step] is
included and changes the behaviour of the ``CVEPenalizationStep``. The
``SecurityIndicatorsStep`` aggregates information from ``si-cloc`` and
``si-bandit`` which wrap ``cloc`` and ``bandit`` to work on specific python
package versions to be easily stored in our DB. The CVE penalization step,
instead of penalizing a package version for having a known CVE it will
completely remove it from resolution. [#cve_security]

This is a living document and as other methods of judging a packages security
are added to Thoth this document will be update to reflect these new ways of
scoring.

Bandit
======

Bandit [#bandit]_ is a project created by the PyCQA — Python Code Quality
Authority — which transforms Python code into an abstract syntax tree (AST) and
runs static code quality checks looking for common security issues in Python.
Bandit classifies the issues by severity and confidence.

cloc
====

``cloc`` [#cloc]_ is a command line tool that counts lines of code. This is used
as a normalizer for security score. Having a single high-severity,
high-confidence issue in a small Python project is much more concerning than if
a single high-severity, high-confidence issue is found in a large project.

.. [#bandit] https://bandit.readthedocs.io/en/latest/
.. [#cloc] http://cloc.sourceforge.net/
.. [#security_step] https://github.com/thoth-station/adviser/blob/master/thoth/adviser/steps/security_indicators.py
.. [#cve_security] https://github.com/thoth-station/adviser/blob/master/thoth/adviser/steps/cve.py#L99
