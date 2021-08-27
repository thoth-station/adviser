.. _architecture:

Thoth's architecture
--------------------

In this section, the reader gets a notion about Thoth architecture, requirements
for deployment and main Thoth's components.

The whole deployment is divided into multiple namespaces (or OpenShift
projects):

* ``thoth-frontend``
* ``thoth-middletier``
* ``thoth-backend``
* ``thoth-graph``
* ``thoth-infra``
* ``amun-api`` (optional, used on Amun)
* ``amun-inspection`` (optional, used on Amun)

The main reason behind splitting the application into multiple namespaces are
workloads.  Thoth is running different type of one-time workloads based on a
trigger - for example a single ``adviser`` instance is created as per user
request. The workload is then scheduled into a separate namespace (backend, in
case of adviser) and the given namespace acts as a pool of resources that are
available to be used for workloads. Other namespaces, for example frontend, can
be still used to scale, build, re-deploy or manage components.

Thoth is deployed from `thoth-station/thoth-application repo
<https://github.com/thoth-station/thoth-application>`__ using `Argo CD
<https://argoproj.github.io/argo-cd/>`__. Deployment can also be accomplished
using using `kustomize <https://kustomize.io/>`__.

See `Requirements for AICoE-CI & Thoth deployment
<https://github.com/AICoE/aicoe-ci>`__
with more detailed information.

Infra Namespace
###############

This namespace is separated for "infrastructure" related bits.

**Components running in this namespace:**

* `metrics-exporter <https://github.com/thoth-station/metrics-exporter>`__ -
  exposing deployment and content related metrics

* `advise-reporter <https://github.com/thoth-station/advise-reporter>`__ -
  periodically calculating and reporting information about adviser runs

* `slo-reporter <https://github.com/thoth-station/slo-reporter>`__ - providing
  reports on Thoth Service Level Objectives (SLO) to stakeholders

* `investigator-consumer <https://github.com/thoth-station/investigator>`__ -
  Kafka based component that consumes messages produced by Thoth components and
  schedules Argo workflows

* `investigator-message-metrics
  <https://github.com/thoth-station/investigator>`__ - exposing calculated
  metrics from messages seen in the system

Frontend Namespace
##################

The ``thoth-frontend`` is used as a management namespace. Services running in
this namespace have usually assigned a service account for running and managing
pods that are available inside other namespaces.

A user can interact with the user-facing API that is the key interaction point
for users or bots. `The user-facing API
<https://github.com/thoth-station/user-api>`__ specifies its endpoints using
Swagger/OpenAPI specification. See `Thamos repo and documentation - a library
and CLI for interacting with Thoth <https://github.com/thoth-station/thamos>`_
and `the user API service repo <https://github.com/thoth-station/user-api>`_
itself for more info. You can also find more info in the :ref:`integration
<integration>` section.

**Components running in this namespace:**

* `graph-refresh-job <https://github.com/thoth-station/graph-refresh-job>`__ -
  a periodic job responsible for scheduling analyses of packages that were not yet
  analyzed

* `package-releases-job
  <https://github.com/thoth-station/package-releases-job>`__ - a periodic job
  responsible for tracking new releases on Python's package index (the public
  one is `PyPI.org <https://pypi.org>`_, see also `AICoE index
  <https://tensorflow.pypi.thoth-station.ninja/>`_)

* `cve-update-job <https://github.com/thoth-station/cve-update-job>`__ - a
  periodic job responsible for gathering CVE information about packages

* `package-update-job <https://github.com/thoth-station/package-update-job>`__
  - a periodic job responsible for checking the availability of packages along with their hashes from Python's package index.

* `cve-update-job <https://github.com/thoth-station/cve-update-job>`__ - a
  periodic job responsible for gathering CVE information about packages

* `pulp-pypi-sync-job
  <https://github.com/thoth-station/pulp-pypi-sync-job>`__ - a periodic
  job responsible for registering Python package indexes available on
  `pulp-python <https://docs.pulpproject.org/pulp_python/index.html>`__

Middletier Namespace
####################

The middletier namespace is used for analyzes and actual resource hungry tasks
that compute results for Thoth's knowledge graph. This namespace was separated
from the frontend namespace to guarantee application responsibility. All the
tasks that require computing results for the knowledge graph are scheduled in
this namespace. This namespace has an allocated pool of resources for such
un-predicable amount of computational pods needed for this purpose (e.g. pods
are not scheduled besides running user API possibly making user API
non-responsive).

**Components running in this namespace:**

* `package-extract <https://github.com/thoth-station/package-extract>`__ - an
  analyzer responsible for extracting packages from runtime/buildtime
  environments (container images)

* `solver <https://github.com/thoth-station/solver>`__ - an analyzer run to
  gather information about dependencies between packages (on which packages the
  given package depends on?, what versions satisfy version ranges?) and gathers
  observations such as whether the given package is installable into the given
  environment and if it is present on a Python package index

