.. _security_advises:

Thoth Security Advises
======================

Thoth allows users to request security advises. When a security based advise is
requested the pipeline unit :class:`SecurityIndicatorsStep
<thoth.adviser.steps.security_indicators.SecurityIndicatorStep>` is included
and changes the behaviour of the :class:`CvePenalizationStep
<thoth.adviser.steps.cve.CvePenalizationStep>`. The
:class:`SecurityIndicatorsStep
<thoth.adviser.steps.security_indicators.SecurityIndicatorStep>` aggregates
information from ``si-cloc`` and ``si-bandit`` which wrap ``cloc`` and
``bandit`` to work on specific python package versions to be easily stored in
our DB. The CVE penalization step, instead of penalizing a package version for
having a known CVE it will completely remove it from resolution.

This is a living document and as other methods of judging a packages security
are added to Thoth this document will be update to reflect these new ways of
scoring.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/mes9sDMPr28" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

CVE
###

Thoth uses vulnerability database published by the Python packaging association
(PyPA) - see pypa/advisory-db [#advisory-db]_. This database keeps track of
known vulnerabilities in Python packages.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/R2i2lF4Ll4g" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

Bandit
######

Bandit [#bandit]_ is a project created by the PyCQA — Python Code Quality
Authority — which transforms Python code into an abstract syntax tree (AST) and
runs static code quality checks looking for common security issues in Python.
Bandit classifies the issues by severity and confidence.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/GypRonz01Hg" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

cloc
####

``cloc`` [#cloc]_ is a command line tool that counts lines of code. This is used
as a normalizer for security score. Having a single high-severity,
high-confidence issue in a small Python project is much more concerning than if
a single high-severity, high-confidence issue is found in a large project.

Security Scorecards for Open Source Projects
############################################

`Open Source Security Foundation <https://openssf.org/>`__ provides `Security Scorecards
for open-source projects <https://openssf.org/blog/2020/11/06/security-scorecards-for-open-source-projects/>`__.
Thoth uses scorecards in recommendations to provide additional knowledge about Python packages to users.
If you are interested, follow `scorecards checks available
<https://github.com/ossf/scorecard/blob/main/docs/checks.md>`__.

Security Scorecards used in Thoth are available
`in thoth-station/prescriptions repository <https://github.com/thoth-station/prescriptions/>`__.

Using security advises in OpenShift S2I
#######################################

Thoth's integration in OpenShift S2I can block building Python applications
that are potentially vulnerable. By adjusting ``recommendation_type`` to
``security``, the build process fails if any package is considered
vulnerable.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/bOUEEh3u0Ug" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

.. [#advisory-db] https://github.com/pypa/advisory-db
.. [#bandit] https://bandit.readthedocs.io/en/latest/
.. [#cloc] http://cloc.sourceforge.net/