* `graph-sync-job <https://github.com/thoth-station/graph-sync-job>`__ - a job
  responsible for syncing data in a JSON format persisted on Ceph to the Thoth's
  knowledge graph database

* `prescriptions-refresh-job
  <https://github.com/thoth-station/prescriptions-refresh-job>`__ - a periodic
  job responsible for keeping `Thoth's prescriptions
  <https://github.com/thoth-station/prescriptions>`__ up to date

All the components are scheduled using `Argo workflows
<https://argoproj.github.io/argo-workflows/>`__. Additional logic used during
executing workflows is taken from `thoth-station/workflow-helpers repository
<https://github.com/thoth-station/workflow-helpers>`__.

Backend Namespace
#################

The backend part of application is used for executing code that, based on
gathered information from analyzers run in the middletier namespace, compute
results for actual Thoth users (bots or humans).

This namespace has, as in the case of middletier namespace, allocated pool of
resources. Each time a user requests a recommendation, pods are dynamically
created in this namespace to compute results.

**Components running in this namespace:**

* `adviser <https://github.com/thoth-station/adviser>`__ - a recommendation
  engine computing stack level recommendations for a user for the given runtime
  environment

* `provenance-checker <https://github.com/thoth-station/adviser>`__ - an
  analyzer that checks for provenance (origin) of packages so that a user uses
  correct packages from correct package sources (Python indexes); the
  implementation now lies in the `adviser repo
  <https://github.com/thoth-station/adviser>`__

* `graph-sync-job <https://github.com/thoth-station/graph-sync-job>`__ - a job
  responsible for syncing data in a JSON format persisted on Ceph to the Thoth's
  knowledge graph database

All the components are scheduled using `Argo workflows
<https://argoproj.github.io/argo-workflows/>`__. Additional logic used during
executing workflows is taken from `thoth-station/workflow-helpers repository
<https://github.com/thoth-station/workflow-helpers>`__.

Graph Namespace
###############

A separate namespace for database related deployments.

**Components running in this namespace:**

* Thoth's knowledge graph - a `PostgreSQL database <https://www.postgresql.org/>`_

* `pgbouncer <https://www.pgbouncer.org/>`__ - recycle and manage connections
  to the database; all the components talk to this component rather than
  directly to PostgreSQL

* `pgweb <https://sosedoff.github.io/pgweb/>`__ (optional) - interact with
  Thoth's knowledge graph via UI

* `postgresql-metrics-exporter
  <https://github.com/wrouesnel/postgres_exporter>`__ - PostgreSQL related
  metrics for the the database observability

* `graph-backup-job
  <https://github.com/thoth-station/graph-backup-job>`__ - a periodic job that
  creates database backups

* `graph-metrics-exporter
  <https://github.com/thoth-station/graph-metrics-exporter/>`__ - a periodic
  job that exports metrics out of the main database asynchronously

Grafana dashboards
##################

To guarantee application observability, there were created `Grafana
<https://grafana.com/>`__ dashboards available in
`thoth-station/thoth-application repository
<https://github.com/thoth-station/thoth-application/tree/master/grafana-dashboard>`__.

Argo Workflows and Kafka
########################

The whole Thoth deployment relies on `Argo Workflows <https://argoproj.github.io/>`__
and `Kafka <https://kafka.apache.org/>`__. `kafdrop
<https://github.com/obsidiandynamics/kafdrop>`__ can be used as a Kafka Web UI
(check `thoth-messaging repo <https://github.com/thoth-station/messaging/>`__)
and Argo Workflows provides `Argo UI <https://github.com/argoproj/argo-ui>`__
to check and visualize workflows.

Amun
====

See `Amun API for more info <https://github.com/thoth-station/amun-api>`__.
Amun also uses Kafka and Argo Workflows as listed above.

Amun API namespace
##################

* `Amun API <https://github.com/thoth-station/amun-api>`__ - API for the
  execution engine for inspecting quality, performance, and usability of
  software and software stacks in a cluster

Amun inspection namespace
#########################

* `inspection builds and jobs
  <https://github.com/thoth-station/thoth-application/tree/master/amun>`__ -
  created by Amun API and executed

* `dependency-monkey <https://github.com/thoth-station/dependency-monkey>`__ -
  an analyzer that dynamically constructs package stacks and submits them to
  `Amun <https://github.com/thoth-station/amun-api>`__ for dynamic application
  analysis

For more information, see `Amun API repository
<https://github.com/thoth-station/amun-api>`__ and autogenerated `Amun client
<https://github.com/thoth-station/amun-client>`_. See also `the performance
repo <https://github.com/thoth-station/performance>`__ for scripts used for
performance related inspections.
