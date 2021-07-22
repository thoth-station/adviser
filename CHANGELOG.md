
## Release 0.1.0 (2018-09-17T13:12:16)
* Initial dependency lock
* Add forgotten lxml library for bs4 parsing
* Provide JanusGraph configuration in provenance-checker template
* Provide JanusGraph configuration in adviser template
* Pass full path to Python3 in s2i
* Make CLI executable
* Install forgotten packages
* Add execute bit to app.sh
* State we want to run provenance rather than adviser in template
* Revert "Provide entrypoint for OpenShift s2i"
* Provide a script to run desired subcommand
* Provide entrypoint for OpenShift s2i
* Remove unused script as adviser is s2i now
* Remove Dockerfile as adviser is s2i now
* Let's reuse parameter names from adviser
* Use local tensorflow index page for gathering versions
* Fix warehouse test
* Some CI fixes
* Initial dependency lock
* Let Kebechet pin down deps
* Remove old TODO
* Implement sorting based on semver
* Create abstraction classes
* Initial python recommendation implementation
* Automatic update of dependency thoth-common from 0.2.6 to 0.2.7
* Automatic update of dependency thoth-common from 0.2.5 to 0.2.6
* Introduce provenance checker template
* Automatic update of dependency thoth-storages from 0.5.1 to 0.5.2
* Automatic update of dependency thoth-common from 0.2.4 to 0.2.5
* Automatic update of dependency thoth-common from 0.2.3 to 0.2.4
* change the queue
* Automatic update of dependency thoth-common from 0.2.2 to 0.2.3
* Automatic update of dependency thoth-storages from 0.5.0 to 0.5.1
* Automatic update of dependency thoth-storages from 0.4.0 to 0.5.0
* Automatic update of dependency thoth-storages from 0.3.0 to 0.4.0
* Automatic update of dependency thoth-storages from 0.2.0 to 0.3.0
* Automatic update of dependency thoth-storages from 0.1.1 to 0.2.0
* State all template parameters
* Be consistent with label naming
* Update requirements.txt respecting requirements in Pipfile
* Automatic update of dependency thoth-common from 0.2.1 to 0.2.2
* Automatic update of dependency thoth-storages from 0.1.0 to 0.1.1
* Add app=thoth label to pod template
* Adjust template labels
* Fix image stream kind in template
* Fix coala naming convention configuration
* Add OpenShift templates for deployment
* Automatic update of dependency thoth-storages from 0.0.33 to 0.1.0
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Initial dependency lock
* Delete Pipfile.lock for relocking dependencies
* relocked, travis removed, zuul added
* Automatic update of dependency thoth-common from 0.0.9 to 0.1.0
* Automatic update of dependency thoth-analyzer from 0.0.6 to 0.0.7
* Automatic update of dependency thoth-analyzer from 0.0.5 to 0.0.6
* Automatic update of dependency thoth-storages from 0.0.32 to 0.0.33
* Automatic update of dependency thoth-storages from 0.0.29 to 0.0.32
* Automatic update of dependency thoth-common from 0.0.6 to 0.0.9
* Update thoth packageswq
* Automatic update of dependency thoth-storages from 0.0.25 to 0.0.28
* Do not restrict Thoth packages
* Another CI fix
* Another CI fix
* Run coala in non-interactive mode
* CI fix
* Run coala in CI
* Create OWNERS
* Remove dependencies.yml
* Use coala for code checks
* Fix package name in license header
* Add LICENSE and license headers
* Use thoth's common logging
* Add README file

## Release 0.1.1 (2018-09-17T14:40:29)
* Setuptools find_packages does not respect namespaces

## Release 0.2.0 (2018-09-18T07:41:14)
* Introduce add_source and add_package methods

## Release 0.3.0 (2018-10-16T16:00:21)
* fixing coala
* typo :/
* using thoth zuul jobs now
* Adjust setup.py to run testsuite correctly
* Run testsuite using setup.py
* Output to JSON in adviser
* Link PackageVersion to Source index used
* Report dict reporesentation of input instead of raw strings
* Add missing parameters to template
* Fix labels section in template
* Dependency monkey is a template
* Move dependency monkey to a job template
* Rename adviser template to be more clear
* Move from Pods to Jobs
* Directly pass adviser subcommand that should be run
* Introduce Dependency Monkey template
* Update README file
* Fix link to Thamos
* Introduce method for converting model to object
* Possible different source is info
* Add Codacy badge
* Fix testsuite respecting last changes
* Link to Pipenv docs for specifying package indexes
* Fix console figure
* State configured index in the report message
* Adjust reported issue id for possible different source
* Add installation section and adjust based on review comments
* Document provenance checks
* Quote relevant parts of string
* Add the current PyPI index to default warehouses
* Make artifact names lowercase by deafult
* Finish provenance reports
* Report directly findings in the provenance check report
* Adviser report should be always an array
* Report back error if we cannot conclude on application stack
* Ignore s2i's virtualenv in which adviser is run
* Increase memory for adviser due to OOMs
* Do not use command in openshift template

## Release 0.4.0 (2019-05-08T23:28:27)
* Fix coala issues
* :pushpin: Automatic update of dependency pytest from 4.4.1 to 4.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.11.1 to 0.11.2
* Use new method to obtain even large stacks from graph database
* :pushpin: Automatic update of dependency mock from 3.0.4 to 3.0.5
* :pushpin: Automatic update of dependency mock from 3.0.3 to 3.0.4
* Add information about library usage to pipeline and OpenShift job
* Build-time error filtering should be a very first step
* Propagate information about project runtime when checking buildtime error
* Fix issue happening in semver sort after a package is removed
* Remove toolchain to always use latest toolchain release
* Fix empty paths if there is raised an exception about invalid pkg removal
* :pushpin: Automatic update of dependency thoth-storages from 0.11.0 to 0.11.1
* Log message was missleading if package_tuple gets overwritten
* Provide fast-path when checking for already removed packages
* :pushpin: Automatic update of dependency pytest-cov from 2.6.1 to 2.7.1
* Implement build-time error filtering step
* :pushpin: Automatic update of dependency mock from 3.0.2 to 3.0.3
* :pushpin: Automatic update of dependency mock from 2.0.0 to 3.0.2
* :pushpin: Automatic update of dependency thoth-storages from 0.10.0 to 0.11.0
* Adjust provenance-checker template to use Dgraph
* Adjust Dependency Monkey to use Dgraph
* Adjust adviser template to use Dgraph
* Report overall score of a stack
* Remove is_solvable flag as done in Dgraph implementation
* Added the method to read version from project to conf.py
* Remove JanusGraph specific bits
* Do not depend on specific graph adapter from specific module
* Remove JanusGraph specific bits
* :pushpin: Automatic update of dependency thoth-storages from 0.9.7 to 0.10.0
* Trigger dependency monkey reports sync into graph database
* :pushpin: Automatic update of dependency pytest from 4.4.0 to 4.4.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.4 to 0.8.5
* Automatic update of dependency thoth-common from 0.8.3 to 0.8.4
* Create a workaround for click argument parsing from env vars
* :sparkles: added the Registry to be used for image pulling to the templates
* Adviser implementation using stack generation pipeline
* Automatic update of dependency thoth-common from 0.8.2 to 0.8.3
* Make Isis a proper adapter
* Automatic update of dependency thoth-common from 0.8.1 to 0.8.2
* Automatic update of dependency pytest from 4.3.1 to 4.4.0
* :bug: put some sane default for IMAGE_STREAM_NAMESPACE into each template
* hot fixing the timeout
* :sparkles: ImageStream Tag and Namespace
* Automatic update of dependency flexmock from 0.10.3 to 0.10.4
* Report premature end of stack stream
* Improve handling of long-running advises
* Add timeout seconds for adviser to let it submit results
* Top score is now 100
* Automatic update of dependency thoth-storages from 0.9.6 to 0.9.7
* Automatic update of dependency thoth-python from 0.4.6 to 0.5.0
* Make reports more human readable
* Fix testsuite
* Add Thoth's configuration file
* Make Isis instance attribute
* Always kill stack producer if there is no consumer of stacks
* Fix Coala issues
* Do not score more than requested number of latest stacks
* Introduce stack producer timeout
* Use Sphinx for documentation
* Fix some test errors
* Minor improvements
* Introduce parameters for limiting number of versions
* Introduce limit parameter to limit number of packages of a same type
* Fix usage of package_t in libdependency_graph.so
* Use safe_load
* Fix coala complains
* Report any exception which occurred during dependency monkey run
* Introduce checks on configuration
* Make sure Isis is a singleton
* Minor fix in logged message
* Use Isis API from configmap
* Introduce performance based queries to Isis
* Make Coala happy again
* Use black for formatting
* Add missing file
* Make sure versions are sorted, add tests for adviser
* Use black for formatting tests
* Fix tests
* Log runtime environment when computing advises
* Address coala issues
* Add an optional graph database adapter to reduce number of connections
* Take into account packages that are not installable into the given env
* Update README, state local run in a container
* Report CVE count only if there were some found
* Remove unused env variables
* Provide Sentry and Prometheus configuration
* Add metadata information shown in result reports
* Update Pipfile.lock
* Register provenance-checker to graph-sync-scheduler
* Use runtime information during runtime-specific resolution
* Use runtime environment as provided by user
* Use click echo instead of raw print
* Fix wrong order of tuples
* Provide generic stack information
* Score and report CVEs in the application stack to the user
* Report version on each run
* Do not be too verbose
* Open source documentation for dependency graph
* Document dependency graph build
* Report number of stacks scored
* Raise an exception on premature stream end
* Minor changes in comment and logging message
* Fix coala complains
* Wait for parent to score stacks in stack producer
* Add shared library for CentOS:7
* Provide Dockerfile for container-build
* Add linked library
* Initial dependency graph implementation in C++
* Correctly handle end of pipe
* Adjust .gitignore
* Run dependency graph as a standalone process, produce stacks into pipe
* It's already 2019
* Use proper loglevel for debug message
* Restrict indexes in dependency monkey runs
* Schedule graph syncs for adviser runs by graph-sync-operator
* Fix hashes collision in generated Pipfile.locks
* Implement dependency graph in C++
* Reuse connected graph adapter do reduce number of connections
* Amun API URL is used by Dependency Monkey
* Argument has to be named otherwise cannot be used as kwargs
* Increase run time for dependency monkey
* Propagate whitelisted sources to provenance checks
* Increase dependency monkey requests
* Correctly propagate job ids from workload operator
* Fix CI by updating thoth-python package
* Remove duplicit parameter from template
* Increase adviser job run limit
* Provide limit and count defaults in template
* Add coverage file to .gitignore
* Fix linter issues
* Fix wrong variable usage
* Report limit if limit was reached
* Remove unused imports
* Minor docs fixes
* Link to Dependency Monkey design document
* Add dependency monkey design document into docs
* Cut off and minor adjustmets
* Refactor test suite
* Use black for formatting
* Minor code refactoring, update requirements
* Use to_tuple_locked method as we have locked packages
* Fix missing import
* Construct Pipfile from resolved dependencies
* Print estimated number of software stacks
* Remove unused if statement
* Adjust dependency graph to use ids
* The decision function is now not optional
* Performance based scoring on exact stack match
* Do not pass None values in runtime environment to_dict
* Simplify work with dependency graph
* Fix handling of runtime environment, remove unused bits
* Avoid possibly inserting same package versions multiple times
* Utilize iter_dependencies locked method
* Use Python 3.6 by default
* Discard original sources when creating a new project
* Fix transitive dependencies retrieval
* Don't be too verbose in logs
* Mark jobs for cleanup
* Fetch digests from graph database in provenance checks
* Remove unused perf type
* Prepare dependency graph for graph slicing
* Minor fixes in decision functions
* Restructure scoring and decision functions
* Capture all the layers of dependencies
* Minor code refactoring
* Do not print reasoning into logs
* Fix injecting digests into generated stacks
* Minor fixes in dependency monkey
* Do not forget to package requirements.txt
* Minor fixes
* Raise an exception if no matching versions were found
* Consider also version when creating dependency graph
* Move relevant test files to thoth-python package
* Correctly fill stacks with package digests
* Remove files that were moved to thoth-python
* Include index when retrieving packages from the graph database
* Fill package hashes from the graph database
* Fix import errors
* Structure error reports correctly respecting schema
* Use thoth-python package
* CI fixes
* Fix janusgraph port
* Fix Coala complains
* Fixes and improvements
* Adjust temporary filling package hashes
* Fix missing import
* Pass index to be none always
* Fill package digets in advises
* Be consistent with subcommand naming
* Minor fix in docstring
* Introduce limit in dependency monkey template
* Introduce limit and count in adviser template
* First implementation of the Adviser class
* Default to stdout in dependency monkey
* Refactor dependency monkey so that it can be used in notebooks
* Perform deepcopy to report the correct input
* Fix filling hashes multiple times
* Seed and count can be empty string
* Convert required parameters to ints
* Fix environment variable name
* Place all decision functions at one place
* Improve logging
* Fix missing import
* Make sure queries respect python package names according to PEP
* Improve logging to make sure its visible what's going on
* Fix syntax error
* Fix import error
* Add missing import
* Add ability to submit a testing stack
* Issue warning when submitting to Amun API
* Remove duplicit code for loading Amun context
* Handle exceptions happening when submitting to Amun API
* CI fixes
* Add exception if constraints cannot be met
* Temporary fill package digests by querying PyPI index
* Always check which source in a warehouse
* Adjust output methods
* Adjust dependency monkey job template
* Minor improvements in implementation
* Aaa
* Fixes in the dependency graph implementation
* A package version is distinguished by name, version and index
* Add missing imports
* Check first layer of dependencies for validity
* Sanity check for adding non-locked version to lock
* Add testsuite for graph solver, dependency graph implementation
* Introduce graph Python solver
* Add testsuite for graph solver
* Introduce dependency graph
* Introduce graph Python solver
* reading README from file, its the long_description...

## Release 0.5.0 (2019-07-30T11:12:42)
* :pushpin: Automatic update of dependency thoth-storages from 0.16.0 to 0.17.0
* Deinstantiate solver once it is no longer needed
* Fix instantiation of edges
* Adjust testsuite so that it works with new implementation
* :pushpin: Automatic update of dependency thoth-storages from 0.15.2 to 0.16.0
* Fix handling of additional pytest arguments in setup.py test
* Fix handling of additional pytest arguments in setup.py test
* Move logic of stack candidates preparation to finalization part
* :pushpin: Automatic dependency re-locking
* Remove unused import
* Improve some logger messages
* Rewrite core adviser logic for dependency graph manipulation
* Optimize retrieval of transitive dependencies to avoid list copies
* Optimize instantiation of objects when resolved from graph database
* :pushpin: Automatic update of dependency thoth-storages from 0.15.1 to 0.15.2
* :pushpin: Automatic update of dependency thoth-python from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency thoth-solver from 1.2.1 to 1.2.2
* :pushpin: Automatic update of dependency thoth-storages from 0.15.0 to 0.15.1
* Inform user that the missing release will be analyzed later on
* Remove invalid configuration entry APP_FILE in build config
* :pushpin: Automatic update of dependency thoth-storages from 0.14.8 to 0.15.0
* Fix transitive query - correctly propagate runtime information
* Improve warning message
* :pushpin: Automatic update of dependency thoth-common from 0.9.3 to 0.9.4
* Adjust testing recommendation type for now
* Remove score based cut-off step, observation reduction takes its position
* Add tests for observation based reduction
* Introduce observation reduction step to reduce subgraphs with no observations
* Add error message if no stacks were produced
* Report error if no recommendation was produced
* Introduce routines for iterating over develop and non-develop deps
* :sparkles: added the standard github configuration and a CODEOWNERS file
* Update lockfile
* Report used pipeline configuration of adviser to user
* Additional fixes and additions
* Minor changes
* Use CXXABI_1.3.8
* Use black for formatting
* Rework optimizations
* Adjust testsuite for new implementation
* Implement structure for dependency graph adjustment
* Report packages forming a found stack inside to a log
* Print out estimated number of stacks in scientific form
* Use only packages with known index
* Increase default adviser's requests and limits
* :pushpin: Automatic update of dependency thoth-storages from 0.11.4 to 0.14.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.11 to 0.9.0
* Add build trigger using generic webhook
* :pushpin: Automatic update of dependency pytest from 4.6.2 to 4.6.3
* Updated Readme to Dgraph examples
* :pushpin: Automatic update of dependency thoth-common from 0.8.7 to 0.8.11
* :pushpin: Automatic update of dependency pytest from 4.5.0 to 4.6.2
* Optimize package removal by working on indexes instead of package tuples
* Keep stats for package removals per step run
* Update documentation to respect current state
* Use uint16_t for representing packages in libdependency graph
* Simplify module structure to libdependency_graph library
* :pushpin: Automatic update of dependency thoth-common from 0.8.5 to 0.8.7
* Give adviser more time to process rest of the stacks in queue
* Provide better report to user on why adviser has stopped prematurely
* Use defaults of -1 for "unlimited" numbers in the cluster
* Parse a special value of -1 in the cluster to workaround click's errors
* Be more user-friendly in cluster logs
* Place toolchain cut after semver sort

## Release 0.6.0 (2019-10-28T19:45:51)
* Use THOTH_ADVISE variable for consistency
* updated templates with annotations and param thoth-advise-value
* :pushpin: Automatic update of dependency methodtools from 0.1.1 to 0.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.11 to 0.19.12
* Do not use cached adviser
* :pushpin: Automatic update of dependency thoth-storages from 0.19.10 to 0.19.11
* :pushpin: Automatic update of dependency pytest from 5.2.1 to 5.2.2
* :pushpin: Automatic update of dependency methodtools from 0.1.0 to 0.1.1
* Pin thoth libraries which will have incompatible release
* :pushpin: Automatic update of dependency thoth-python from 0.6.4 to 0.6.5
* :pushpin: Automatic update of dependency pylint from 2.4.2 to 2.4.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.9 to 0.19.10
* :pushpin: Automatic update of dependency thoth-python from 0.6.3 to 0.6.4
* Add spaces to fix toml issues
* :pushpin: Automatic update of dependency thoth-common from 0.9.12 to 0.9.14
* :pushpin: Automatic update of dependency thoth-common from 0.9.11 to 0.9.12
* :pushpin: Automatic update of dependency pytest from 5.2.0 to 5.2.1
* :pushpin: Automatic update of dependency pytest-cov from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency pytest-cov from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency thoth-common from 0.9.10 to 0.9.11
* :pushpin: Automatic update of dependency pylint from 2.4.1 to 2.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.8 to 0.19.9
* :pushpin: Automatic update of dependency pytest from 5.1.3 to 5.2.0
* Fix duration
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.3 to 0.1.4
* :pushpin: Automatic update of dependency thoth-storages from 0.19.7 to 0.19.8
* Fix duration calculation
* Add duration to Adviser
* Re-anable operating system sieve
* Check we do not raise exception if os sieve wants to filter out all packages
* Introduce sieve for limiting number of latest versions in direct dependencies
* Add a new sieve for limiting pre-releases in direct dependencies
* Introduce semver sorting on direct dependnecies - sieve
* Just a minor change to make code great again
* :pushpin: Automatic update of dependency pylint from 2.4.0 to 2.4.1
* Introduce a stable sorting of packages in sieve context
* :pushpin: Automatic update of dependency thoth-storages from 0.19.6 to 0.19.7
* :pushpin: Automatic update of dependency pylint from 2.3.1 to 2.4.0
* use postgresql hostname from thoth configmap
* Add check for upstream tensorflow parsing
* :pushpin: Automatic update of dependency thoth-python from 0.6.2 to 0.6.3
* Adjust os sieve testsuite to reflect changes
* Introduce tests for checking correct parsing of AICoE releases
* :pushpin: Automatic update of dependency thoth-storages from 0.19.5 to 0.19.6
* :pushpin: Automatic update of dependency pytest from 5.1.2 to 5.1.3
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.2 to 0.1.3
* Add seldon and seldon-core to cached packages
* Create a check and test case to handle errors when trying to resolve unsolved packages
* :pushpin: Automatic update of dependency thoth-common from 0.9.9 to 0.9.10
* :pushpin: Automatic update of dependency thoth-storages from 0.19.4 to 0.19.5
* :pushpin: Automatic update of dependency thoth-common from 0.9.8 to 0.9.9
* Corrected typos
* :pushpin: Automatic update of dependency thoth-storages from 0.19.3 to 0.19.4
* Add Sentry DSN to build of adviser-cached
* :pushpin: Automatic update of dependency thoth-storages from 0.19.2 to 0.19.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.1 to 0.19.2
* Propagate deployment name to have reports when cache is built
* Propagate deployment name for sentry environment
* :pushpin: Automatic update of dependency thoth-storages from 0.19.0 to 0.19.1
* Fix testsuite
* Make coala happy
* Fix indentation issues
* Relock requirements
* Fix exception message
* Print out packages before each pipeline unit
* Implement solved sieve
* Changes needed for PostgreSQL migration
* Add a pipeline step which removes unsolved packages
* Do not use -e flag
* Store and restore cache on builds
* Add more packages to cache config file
* Adjust cache not to cache graph database adapter
* Create adviser cache during container build
* :pushpin: Automatic update of dependency thoth-python from 0.6.1 to 0.6.2
* :pushpin: Automatic update of dependency thoth-storages from 0.18.6 to 0.19.0
* Propagate runtime environment explicitly
* Use more generic env var names
* Remove performance related tests
* Drop generic performance querying
* Start using PostgreSQL in deployment
* :pushpin: Automatic update of dependency semantic-version from 2.8.1 to 2.8.2
* :pushpin: Automatic update of dependency pytest from 5.1.1 to 5.1.2
* :pushpin: Automatic update of dependency semantic-version from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency semantic-version from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency semantic-version from 2.7.0 to 2.7.1
* :pushpin: Automatic update of dependency semantic-version from 2.6.0 to 2.7.0
* Turn error into warning
* :pushpin: Automatic update of dependency pytest from 5.1.0 to 5.1.1
* Improve error message reported if no releases were found
* State how to integrate with Thoth in docs
* Do not use setuptools.find_namespace_packages() for now
* Start using Thoth's s2i base image
* Fix missing packages in adviser's package
* :pushpin: Automatic update of dependency pytest from 5.0.1 to 5.1.0
* :pushpin: Automatic update of dependency pydocstyle from 4.0.0 to 4.0.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.5 to 0.18.6
* :pushpin: Automatic update of dependency thoth-common from 0.9.7 to 0.9.8
* :pushpin: Automatic update of dependency thoth-common from 0.9.6 to 0.9.7
* Document how to make changes in the dependency graph while it changes
* A package can be removed in the previous sub-graphs removals
* :pushpin: Automatic update of dependency voluptuous from 0.11.5 to 0.11.7
* :pushpin: Automatic update of dependency thoth-python from 0.6.0 to 0.6.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.4 to 0.18.5
* Change name of Thoth template to make Coala happy
* Start using Thoth in OpenShift's s2i
* Adjust testsuite to use only_solved flag
* Ask graph database only for packages which were already solved
* Do not remove package tuples which are direct dependencies
* Do not treat builds as pre-releases
* Fix reference to variable - do not pass class
* Fix resolving direct dependencies based on the score
* :pushpin: Automatic update of dependency thoth-storages from 0.18.3 to 0.18.4
* Introduce sieves
* :pushpin: Automatic update of dependency thoth-common from 0.9.5 to 0.9.6
* Update docs with sieves
* Add docs for performance indicators
* :pushpin: Automatic update of dependency thoth-storages from 0.18.1 to 0.18.3
* :pushpin: Automatic update of dependency thoth-storages from 0.18.0 to 0.18.1
* :pushpin: Automatic update of dependency thoth-storages from 0.17.0 to 0.18.0

## Release 0.6.0 (2019-11-01T15:47:13)
* Start using adaptive simulated annealing
* Release of version 0.6.0
* Use THOTH_ADVISE variable for consistency
* updated templates with annotations and param thoth-advise-value
* :pushpin: Automatic update of dependency methodtools from 0.1.1 to 0.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.11 to 0.19.12
* Do not use cached adviser
* :pushpin: Automatic update of dependency thoth-storages from 0.19.10 to 0.19.11
* :pushpin: Automatic update of dependency pytest from 5.2.1 to 5.2.2
* :pushpin: Automatic update of dependency methodtools from 0.1.0 to 0.1.1
* Pin thoth libraries which will have incompatible release
* :pushpin: Automatic update of dependency thoth-python from 0.6.4 to 0.6.5
* :pushpin: Automatic update of dependency pylint from 2.4.2 to 2.4.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.9 to 0.19.10
* :pushpin: Automatic update of dependency thoth-python from 0.6.3 to 0.6.4
* Add spaces to fix toml issues
* :pushpin: Automatic update of dependency thoth-common from 0.9.12 to 0.9.14
* :pushpin: Automatic update of dependency thoth-common from 0.9.11 to 0.9.12
* :pushpin: Automatic update of dependency pytest from 5.2.0 to 5.2.1
* :pushpin: Automatic update of dependency pytest-cov from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency pytest-cov from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency thoth-common from 0.9.10 to 0.9.11
* :pushpin: Automatic update of dependency pylint from 2.4.1 to 2.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.8 to 0.19.9
* :pushpin: Automatic update of dependency pytest from 5.1.3 to 5.2.0
* Fix duration
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.3 to 0.1.4
* :pushpin: Automatic update of dependency thoth-storages from 0.19.7 to 0.19.8
* Fix duration calculation
* Add duration to Adviser
* Re-anable operating system sieve
* Check we do not raise exception if os sieve wants to filter out all packages
* Introduce sieve for limiting number of latest versions in direct dependencies
* Add a new sieve for limiting pre-releases in direct dependencies
* Introduce semver sorting on direct dependnecies - sieve
* Just a minor change to make code great again
* :pushpin: Automatic update of dependency pylint from 2.4.0 to 2.4.1
* Introduce a stable sorting of packages in sieve context
* :pushpin: Automatic update of dependency thoth-storages from 0.19.6 to 0.19.7
* :pushpin: Automatic update of dependency pylint from 2.3.1 to 2.4.0
* use postgresql hostname from thoth configmap
* Add check for upstream tensorflow parsing
* :pushpin: Automatic update of dependency thoth-python from 0.6.2 to 0.6.3
* Adjust os sieve testsuite to reflect changes
* Introduce tests for checking correct parsing of AICoE releases
* :pushpin: Automatic update of dependency thoth-storages from 0.19.5 to 0.19.6
* :pushpin: Automatic update of dependency pytest from 5.1.2 to 5.1.3
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.2 to 0.1.3
* Add seldon and seldon-core to cached packages
* Create a check and test case to handle errors when trying to resolve unsolved packages
* :pushpin: Automatic update of dependency thoth-common from 0.9.9 to 0.9.10
* :pushpin: Automatic update of dependency thoth-storages from 0.19.4 to 0.19.5
* :pushpin: Automatic update of dependency thoth-common from 0.9.8 to 0.9.9
* Corrected typos
* :pushpin: Automatic update of dependency thoth-storages from 0.19.3 to 0.19.4
* Add Sentry DSN to build of adviser-cached
* :pushpin: Automatic update of dependency thoth-storages from 0.19.2 to 0.19.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.1 to 0.19.2
* Propagate deployment name to have reports when cache is built
* Propagate deployment name for sentry environment
* :pushpin: Automatic update of dependency thoth-storages from 0.19.0 to 0.19.1
* Fix testsuite
* Make coala happy
* Fix indentation issues
* Relock requirements
* Fix exception message
* Print out packages before each pipeline unit
* Implement solved sieve
* Changes needed for PostgreSQL migration
* Add a pipeline step which removes unsolved packages
* Do not use -e flag
* Store and restore cache on builds
* Add more packages to cache config file
* Adjust cache not to cache graph database adapter
* Create adviser cache during container build
* :pushpin: Automatic update of dependency thoth-python from 0.6.1 to 0.6.2
* :pushpin: Automatic update of dependency thoth-storages from 0.18.6 to 0.19.0
* Propagate runtime environment explicitly
* Use more generic env var names
* Remove performance related tests
* Drop generic performance querying
* Start using PostgreSQL in deployment
* :pushpin: Automatic update of dependency semantic-version from 2.8.1 to 2.8.2
* :pushpin: Automatic update of dependency pytest from 5.1.1 to 5.1.2
* :pushpin: Automatic update of dependency semantic-version from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency semantic-version from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency semantic-version from 2.7.0 to 2.7.1
* :pushpin: Automatic update of dependency semantic-version from 2.6.0 to 2.7.0
* Turn error into warning
* :pushpin: Automatic update of dependency pytest from 5.1.0 to 5.1.1
* Improve error message reported if no releases were found
* State how to integrate with Thoth in docs
* Do not use setuptools.find_namespace_packages() for now
* Start using Thoth's s2i base image
* Fix missing packages in adviser's package
* :pushpin: Automatic update of dependency pytest from 5.0.1 to 5.1.0
* :pushpin: Automatic update of dependency pydocstyle from 4.0.0 to 4.0.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.5 to 0.18.6
* :pushpin: Automatic update of dependency thoth-common from 0.9.7 to 0.9.8
* :pushpin: Automatic update of dependency thoth-common from 0.9.6 to 0.9.7
* Document how to make changes in the dependency graph while it changes
* A package can be removed in the previous sub-graphs removals
* :pushpin: Automatic update of dependency voluptuous from 0.11.5 to 0.11.7
* :pushpin: Automatic update of dependency thoth-python from 0.6.0 to 0.6.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.4 to 0.18.5
* Change name of Thoth template to make Coala happy
* Start using Thoth in OpenShift's s2i
* Adjust testsuite to use only_solved flag
* Ask graph database only for packages which were already solved
* Do not remove package tuples which are direct dependencies
* Do not treat builds as pre-releases
* Fix reference to variable - do not pass class
* Fix resolving direct dependencies based on the score
* :pushpin: Automatic update of dependency thoth-storages from 0.18.3 to 0.18.4
* Introduce sieves
* :pushpin: Automatic update of dependency thoth-common from 0.9.5 to 0.9.6
* Update docs with sieves
* Add docs for performance indicators
* :pushpin: Automatic update of dependency thoth-storages from 0.18.1 to 0.18.3
* :pushpin: Automatic update of dependency thoth-storages from 0.18.0 to 0.18.1
* :pushpin: Automatic update of dependency thoth-storages from 0.17.0 to 0.18.0

## Release 0.6.1 (2019-11-06T11:39:17)
* :pushpin: Automatic update of dependency hypothesis from 4.43.4 to 4.43.5
* :pushpin: Automatic update of dependency hypothesis from 4.43.3 to 4.43.4
* :pushpin: Automatic update of dependency hypothesis from 4.43.2 to 4.43.3
* Cache queries for retrieving enabled indexes
* :pushpin: Automatic update of dependency hypothesis from 4.43.1 to 4.43.2
* Use slots on pipeline unit instances
* Fix resolving direct dependencies when pagination is used
* :pushpin: Automatic update of dependency thoth-storages from 0.19.14 to 0.19.15
* :pushpin: Automatic update of dependency hypothesis from 4.43.0 to 4.43.1
* :pushpin: Automatic update of dependency hypothesis from 4.42.10 to 4.43.0
* :pushpin: Automatic update of dependency pytest-mypy from 0.4.1 to 0.4.2
* :pushpin: Automatic update of dependency hypothesis from 4.42.9 to 4.42.10
* :pushpin: Automatic update of dependency hypothesis from 4.42.8 to 4.42.9
* :pushpin: Automatic update of dependency hypothesis from 4.42.7 to 4.42.8
* :pushpin: Automatic update of dependency hypothesis from 4.42.6 to 4.42.7
* :pushpin: Automatic update of dependency hypothesis from 4.42.5 to 4.42.6
* :pushpin: Automatic update of dependency hypothesis from 4.42.4 to 4.42.5
* Release of version 0.6.0
* :pushpin: Automatic update of dependency hypothesis from 4.42.0 to 4.42.4
* Start using adaptive simulated annealing

## Release 0.7.0 (2019-12-05T17:16:02)
* :pushpin: Automatic update of dependency hypothesis from 4.50.6 to 4.50.7
* Fix coala complains
* Enhance exception
* Give more information dependencies were not resolved
* Set beam width template in the adviser template job
* Fix coala complains
* Some docs for readers and developers
* Fix stride signature
* Fix boot docstring
* Fix tests
* Optimizations of beam
* Fix Coala complains
* Use generators to retrieve items
* Provide property for run executor that prints report
* Provide an option to configure pipeline via file/dict
* Log package version before pipeline step execution
* Remove unused method
* Test simulated annealing primitives, refactor core annealing part
* Step should not return Nan/Inf
* Use backtracking to run steps
* Make coala happy again
* Add tests for two corner cases for package clash during resolution
* Fix beam top manipulation
* Add logic for registering a final state
* Add dependencies only if they were previously considered based on env marker
* Remove print used during debugging
* :pushpin: Automatic update of dependency hypothesis from 4.50.5 to 4.50.6
* :pushpin: Automatic update of dependency hypothesis from 4.50.4 to 4.50.5
* :pushpin: Automatic update of dependency hypothesis from 4.50.3 to 4.50.4
* :pushpin: Automatic update of dependency hypothesis from 4.50.2 to 4.50.3
* Change default number of stacks returned on call
* Fix parameter to adviser CLI
* Adjust logged messages
* Make beam instance of resolver
* Adjust limit latest versions signature, do not perform shallow copy
* Sieve now accepts and returns a generator of package versions
* :pushpin: Automatic update of dependency thoth-storages from 0.19.24 to 0.19.25
* Address review comments
* :pushpin: Automatic update of dependency hypothesis from 4.50.1 to 4.50.2
* Fix coala issues
* Fix typo in docstring
* :pushpin: Automatic update of dependency hypothesis from 4.50.0 to 4.50.1
* :pushpin: Automatic update of dependency hypothesis from 4.49.0 to 4.50.0
* Optimize retrieval of environment markers
* :pushpin: Automatic update of dependency hypothesis from 4.48.0 to 4.49.0
* :pushpin: Automatic update of dependency hypothesis from 4.47.4 to 4.48.0
* Even more tests
* :pushpin: Automatic update of dependency hypothesis from 4.47.3 to 4.47.4
* Propagate document id into jobs
* More tests
* :pushpin: Automatic update of dependency hypothesis from 4.47.2 to 4.47.3
* :pushpin: Automatic update of dependency pytest from 5.3.0 to 5.3.1
* :pushpin: Automatic update of dependency hypothesis from 4.47.1 to 4.47.2
* :pushpin: Automatic update of dependency hypothesis from 4.47.0 to 4.47.1
* :pushpin: Automatic update of dependency hypothesis from 4.46.1 to 4.47.0
* :pushpin: Automatic update of dependency hypothesis from 4.46.0 to 4.46.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.23 to 0.19.24
* :pushpin: Automatic update of dependency hypothesis from 4.45.1 to 4.46.0
* :pushpin: Automatic update of dependency matplotlib from 3.1.1 to 3.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.22 to 0.19.23
* Remove unused imports
* :pushpin: Automatic update of dependency hypothesis from 4.45.0 to 4.45.1
* :pushpin: Automatic update of dependency hypothesis from 4.44.4 to 4.45.0
* :pushpin: Automatic update of dependency hypothesis from 4.44.2 to 4.44.4
* :pushpin: Automatic update of dependency pytest from 5.2.4 to 5.3.0
* :pushpin: Automatic update of dependency thoth-storages from 0.19.21 to 0.19.22
* :pushpin: Automatic update of dependency thoth-storages from 0.19.19 to 0.19.21
* Bump library versions
* Fix hashes representation in the generated Pipfile.lock
* Remove score filter stride
* Remove Dgraph leftovers
* Hotfix for obtained hashes
* Minor typo fixes
* Notify when a new pipeline product was produced
* Notify user when computing recommendations
* Update dependencies
* :pushpin: Automatic update of dependency thoth-storages from 0.19.18 to 0.19.19
* Fix coala complains
* Plotting environment variables were renamed
* Split adviser implementation for extensibility and testing
* :pushpin: Automatic update of dependency hypothesis from 4.44.1 to 4.44.2
* :pushpin: Automatic update of dependency hypothesis from 4.44.0 to 4.44.1
* :pushpin: Automatic update of dependency hypothesis from 4.43.8 to 4.44.0
* Add missing modules
* :pushpin: Automatic update of dependency thoth-storages from 0.19.17 to 0.19.18
* Update dependencies for new API
* :pushpin: Automatic update of dependency hypothesis from 4.43.6 to 4.43.8
* New thoth-python uses packaging's Version with different API
* Remove old test - solver does not support latest versions anymore
* Fix coala issues - reformat using black
* Use new solver implementation
* Update README to show how to run adviser locally
* :pushpin: Automatic update of dependency hypothesis from 4.43.5 to 4.43.6
* :pushpin: Automatic update of dependency thoth-storages from 0.19.15 to 0.19.17
* Adjust provenance-checker output to be in alaign with adviser and dm
* Revert "runtime_environment var should be dict in parameter"
* Fix exit code propagation to the main process
* runtime_environment var should be dict in parameter
* Release of version 0.6.1
* :pushpin: Automatic update of dependency hypothesis from 4.43.4 to 4.43.5
* :pushpin: Automatic update of dependency hypothesis from 4.43.3 to 4.43.4
* :pushpin: Automatic update of dependency hypothesis from 4.43.2 to 4.43.3
* Cache queries for retrieving enabled indexes
* :pushpin: Automatic update of dependency hypothesis from 4.43.1 to 4.43.2
* Use slots on pipeline unit instances
* Fix resolving direct dependencies when pagination is used
* :pushpin: Automatic update of dependency thoth-storages from 0.19.14 to 0.19.15
* :pushpin: Automatic update of dependency hypothesis from 4.43.0 to 4.43.1
* :pushpin: Automatic update of dependency hypothesis from 4.42.10 to 4.43.0
* :pushpin: Automatic update of dependency pytest-mypy from 0.4.1 to 0.4.2
* :pushpin: Automatic update of dependency hypothesis from 4.42.9 to 4.42.10
* :pushpin: Automatic update of dependency hypothesis from 4.42.8 to 4.42.9
* :pushpin: Automatic update of dependency hypothesis from 4.42.7 to 4.42.8
* :pushpin: Automatic update of dependency hypothesis from 4.42.6 to 4.42.7
* :pushpin: Automatic update of dependency hypothesis from 4.42.5 to 4.42.6
* :pushpin: Automatic update of dependency hypothesis from 4.42.4 to 4.42.5
* Release of version 0.6.0
* :pushpin: Automatic update of dependency hypothesis from 4.42.0 to 4.42.4
* Start using adaptive simulated annealing
* Release of version 0.6.0
* Use THOTH_ADVISE variable for consistency
* updated templates with annotations and param thoth-advise-value
* :pushpin: Automatic update of dependency methodtools from 0.1.1 to 0.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.11 to 0.19.12
* Do not use cached adviser
* :pushpin: Automatic update of dependency thoth-storages from 0.19.10 to 0.19.11
* :pushpin: Automatic update of dependency pytest from 5.2.1 to 5.2.2
* :pushpin: Automatic update of dependency methodtools from 0.1.0 to 0.1.1
* Pin thoth libraries which will have incompatible release
* :pushpin: Automatic update of dependency thoth-python from 0.6.4 to 0.6.5
* :pushpin: Automatic update of dependency pylint from 2.4.2 to 2.4.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.9 to 0.19.10
* :pushpin: Automatic update of dependency thoth-python from 0.6.3 to 0.6.4
* Add spaces to fix toml issues
* :pushpin: Automatic update of dependency thoth-common from 0.9.12 to 0.9.14
* :pushpin: Automatic update of dependency thoth-common from 0.9.11 to 0.9.12
* :pushpin: Automatic update of dependency pytest from 5.2.0 to 5.2.1
* :pushpin: Automatic update of dependency pytest-cov from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency pytest-cov from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency thoth-common from 0.9.10 to 0.9.11
* :pushpin: Automatic update of dependency pylint from 2.4.1 to 2.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.8 to 0.19.9
* :pushpin: Automatic update of dependency pytest from 5.1.3 to 5.2.0
* Fix duration
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.3 to 0.1.4
* :pushpin: Automatic update of dependency thoth-storages from 0.19.7 to 0.19.8
* Fix duration calculation
* Add duration to Adviser
* Re-anable operating system sieve
* Check we do not raise exception if os sieve wants to filter out all packages
* Introduce sieve for limiting number of latest versions in direct dependencies
* Add a new sieve for limiting pre-releases in direct dependencies
* Introduce semver sorting on direct dependnecies - sieve
* Just a minor change to make code great again
* :pushpin: Automatic update of dependency pylint from 2.4.0 to 2.4.1
* Introduce a stable sorting of packages in sieve context
* :pushpin: Automatic update of dependency thoth-storages from 0.19.6 to 0.19.7
* :pushpin: Automatic update of dependency pylint from 2.3.1 to 2.4.0
* use postgresql hostname from thoth configmap
* Add check for upstream tensorflow parsing
* :pushpin: Automatic update of dependency thoth-python from 0.6.2 to 0.6.3
* Adjust os sieve testsuite to reflect changes
* Introduce tests for checking correct parsing of AICoE releases
* :pushpin: Automatic update of dependency thoth-storages from 0.19.5 to 0.19.6
* :pushpin: Automatic update of dependency pytest from 5.1.2 to 5.1.3
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.2 to 0.1.3
* Add seldon and seldon-core to cached packages
* Create a check and test case to handle errors when trying to resolve unsolved packages
* :pushpin: Automatic update of dependency thoth-common from 0.9.9 to 0.9.10
* :pushpin: Automatic update of dependency thoth-storages from 0.19.4 to 0.19.5
* :pushpin: Automatic update of dependency thoth-common from 0.9.8 to 0.9.9
* Corrected typos
* :pushpin: Automatic update of dependency thoth-storages from 0.19.3 to 0.19.4
* Add Sentry DSN to build of adviser-cached
* :pushpin: Automatic update of dependency thoth-storages from 0.19.2 to 0.19.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.1 to 0.19.2
* Propagate deployment name to have reports when cache is built
* Propagate deployment name for sentry environment
* :pushpin: Automatic update of dependency thoth-storages from 0.19.0 to 0.19.1
* Fix testsuite
* Make coala happy
* Fix indentation issues
* Relock requirements
* Fix exception message
* Print out packages before each pipeline unit
* Implement solved sieve
* Changes needed for PostgreSQL migration
* Add a pipeline step which removes unsolved packages
* Do not use -e flag
* Store and restore cache on builds
* Add more packages to cache config file
* Adjust cache not to cache graph database adapter
* Create adviser cache during container build
* :pushpin: Automatic update of dependency thoth-python from 0.6.1 to 0.6.2
* :pushpin: Automatic update of dependency thoth-storages from 0.18.6 to 0.19.0
* Propagate runtime environment explicitly
* Use more generic env var names
* Remove performance related tests
* Drop generic performance querying
* Start using PostgreSQL in deployment
* :pushpin: Automatic update of dependency semantic-version from 2.8.1 to 2.8.2
* :pushpin: Automatic update of dependency pytest from 5.1.1 to 5.1.2
* :pushpin: Automatic update of dependency semantic-version from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency semantic-version from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency semantic-version from 2.7.0 to 2.7.1
* :pushpin: Automatic update of dependency semantic-version from 2.6.0 to 2.7.0
* Turn error into warning
* :pushpin: Automatic update of dependency pytest from 5.1.0 to 5.1.1
* Improve error message reported if no releases were found
* State how to integrate with Thoth in docs
* Do not use setuptools.find_namespace_packages() for now
* Start using Thoth's s2i base image
* Fix missing packages in adviser's package
* :pushpin: Automatic update of dependency pytest from 5.0.1 to 5.1.0
* :pushpin: Automatic update of dependency pydocstyle from 4.0.0 to 4.0.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.5 to 0.18.6
* :pushpin: Automatic update of dependency thoth-common from 0.9.7 to 0.9.8
* :pushpin: Automatic update of dependency thoth-common from 0.9.6 to 0.9.7
* Document how to make changes in the dependency graph while it changes
* A package can be removed in the previous sub-graphs removals
* :pushpin: Automatic update of dependency voluptuous from 0.11.5 to 0.11.7
* :pushpin: Automatic update of dependency thoth-python from 0.6.0 to 0.6.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.4 to 0.18.5
* Change name of Thoth template to make Coala happy
* Start using Thoth in OpenShift's s2i
* Adjust testsuite to use only_solved flag
* Ask graph database only for packages which were already solved
* Do not remove package tuples which are direct dependencies
* Do not treat builds as pre-releases
* Fix reference to variable - do not pass class
* Fix resolving direct dependencies based on the score
* :pushpin: Automatic update of dependency thoth-storages from 0.18.3 to 0.18.4
* Introduce sieves
* :pushpin: Automatic update of dependency thoth-common from 0.9.5 to 0.9.6
* Update docs with sieves
* Add docs for performance indicators
* :pushpin: Automatic update of dependency thoth-storages from 0.18.1 to 0.18.3
* :pushpin: Automatic update of dependency thoth-storages from 0.18.0 to 0.18.1
* :pushpin: Automatic update of dependency thoth-storages from 0.17.0 to 0.18.0
* Release of version 0.5.0
* :pushpin: Automatic update of dependency thoth-storages from 0.16.0 to 0.17.0
* Deinstantiate solver once it is no longer needed
* Fix instantiation of edges
* Adjust testsuite so that it works with new implementation
* :pushpin: Automatic update of dependency thoth-storages from 0.15.2 to 0.16.0
* Fix handling of additional pytest arguments in setup.py test
* Fix handling of additional pytest arguments in setup.py test
* Move logic of stack candidates preparation to finalization part
* :pushpin: Automatic dependency re-locking
* Remove unused import
* Improve some logger messages
* Rewrite core adviser logic for dependency graph manipulation
* Optimize retrieval of transitive dependencies to avoid list copies
* Optimize instantiation of objects when resolved from graph database
* :pushpin: Automatic update of dependency thoth-storages from 0.15.1 to 0.15.2
* :pushpin: Automatic update of dependency thoth-python from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency thoth-solver from 1.2.1 to 1.2.2
* :pushpin: Automatic update of dependency thoth-storages from 0.15.0 to 0.15.1
* Inform user that the missing release will be analyzed later on
* Remove invalid configuration entry APP_FILE in build config
* :pushpin: Automatic update of dependency thoth-storages from 0.14.8 to 0.15.0
* Fix transitive query - correctly propagate runtime information
* Improve warning message
* :pushpin: Automatic update of dependency thoth-common from 0.9.3 to 0.9.4
* Adjust testing recommendation type for now
* Remove score based cut-off step, observation reduction takes its position
* Add tests for observation based reduction
* Introduce observation reduction step to reduce subgraphs with no observations
* Add error message if no stacks were produced
* Report error if no recommendation was produced
* Introduce routines for iterating over develop and non-develop deps
* :sparkles: added the standard github configuration and a CODEOWNERS file
* Update lockfile
* Report used pipeline configuration of adviser to user
* Additional fixes and additions
* Minor changes
* Use CXXABI_1.3.8
* Use black for formatting
* Rework optimizations
* Adjust testsuite for new implementation
* Implement structure for dependency graph adjustment
* Report packages forming a found stack inside to a log
* Print out estimated number of stacks in scientific form
* Use only packages with known index
* Increase default adviser's requests and limits
* :pushpin: Automatic update of dependency thoth-storages from 0.11.4 to 0.14.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.11 to 0.9.0
* Add build trigger using generic webhook
* :pushpin: Automatic update of dependency pytest from 4.6.2 to 4.6.3
* Updated Readme to Dgraph examples
* :pushpin: Automatic update of dependency thoth-common from 0.8.7 to 0.8.11
* :pushpin: Automatic update of dependency pytest from 4.5.0 to 4.6.2
* Optimize package removal by working on indexes instead of package tuples
* Keep stats for package removals per step run
* Update documentation to respect current state
* Use uint16_t for representing packages in libdependency graph
* Simplify module structure to libdependency_graph library
* :pushpin: Automatic update of dependency thoth-common from 0.8.5 to 0.8.7
* Give adviser more time to process rest of the stacks in queue
* Provide better report to user on why adviser has stopped prematurely
* Use defaults of -1 for "unlimited" numbers in the cluster
* Parse a special value of -1 in the cluster to workaround click's errors
* Be more user-friendly in cluster logs
* Place toolchain cut after semver sort
* :pushpin: Automatic update of dependency pytest from 4.4.2 to 4.5.0
* :pushpin: Automatic update of dependency thoth-storages from 0.11.3 to 0.11.4
* Re-introduce filedump for fixes on long-lasting queries
* Log number of packages considered during dependency graph traversals
* Fix testsuite
* Create pipeline builder abstraction
* :pushpin: Automatic update of dependency thoth-storages from 0.11.2 to 0.11.3
* Release of version 0.4.0
* Fix coala issues
* :pushpin: Automatic update of dependency pytest from 4.4.1 to 4.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.11.1 to 0.11.2
* Use new method to obtain even large stacks from graph database
* :pushpin: Automatic update of dependency mock from 3.0.4 to 3.0.5
* :pushpin: Automatic update of dependency mock from 3.0.3 to 3.0.4
* Add information about library usage to pipeline and OpenShift job
* Build-time error filtering should be a very first step
* Propagate information about project runtime when checking buildtime error
* Fix issue happening in semver sort after a package is removed
* Remove toolchain to always use latest toolchain release
* Fix empty paths if there is raised an exception about invalid pkg removal
* :pushpin: Automatic update of dependency thoth-storages from 0.11.0 to 0.11.1
* Log message was missleading if package_tuple gets overwritten
* Provide fast-path when checking for already removed packages
* :pushpin: Automatic update of dependency pytest-cov from 2.6.1 to 2.7.1
* Implement build-time error filtering step
* :pushpin: Automatic update of dependency mock from 3.0.2 to 3.0.3
* :pushpin: Automatic update of dependency mock from 2.0.0 to 3.0.2
* :pushpin: Automatic update of dependency thoth-storages from 0.10.0 to 0.11.0
* Adjust provenance-checker template to use Dgraph
* Adjust Dependency Monkey to use Dgraph
* Adjust adviser template to use Dgraph
* Report overall score of a stack
* Remove is_solvable flag as done in Dgraph implementation
* Added the method to read version from project to conf.py
* Remove JanusGraph specific bits
* Do not depend on specific graph adapter from specific module
* Remove JanusGraph specific bits
* :pushpin: Automatic update of dependency thoth-storages from 0.9.7 to 0.10.0
* Trigger dependency monkey reports sync into graph database
* :pushpin: Automatic update of dependency pytest from 4.4.0 to 4.4.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.4 to 0.8.5
* Automatic update of dependency thoth-common from 0.8.3 to 0.8.4
* Create a workaround for click argument parsing from env vars
* :sparkles: added the Registry to be used for image pulling to the templates
* Adviser implementation using stack generation pipeline
* Automatic update of dependency thoth-common from 0.8.2 to 0.8.3
* Make Isis a proper adapter
* Automatic update of dependency thoth-common from 0.8.1 to 0.8.2
* Automatic update of dependency pytest from 4.3.1 to 4.4.0
* :bug: put some sane default for IMAGE_STREAM_NAMESPACE into each template
* hot fixing the timeout
* :sparkles: ImageStream Tag and Namespace
* Automatic update of dependency flexmock from 0.10.3 to 0.10.4
* Report premature end of stack stream
* Improve handling of long-running advises
* Add timeout seconds for adviser to let it submit results
* Top score is now 100
* Automatic update of dependency thoth-storages from 0.9.6 to 0.9.7
* Automatic update of dependency thoth-python from 0.4.6 to 0.5.0
* Make reports more human readable
* Fix testsuite
* Add Thoth's configuration file
* Make Isis instance attribute
* Always kill stack producer if there is no consumer of stacks
* Fix Coala issues
* Do not score more than requested number of latest stacks
* Introduce stack producer timeout
* Use Sphinx for documentation
* Fix some test errors
* Minor improvements
* Introduce parameters for limiting number of versions
* Introduce limit parameter to limit number of packages of a same type
* Fix usage of package_t in libdependency_graph.so
* Use safe_load
* Fix coala complains
* Report any exception which occurred during dependency monkey run
* Introduce checks on configuration
* Make sure Isis is a singleton
* Minor fix in logged message
* Use Isis API from configmap
* Introduce performance based queries to Isis
* Make Coala happy again
* Use black for formatting
* Add missing file
* Make sure versions are sorted, add tests for adviser
* Use black for formatting tests
* Fix tests
* Log runtime environment when computing advises
* Address coala issues
* Add an optional graph database adapter to reduce number of connections
* Take into account packages that are not installable into the given env
* Update README, state local run in a container
* Report CVE count only if there were some found
* Remove unused env variables
* Provide Sentry and Prometheus configuration
* Add metadata information shown in result reports
* Update Pipfile.lock
* Register provenance-checker to graph-sync-scheduler
* Use runtime information during runtime-specific resolution
* Use runtime environment as provided by user
* Use click echo instead of raw print
* Fix wrong order of tuples
* Provide generic stack information
* Score and report CVEs in the application stack to the user
* Report version on each run
* Do not be too verbose
* Open source documentation for dependency graph
* Document dependency graph build
* Report number of stacks scored
* Raise an exception on premature stream end
* Minor changes in comment and logging message
* Fix coala complains
* Wait for parent to score stacks in stack producer
* Add shared library for CentOS:7
* Provide Dockerfile for container-build
* Add linked library
* Initial dependency graph implementation in C++
* Correctly handle end of pipe
* Adjust .gitignore
* Run dependency graph as a standalone process, produce stacks into pipe
* It's already 2019
* Use proper loglevel for debug message
* Restrict indexes in dependency monkey runs
* Schedule graph syncs for adviser runs by graph-sync-operator
* Fix hashes collision in generated Pipfile.locks
* Implement dependency graph in C++
* Reuse connected graph adapter do reduce number of connections
* Amun API URL is used by Dependency Monkey
* Argument has to be named otherwise cannot be used as kwargs
* Increase run time for dependency monkey
* Propagate whitelisted sources to provenance checks
* Increase dependency monkey requests
* Correctly propagate job ids from workload operator
* Fix CI by updating thoth-python package
* Remove duplicit parameter from template
* Increase adviser job run limit
* Provide limit and count defaults in template
* Add coverage file to .gitignore
* Fix linter issues
* Fix wrong variable usage
* Report limit if limit was reached
* Remove unused imports
* Minor docs fixes
* Link to Dependency Monkey design document
* Add dependency monkey design document into docs
* Cut off and minor adjustmets
* Refactor test suite
* Use black for formatting
* Minor code refactoring, update requirements
* Use to_tuple_locked method as we have locked packages
* Fix missing import
* Construct Pipfile from resolved dependencies
* Print estimated number of software stacks
* Remove unused if statement
* Adjust dependency graph to use ids
* The decision function is now not optional
* Performance based scoring on exact stack match
* Do not pass None values in runtime environment to_dict
* Simplify work with dependency graph
* Fix handling of runtime environment, remove unused bits
* Avoid possibly inserting same package versions multiple times
* Utilize iter_dependencies locked method
* Use Python 3.6 by default
* Discard original sources when creating a new project
* Fix transitive dependencies retrieval
* Don't be too verbose in logs
* Mark jobs for cleanup
* Fetch digests from graph database in provenance checks
* Remove unused perf type
* Prepare dependency graph for graph slicing
* Minor fixes in decision functions
* Restructure scoring and decision functions
* Capture all the layers of dependencies
* Minor code refactoring
* Do not print reasoning into logs
* Fix injecting digests into generated stacks
* Minor fixes in dependency monkey
* Do not forget to package requirements.txt
* Minor fixes
* Raise an exception if no matching versions were found
* Consider also version when creating dependency graph
* Move relevant test files to thoth-python package
* Correctly fill stacks with package digests
* Remove files that were moved to thoth-python
* Include index when retrieving packages from the graph database
* Fill package hashes from the graph database
* Fix import errors
* Structure error reports correctly respecting schema
* Use thoth-python package
* CI fixes
* Fix janusgraph port
* Fix Coala complains
* Fixes and improvements
* Adjust temporary filling package hashes
* Fix missing import
* Pass index to be none always
* Fill package digets in advises
* Be consistent with subcommand naming
* Minor fix in docstring
* Introduce limit in dependency monkey template
* Introduce limit and count in adviser template
* First implementation of the Adviser class
* Default to stdout in dependency monkey
* Refactor dependency monkey so that it can be used in notebooks
* Perform deepcopy to report the correct input
* Fix filling hashes multiple times
* Seed and count can be empty string
* Convert required parameters to ints
* Fix environment variable name
* Place all decision functions at one place
* Improve logging
* Fix missing import
* Make sure queries respect python package names according to PEP
* Improve logging to make sure its visible what's going on
* Fix syntax error
* Fix import error
* Add missing import
* Add ability to submit a testing stack
* Issue warning when submitting to Amun API
* Remove duplicit code for loading Amun context
* Handle exceptions happening when submitting to Amun API
* CI fixes
* Add exception if constraints cannot be met
* Temporary fill package digests by querying PyPI index
* Always check which source in a warehouse
* Adjust output methods
* Adjust dependency monkey job template
* Minor improvements in implementation
* Aaa
* Fixes in the dependency graph implementation
* A package version is distinguished by name, version and index
* Add missing imports
* Check first layer of dependencies for validity
* Sanity check for adding non-locked version to lock
* Add testsuite for graph solver, dependency graph implementation
* Introduce graph Python solver
* Add testsuite for graph solver
* Introduce dependency graph
* Introduce graph Python solver
* reading README from file, its the long_description...
* Check for latest packages present on indexes
* Release of version 0.3.0
* fixing coala
* typo :/
* using thoth zuul jobs now
* Adjust setup.py to run testsuite correctly
* Run testsuite using setup.py
* Output to JSON in adviser
* Link PackageVersion to Source index used
* Report dict reporesentation of input instead of raw strings
* Add missing parameters to template
* Fix labels section in template
* Dependency monkey is a template
* Move dependency monkey to a job template
* Rename adviser template to be more clear
* Move from Pods to Jobs
* Directly pass adviser subcommand that should be run
* Introduce Dependency Monkey template
* Update README file
* Fix link to Thamos
* Introduce method for converting model to object
* Possible different source is info
* Add Codacy badge
* Fix testsuite respecting last changes
* Link to Pipenv docs for specifying package indexes
* Fix console figure
* State configured index in the report message
* Adjust reported issue id for possible different source
* Add installation section and adjust based on review comments
* Document provenance checks
* Quote relevant parts of string
* Add the current PyPI index to default warehouses
* Make artifact names lowercase by deafult
* Finish provenance reports
* Report directly findings in the provenance check report
* Adviser report should be always an array
* Report back error if we cannot conclude on application stack
* Ignore s2i's virtualenv in which adviser is run
* Increase memory for adviser due to OOMs
* Release of version 0.2.0
* Introduce add_source and add_package methods
* Do not use command in openshift template
* Release of version 0.1.1
* Setuptools find_packages does not respect namespaces
* Release of version 0.1.0
* Initial dependency lock
* Add forgotten lxml library for bs4 parsing
* Provide JanusGraph configuration in provenance-checker template
* Provide JanusGraph configuration in adviser template
* Pass full path to Python3 in s2i
* Make CLI executable
* Install forgotten packages
* Add execute bit to app.sh
* State we want to run provenance rather than adviser in template
* Revert "Provide entrypoint for OpenShift s2i"
* Provide a script to run desired subcommand
* Provide entrypoint for OpenShift s2i
* Remove unused script as adviser is s2i now
* Remove Dockerfile as adviser is s2i now
* Let's reuse parameter names from adviser
* Use local tensorflow index page for gathering versions
* Fix warehouse test
* Some CI fixes
* Initial dependency lock
* Let Kebechet pin down deps
* Remove old TODO
* Implement sorting based on semver
* Create abstraction classes
* Initial python recommendation implementation
* Automatic update of dependency thoth-common from 0.2.6 to 0.2.7
* Automatic update of dependency thoth-common from 0.2.5 to 0.2.6
* Introduce provenance checker template
* Automatic update of dependency thoth-storages from 0.5.1 to 0.5.2
* Automatic update of dependency thoth-common from 0.2.4 to 0.2.5
* Automatic update of dependency thoth-common from 0.2.3 to 0.2.4
* change the queue
* Automatic update of dependency thoth-common from 0.2.2 to 0.2.3
* Automatic update of dependency thoth-storages from 0.5.0 to 0.5.1
* Automatic update of dependency thoth-storages from 0.4.0 to 0.5.0
* Automatic update of dependency thoth-storages from 0.3.0 to 0.4.0
* Automatic update of dependency thoth-storages from 0.2.0 to 0.3.0
* Automatic update of dependency thoth-storages from 0.1.1 to 0.2.0
* State all template parameters
* Be consistent with label naming
* Update requirements.txt respecting requirements in Pipfile
* Automatic update of dependency thoth-common from 0.2.1 to 0.2.2
* Automatic update of dependency thoth-storages from 0.1.0 to 0.1.1
* Add app=thoth label to pod template
* Adjust template labels
* Fix image stream kind in template
* Fix coala naming convention configuration
* Add OpenShift templates for deployment
* Automatic update of dependency thoth-storages from 0.0.33 to 0.1.0
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Initial dependency lock
* Delete Pipfile.lock for relocking dependencies
* relocked, travis removed, zuul added
* Automatic update of dependency thoth-common from 0.0.9 to 0.1.0
* Automatic update of dependency thoth-analyzer from 0.0.6 to 0.0.7
* Automatic update of dependency thoth-analyzer from 0.0.5 to 0.0.6
* Automatic update of dependency thoth-storages from 0.0.32 to 0.0.33
* Automatic update of dependency thoth-storages from 0.0.29 to 0.0.32
* Automatic update of dependency thoth-common from 0.0.6 to 0.0.9
* Update thoth packageswq
* Automatic update of dependency thoth-storages from 0.0.25 to 0.0.28
* Do not restrict Thoth packages
* Another CI fix
* Another CI fix
* Run coala in non-interactive mode
* CI fix
* Run coala in CI
* Create OWNERS
* Remove dependencies.yml
* Use coala for code checks
* Fix package name in license header
* Add LICENSE and license headers
* Use thoth's common logging
* Add README file
* Version 0.0.2
* State only direct dependencies in requirements.txt
* Version 0.0.1
* Update dependencies
* Update thoth-storages from 0.0.3 to 0.0.4
* Rename environment variables to respect user-api arguments passing
* Create initial dependencies.yml config
* Change envvar for --requirements option
* Expose advise_pypi function
* Version 0.0.0
* Build adviser image in CI
* Fix naming typo
* Initial template for implementation
* Initial project import

## Release 0.7.1 (2020-01-13T09:33:26)
* Set random walk as default predictor for Dependency Monkey
* Inspection endpoint does not accept runtime environment
* Fix submitting inspections
* :pushpin: Automatic update of dependency thoth-storages from 0.21.2 to 0.21.3
* Add a boot that checks for fully specified environment
* Add ability to block pipeline units during pipeline build
* :pushpin: Automatic update of dependency thoth-storages from 0.21.1 to 0.21.2
* :pushpin: Automatic update of dependency thoth-storages from 0.21.0 to 0.21.1
* Bump template patch version
* Fix decision type environment variable name
* There is no option for DEPENDENDENCY_MONKEY_LIMIT
* :pushpin: Automatic update of dependency thoth-storages from 0.20.6 to 0.21.0
* Yield from iterator to keep context
* Add a note on requirements.txt
* State pip/pip-compile support in integration section
* Correct wrong key in template
* Adjust testsuite accordingly
* Sort direct dependencies for reproducible resolver runs
* :pushpin: Automatic update of dependency thoth-python from 0.9.0 to 0.9.1
* Do not prefer recent versions in random walk and sampling
* Optimize arithmetics a bit
* Be more explicit about the function call in docstring
* Use r""" if any backslashes in a docstring
* Introduce termial function to prefer more recent versions randomly
* Extend resolver testsuite
* :pushpin: Automatic update of dependency thoth-solver from 1.4.1 to 1.5.0
* Adjust env variable name
* :pushpin: Automatic update of dependency thoth-python from 0.8.0 to 0.9.0
* :pushpin: Automatic update of dependency thoth-storages from 0.20.5 to 0.20.6
* Boots can raise not acceptable
* Do not run adviser from bc in debug mode
* Do not run adviser from bc in debug mode
* Add testsuite for solved software environment pipeline unit
* Register solved software environment boot
* Sort reported environments
* Introduce solved software environment boot
* :pushpin: Automatic update of dependency thoth-storages from 0.20.4 to 0.20.5
* :pushpin: Automatic update of dependency thoth-python from 0.7.1 to 0.8.0
* :pushpin: Automatic update of dependency pytest-timeout from 1.3.3 to 1.3.4
* :pushpin: Automatic update of dependency pyyaml from 5.2 to 5.3
* :pushpin: Automatic update of dependency thoth-storages from 0.20.3 to 0.20.4
* :pushpin: Automatic update of dependency thoth-storages from 0.20.2 to 0.20.3
* Beam is part of context, no need to pass it explictly
* Fixed missing emptyDir in the Adviser Workflow
* Limit number of software stacks to 1 on LATEST
* Adjust testsuite to correctly propagate reward signal
* Introduce beam.reset()
* Introduce beam.get_random()
* Reward signal now accepts resolver context
* Remove environment serialization - it takes some time during runs
* Random walk and initial configuration change
* Fixed too many blank lines in Workflow template
* Fixed adviser Workflow template
* :pushpin: Automatic update of dependency thoth-storages from 0.20.1 to 0.20.2
* Happy new year!
* :pushpin: Automatic update of dependency thoth-storages from 0.20.0 to 0.20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.30 to 0.20.0
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.2 to 1.1.3
* :pushpin: Automatic update of dependency hypothesis from 4.57.0 to 4.57.1
* :pushpin: Automatic update of dependency hypothesis from 4.56.3 to 4.57.0
* Adjust documentation for the new predictor run API
* :pushpin: Automatic update of dependency hypothesis from 4.56.2 to 4.56.3
* :pushpin: Automatic update of dependency hypothesis from 4.56.1 to 4.56.2
* Predictors now return also packages that should be resolved from states
* Fix docstring of boot
* Add few more asserts
* Add tests for leaf node expansion with marker set to False
* Add a boot for mapping UBI to RHEL
* Exclude reports from run error in Sentry
* :pushpin: Automatic update of dependency hypothesis from 4.56.0 to 4.56.1
* :pushpin: Automatic update of dependency hypothesis from 4.55.4 to 4.56.0
* :pushpin: Automatic update of dependency hypothesis from 4.55.3 to 4.55.4
* :pushpin: Automatic update of dependency hypothesis from 4.55.2 to 4.55.3
* Add checks for special cases when environment markers apply to leaf nodes
* Register CVE step only for STABLE and TESTING recommendation types
* Automatically choose the most appropriate predictor based on CLI
* :sparkles: added an Argo Workflow to run an advise
* Adjust API and tests to the new change
* :see_no_evil: ignoring the xml report coverage file
* :pushpin: Automatic update of dependency thoth-storages from 0.19.27 to 0.19.30
* :pushpin: Automatic update of dependency hypothesis from 4.55.1 to 4.55.2
* Format using black
* Counter is no longer used
* Improve multi-key sorting of states in the beam
* Log warning about shared dependencies in the dependency graph
* :pushpin: Automatic update of dependency hypothesis from 4.55.0 to 4.55.1
* Do not retrieve markers during resolution
* Fix logging format expansion
* Log also beam size
* :pushpin: Automatic update of dependency hypothesis from 4.54.2 to 4.55.0
* Match only first part of tuple
* Fix computing top state in the beam
* Simplify creation of initial states
* Adjust relative order for steps registration
* :pushpin: Automatic update of dependency hypothesis from 4.54.1 to 4.54.2
* :pushpin: Automatic update of dependency hypothesis from 4.54.0 to 4.54.1
* Fix Coala complains
* Keep track of dependencies added
* Accepted final states can be 0
* Revert "Add new iteration method for sieves and steps"
* Make temperature function a function of iteration as well
* :pushpin: Automatic update of dependency hypothesis from 4.53.3 to 4.54.0
* :pushpin: Automatic update of dependency hypothesis from 4.53.2 to 4.53.3
* :pushpin: Automatic update of dependency pytest from 5.3.1 to 5.3.2
* Keep beam in context
* Implement a dropout step
* :pushpin: Automatic update of dependency hypothesis from 4.53.1 to 4.53.2
* Bump version in templates
* Fork only in the cluster
* Fix coala complains
* Document new iteration round methods
* Add new iteration method for sieves and steps
* Adjust docs for limit latest versions
* Always bind context
* Add tests for limit latest versions and semver sort
* Adjust test suite
* Adjust semantics of limit latest versions
* Add a note on shared dependencies
* Refactor plotting primitives
* Do not keep history if not plotting in CLI
* Rename and move history related bits in predictors
* Remove debug print
* Implement resolving stop when SIGINT is caught
* Use SIGINT in liveness probe
* Implement version clash boot
* Tests for hill climbing and sampling, minor refactoring
* Add locked sieve
* Beam width is stated two times
* Document OpenShift s2i build integration
* Fix issue when there are no unresolved dependencies left in the state
* Document beam width and how to plot it
* Document build-watcher
* Log correct file location for beam history plots
* :pushpin: Automatic update of dependency hypothesis from 4.53.0 to 4.53.1
* Document build-watcher
* :pushpin: Automatic update of dependency hypothesis from 4.52.0 to 4.53.0
* :pushpin: Automatic update of dependency hypothesis from 4.51.1 to 4.52.0
* :pushpin: Automatic update of dependency hypothesis from 4.51.0 to 4.51.1
* Add a link to Thamos documentation
* Point to Thamos documentation instead of GitHub repo
* Add a link to performance article published
* Add architecture diagram
* State also core repository
* docs: Architecture overview section
* :pushpin: Automatic update of dependency hypothesis from 4.50.8 to 4.51.0
* Remove graph cache bits no longer used
* Document pipeline configuration instrumentation
* Point documentation to other libraries
* Add developer's guide to documentation
* Use RHEL instead of UBI
* Update Thoth configuration file and Thoth's s2i configuration
* Remove old comment
* Add note to step docs - no adjustment in step or beam
* No need to clone a state before running steps
* Do not show not relevant logs to users
* Point to source code documentation for described methods
* Fix exit code propagation of the forked child
* Add validation of count and limit resolver attributes
* Produce more descriptive message if any of direct dependencies was not resolved
* :pushpin: Automatic update of dependency thoth-storages from 0.19.26 to 0.19.27
* Adjust parameters for adviser and dependency-monkey
* Propagate information about package that has CVE to justification in CVE step
* :pushpin: Automatic update of dependency hypothesis from 4.50.7 to 4.50.8
* :pushpin: Automatic update of dependency thoth-storages from 0.19.25 to 0.19.26
* :pushpin: Automatic update of dependency thoth-solver from 1.4.0 to 1.4.1
* Add Google Analytics
* Fix reference to sieve in docs
* Fix references to the source code
* Graph cache is not used anymore
* Fix coala complains

## Release 0.7.2 (2020-01-13T11:36:05)
* Release of version 0.7.1
* Set random walk as default predictor for Dependency Monkey
* Inspection endpoint does not accept runtime environment
* Fix submitting inspections
* :pushpin: Automatic update of dependency thoth-storages from 0.21.2 to 0.21.3
* Add a boot that checks for fully specified environment
* Add ability to block pipeline units during pipeline build
* :pushpin: Automatic update of dependency thoth-storages from 0.21.1 to 0.21.2
* :pushpin: Automatic update of dependency thoth-storages from 0.21.0 to 0.21.1
* Bump template patch version
* Fix decision type environment variable name
* There is no option for DEPENDENDENCY_MONKEY_LIMIT
* :pushpin: Automatic update of dependency thoth-storages from 0.20.6 to 0.21.0
* Yield from iterator to keep context
* Add a note on requirements.txt
* State pip/pip-compile support in integration section
* Correct wrong key in template
* Adjust testsuite accordingly
* Sort direct dependencies for reproducible resolver runs
* :pushpin: Automatic update of dependency thoth-python from 0.9.0 to 0.9.1
* Do not prefer recent versions in random walk and sampling
* Optimize arithmetics a bit
* Be more explicit about the function call in docstring
* Use r""" if any backslashes in a docstring
* Introduce termial function to prefer more recent versions randomly
* Extend resolver testsuite
* :pushpin: Automatic update of dependency thoth-solver from 1.4.1 to 1.5.0
* Adjust env variable name
* :pushpin: Automatic update of dependency thoth-python from 0.8.0 to 0.9.0
* :pushpin: Automatic update of dependency thoth-storages from 0.20.5 to 0.20.6
* Boots can raise not acceptable
* Do not run adviser from bc in debug mode
* Do not run adviser from bc in debug mode
* Add testsuite for solved software environment pipeline unit
* Register solved software environment boot
* Sort reported environments
* Introduce solved software environment boot
* :pushpin: Automatic update of dependency thoth-storages from 0.20.4 to 0.20.5
* :pushpin: Automatic update of dependency thoth-python from 0.7.1 to 0.8.0
* :pushpin: Automatic update of dependency pytest-timeout from 1.3.3 to 1.3.4
* :pushpin: Automatic update of dependency pyyaml from 5.2 to 5.3
* :pushpin: Automatic update of dependency thoth-storages from 0.20.3 to 0.20.4
* :pushpin: Automatic update of dependency thoth-storages from 0.20.2 to 0.20.3
* Beam is part of context, no need to pass it explictly
* Fixed missing emptyDir in the Adviser Workflow
* Limit number of software stacks to 1 on LATEST
* Adjust testsuite to correctly propagate reward signal
* Introduce beam.reset()
* Introduce beam.get_random()
* Reward signal now accepts resolver context
* Remove environment serialization - it takes some time during runs
* Random walk and initial configuration change
* Fixed too many blank lines in Workflow template
* Fixed adviser Workflow template
* :pushpin: Automatic update of dependency thoth-storages from 0.20.1 to 0.20.2
* Happy new year!
* :pushpin: Automatic update of dependency thoth-storages from 0.20.0 to 0.20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.30 to 0.20.0
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.2 to 1.1.3
* :pushpin: Automatic update of dependency hypothesis from 4.57.0 to 4.57.1
* :pushpin: Automatic update of dependency hypothesis from 4.56.3 to 4.57.0
* Adjust documentation for the new predictor run API
* :pushpin: Automatic update of dependency hypothesis from 4.56.2 to 4.56.3
* :pushpin: Automatic update of dependency hypothesis from 4.56.1 to 4.56.2
* Predictors now return also packages that should be resolved from states
* Fix docstring of boot
* Add few more asserts
* Add tests for leaf node expansion with marker set to False
* Add a boot for mapping UBI to RHEL
* Exclude reports from run error in Sentry
* :pushpin: Automatic update of dependency hypothesis from 4.56.0 to 4.56.1
* :pushpin: Automatic update of dependency hypothesis from 4.55.4 to 4.56.0
* :pushpin: Automatic update of dependency hypothesis from 4.55.3 to 4.55.4
* :pushpin: Automatic update of dependency hypothesis from 4.55.2 to 4.55.3
* Add checks for special cases when environment markers apply to leaf nodes
* Register CVE step only for STABLE and TESTING recommendation types
* Automatically choose the most appropriate predictor based on CLI
* :sparkles: added an Argo Workflow to run an advise
* Adjust API and tests to the new change
* :see_no_evil: ignoring the xml report coverage file
* :pushpin: Automatic update of dependency thoth-storages from 0.19.27 to 0.19.30
* :pushpin: Automatic update of dependency hypothesis from 4.55.1 to 4.55.2
* Format using black
* Counter is no longer used
* Improve multi-key sorting of states in the beam
* Log warning about shared dependencies in the dependency graph
* :pushpin: Automatic update of dependency hypothesis from 4.55.0 to 4.55.1
* Do not retrieve markers during resolution
* Fix logging format expansion
* Log also beam size
* :pushpin: Automatic update of dependency hypothesis from 4.54.2 to 4.55.0
* Match only first part of tuple
* Fix computing top state in the beam
* Simplify creation of initial states
* Adjust relative order for steps registration
* :pushpin: Automatic update of dependency hypothesis from 4.54.1 to 4.54.2
* :pushpin: Automatic update of dependency hypothesis from 4.54.0 to 4.54.1
* Fix Coala complains
* Keep track of dependencies added
* Accepted final states can be 0
* Revert "Add new iteration method for sieves and steps"
* Make temperature function a function of iteration as well
* :pushpin: Automatic update of dependency hypothesis from 4.53.3 to 4.54.0
* :pushpin: Automatic update of dependency hypothesis from 4.53.2 to 4.53.3
* :pushpin: Automatic update of dependency pytest from 5.3.1 to 5.3.2
* Keep beam in context
* Implement a dropout step
* :pushpin: Automatic update of dependency hypothesis from 4.53.1 to 4.53.2
* Bump version in templates
* Fork only in the cluster

## Release 0.7.3 (2020-01-14T20:20:14)
* Raise an error if no direct dependencies were found
* Report error on resolution failure
* Create more descriptive message
* Add tests for no dependencies cases during resolution
* Rebase and simplify code
* Fix log message reported
* Log interesting checkpoints during resolution to user
* Reward signal now propagates state for which the reward signal is computed
* Introduce a method for getting a state by its id
* Fix exception error messages produced
* Fix beam method signatures
* Remove unused import statement
* Introduce approximating latest predictor
* :pushpin: Automatic update of dependency thoth-storages from 0.21.5 to 0.21.6
* Re-add state with no unresolved dependencies back to beam on resolution
* Remvoe accidentally committed print statement
* Introduce finalizers for predictor's memory footprint optimization
* Predictor should pick key to beam
* Introduce assigned context to predictor
* Extend docs with MDP
* :pushpin: Automatic update of dependency thoth-storages from 0.21.4 to 0.21.5

## Release 0.8.0 (2020-03-17T13:22:23)
* Fix defaults in CLI, they are lowercase now
* Resolver does not check runtime environment specification during state resolving
* Add Python version boot
* Start using fext in adviser
* :pushpin: Automatic update of dependency pytest from 5.3.5 to 5.4.1
* :pushpin: Automatic update of dependency pytest-mypy from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency pyyaml from 5.3 to 3.13
* Adjust string for image and key
* Add registry env variables
* remove default values
* Generalize variables for Ceph for the workflows
* fixed coala
* Fixed error log and old api
* Prevent from OSError when the requirements string is too large
* :pushpin: Automatic update of dependency click from 7.0 to 7.1.1
* :pushpin: Automatic update of dependency click from 7.0 to 7.1.1
* :pushpin: Automatic update of dependency packaging from 20.1 to 20.3
* :pushpin: Automatic update of dependency matplotlib from 3.1.3 to 3.2.0
* Add voluptous to requirements.txt
* Introduce package source index sieve for filtering based on index
* Remove typeshed
* UBI boot has to be before boot that checks RHEL version
* Solved software environment has to be run after changes to environment
* Adjust testsuite
* Propagate the original runtime environment used in resolving in pipeline products
* Use the correct condition for checking parameters
* Increase timeout for pytest tests
* Fix test suite
* Ignore the run logger for dependency monkey runs
* Fix type
* Propagate metdata to products
* Allow context to be passed as a file
* Update thoth-storages to address import issue
* Update dependencies
* Propagate metdata to products
* Bump template version
* OpenShift templates are referenced by label
* Update dependencies
* Distinguish different types of errors of adviser runs for SLO
* Child exists with status code 256
* Do not overwrite results computed in the forked process
* Adviser workflow when using Thamos CLI
* Add URLs to GitHub and PyPI
* :pushpin: Automatic update of dependency hypothesis from 5.5.3 to 5.5.4
* :pushpin: Automatic update of dependency hypothesis from 5.5.2 to 5.5.3
* No deafult value null for metadata
* :pushpin: Automatic update of dependency hypothesis from 5.5.1 to 5.5.2
* :pushpin: Automatic update of dependency thoth-storages from 0.22.1 to 0.22.2
* Adjust version and use correct keys
* :pushpin: Automatic update of dependency thoth-storages from 0.22.0 to 0.22.1
* Add default value when user does not provided Pipfile.lock
* Add template for releases
* Revert to flexmock(GraphDatabase)
* GraphDatabase->graph
* follow python standards
* add more flex
* back to should receive after storages update
* :pushpin: Automatic update of dependency thoth-storages from 0.21.11 to 0.22.0
* Update .thoth.yaml
* change to should call
* initialize graph
* abi-compat-sieve tests
* :pushpin: Automatic update of dependency hypothesis from 5.4.2 to 5.5.1
* Run workflow even if adviser fails
* add env variable
* Use correct storage to store results
* State thoth-s2i in integration
* Propagate information about missing configuration in report
* Add a wrap for adding info about no observations
* Update docstring
* :pushpin: Automatic update of dependency hypothesis from 5.4.1 to 5.4.2
* Make decision type and recommendation type lowercase
* Modify parameters for GitHub App
* remove metadata
* Move cache to storage level
* cache query results
* shortcut if package requires no symbols
* self.image_symbols is now a set
* Create abi sieve
* Adjust script in finished webhook
* adjust script in finished webhook template
* remove service account argo
* Adjust inner workflow for GitHub App
* :pushpin: Automatic update of dependency hypothesis from 4.57.1 to 5.4.1
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.3 to 1.1.4
* :pushpin: Automatic update of dependency matplotlib from 3.1.2 to 3.1.3
* :pushpin: Automatic update of dependency pytest from 5.3.4 to 5.3.5
* Do identity check instead of equality check
* Capture CLI parameters in resolver's context
* :pushpin: Automatic update of dependency thoth-storages from 0.21.10 to 0.21.11
* Log information about future solver runs of unsolved dependencies
* Fix Coala complains
* Introduce normalization of score returned by step units
* Introduce RHEL version boot for RHEL major releases
* :pushpin: Automatic update of dependency packaging from 20.0 to 20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.21.9 to 0.21.10
* :pushpin: Automatic update of dependency thoth-storages from 0.21.8 to 0.21.9
* :pushpin: Automatic update of dependency pytest from 5.3.3 to 5.3.4
* :pushpin: Automatic update of dependency thoth-storages from 0.21.7 to 0.21.8
* Try its best to always come up with a latest stack
* Rename template for workflow-operator
* Disable dry run for Thoth's recommendations
* Fix a bug when env is not fully specified and env marker filters out deps
* :pushpin: Automatic update of dependency pytest from 5.3.2 to 5.3.3
* Do not show information about results being submitted to result API
* Use WARNING log level in thoth.common
* Ask for thoth.adviser log to have clean logs and respect log configuration
* Use epsilon greedy strategy for picking the latest version
* Adjust limit latest versions and beam width
* Introduce version constrain sieve pipeline unit
* Assign correct default value
* Do not keep history in adviser runs
* Fix default value key
* Add missing metadata to adviser job template
* Fix handling of --dry-run parameter
* Show version of direct dependencies explictly
* Include random decision stride only explictly
* Introduce stride for getting one version in a stack
* :pushpin: Automatic update of dependency thoth-storages from 0.21.6 to 0.21.7
* Move log_once to utils function
* Optimize state removal out of beam
* Terminal output is slow, log only after N stacks generated
* Optimize handling of the top score kept in beam
* Prevent annealing from being stuck
* Fix bug shown when sieves or steps filtered out dependecies
* Log stack counter in a more human readable form
* Propagate also expanded package tuple to reward signal
* Mention behavior for the default value
* Refactor keep history into an utility function for reusability
* Log pipeline speed
* did not save merge before merging
* add metadata

## Release 0.9.0 (2020-04-01T15:50:18)
* Fix info message causing issues when the beam is empty
* Add fext to application requirements
* Remove unusued parameter
* Re-enable fext for beam's internal state handling
* consistency in openshift templates to run provenance
* :pushpin: Automatic update of dependency pyyaml from 3.13 to 5.3.1
* Introduce heat up part of MCTS
* Prioritize releases by AICoE
* :pushpin: Automatic update of dependency thoth-solver from 1.5.0 to 1.5.1
* :pushpin: Automatic update of dependency thoth-storages from 0.22.6 to 0.22.7
* Do not keep beam history if not necessary
* :pushpin: Automatic update of dependency thoth-storages from 0.22.5 to 0.22.6
* Add option consider/do not consider dev dependencies
* Increase timeout for running tests
* Increase timeout for running tests
* No need to initialize logging multiple times
* Minor fixes in api_compat
* Use MCTS predictor for stable and testing recommendations
* Optimize termial of n computation
* Fix scoring of the user stack
* Optimize termial of n computation
* Address issues spotted in resolution when MCTS is used
* Document provenance checks
* :pushpin: Automatic update of dependency pyyaml from 5.3.1 to 3.13
* Fix context handling when passing in as raw JSON
* Fix dependency monkey invocation flag
* :pushpin: Automatic update of dependency hypothesis from 5.7.2 to 5.8.0
* :pushpin: Automatic update of dependency hypothesis from 5.7.1 to 5.7.2
* :pushpin: Automatic update of dependency pyyaml from 3.13 to 5.3.1
* Log resolver progress each 10%
* :pushpin: Automatic update of dependency hypothesis from 5.7.0 to 5.7.1
* Missing parenthesis prevent sync on Ceph
* Test suite and duplicate code refactoring
* Fix docstring
* Updates to the new beam API
* Reduce memory footprint
* Implement MCTS predictor
* Additional changes for TD
* Fix annealing testsuite
* Introduce Temporal Difference based predictor using annealing based scheduling
* Fix coala complains
* Introduce user stack scoring as a base for comparision
* Make sure the error report for adviser exceptions is always present
* :pushpin: Automatic update of dependency thoth-storages from 0.22.4 to 0.22.5
* :pushpin: Automatic update of dependency thoth-storages from 0.22.3 to 0.22.4
* Rewrite beam so that it does not use fext
* Wrong variable name
* :pushpin: Automatic update of dependency hypothesis from 5.6.1 to 5.7.0
* :pushpin: Automatic update of dependency hypothesis from 5.6.0 to 5.6.1
* :pushpin: Automatic update of dependency matplotlib from 3.2.0 to 3.2.1
* Correct space for exception
* Fix handling of environment markers when multiple packages use marker

## Release 0.9.1 (2020-04-01T19:57:10)
* Fix bug causing adviser halt for shared resolved packages

## Release 0.9.2 (2020-04-02T23:08:59)
* Fixes needed to make this package available on PyPI
* Tweak temperature function for ASA, TD and MCTS
* Adjust parameters in deployment

## Release 0.9.3 (2020-04-03T00:49:33)
* Release of version 0.9.2
* Fixes needed to make this package available on PyPI
* Tweak temperature function for ASA, TD and MCTS
* Adjust parameters in deployment
* Release of version 0.9.1
* Fix bug causing adviser halt for shared resolved packages
* Release of version 0.9.0
* Fix info message causing issues when the beam is empty
* Add fext to application requirements
* Remove unusued parameter
* Re-enable fext for beam's internal state handling
* consistency in openshift templates to run provenance
* :pushpin: Automatic update of dependency pyyaml from 3.13 to 5.3.1
* Introduce heat up part of MCTS
* Prioritize releases by AICoE
* :pushpin: Automatic update of dependency thoth-solver from 1.5.0 to 1.5.1
* :pushpin: Automatic update of dependency thoth-storages from 0.22.6 to 0.22.7
* Do not keep beam history if not necessary
* :pushpin: Automatic update of dependency thoth-storages from 0.22.5 to 0.22.6
* Add option consider/do not consider dev dependencies
* Increase timeout for running tests
* Increase timeout for running tests
* No need to initialize logging multiple times
* Minor fixes in api_compat
* Use MCTS predictor for stable and testing recommendations
* Optimize termial of n computation
* Fix scoring of the user stack
* Optimize termial of n computation
* Address issues spotted in resolution when MCTS is used
* Document provenance checks
* :pushpin: Automatic update of dependency pyyaml from 5.3.1 to 3.13
* Fix context handling when passing in as raw JSON
* Fix dependency monkey invocation flag
* :pushpin: Automatic update of dependency hypothesis from 5.7.2 to 5.8.0
* :pushpin: Automatic update of dependency hypothesis from 5.7.1 to 5.7.2
* :pushpin: Automatic update of dependency pyyaml from 3.13 to 5.3.1
* Log resolver progress each 10%
* :pushpin: Automatic update of dependency hypothesis from 5.7.0 to 5.7.1
* Missing parenthesis prevent sync on Ceph
* Test suite and duplicate code refactoring
* Fix docstring
* Updates to the new beam API
* Reduce memory footprint
* Implement MCTS predictor
* Additional changes for TD
* Fix annealing testsuite
* Introduce Temporal Difference based predictor using annealing based scheduling
* Fix coala complains
* Introduce user stack scoring as a base for comparision
* Make sure the error report for adviser exceptions is always present
* :pushpin: Automatic update of dependency thoth-storages from 0.22.4 to 0.22.5
* :pushpin: Automatic update of dependency thoth-storages from 0.22.3 to 0.22.4
* Rewrite beam so that it does not use fext
* Wrong variable name
* :pushpin: Automatic update of dependency hypothesis from 5.6.1 to 5.7.0
* :pushpin: Automatic update of dependency hypothesis from 5.6.0 to 5.6.1
* :pushpin: Automatic update of dependency matplotlib from 3.2.0 to 3.2.1
* Correct space for exception
* Fix handling of environment markers when multiple packages use marker
* Release of version 0.8.0
* Fix defaults in CLI, they are lowercase now
* Resolver does not check runtime environment specification during state resolving
* Add Python version boot
* Start using fext in adviser
* :pushpin: Automatic update of dependency pytest from 5.3.5 to 5.4.1
* :pushpin: Automatic update of dependency pytest-mypy from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency pyyaml from 5.3 to 3.13
* Adjust string for image and key
* Add registry env variables
* remove default values
* Generalize variables for Ceph for the workflows
* fixed coala
* Fixed error log and old api
* Prevent from OSError when the requirements string is too large
* :pushpin: Automatic update of dependency click from 7.0 to 7.1.1
* :pushpin: Automatic update of dependency click from 7.0 to 7.1.1
* :pushpin: Automatic update of dependency packaging from 20.1 to 20.3
* :pushpin: Automatic update of dependency matplotlib from 3.1.3 to 3.2.0
* Add voluptous to requirements.txt
* Introduce package source index sieve for filtering based on index
* Remove typeshed
* UBI boot has to be before boot that checks RHEL version
* Solved software environment has to be run after changes to environment
* Adjust testsuite
* Propagate the original runtime environment used in resolving in pipeline products
* Use the correct condition for checking parameters
* Increase timeout for pytest tests
* Fix test suite
* Ignore the run logger for dependency monkey runs
* Fix type
* Propagate metdata to products
* Allow context to be passed as a file
* Update thoth-storages to address import issue
* Update dependencies
* Propagate metdata to products
* Bump template version
* OpenShift templates are referenced by label
* Update dependencies
* Distinguish different types of errors of adviser runs for SLO
* Child exists with status code 256
* Do not overwrite results computed in the forked process
* Adviser workflow when using Thamos CLI
* Add URLs to GitHub and PyPI
* :pushpin: Automatic update of dependency hypothesis from 5.5.3 to 5.5.4
* :pushpin: Automatic update of dependency hypothesis from 5.5.2 to 5.5.3
* No deafult value null for metadata
* :pushpin: Automatic update of dependency hypothesis from 5.5.1 to 5.5.2
* :pushpin: Automatic update of dependency thoth-storages from 0.22.1 to 0.22.2
* Adjust version and use correct keys
* :pushpin: Automatic update of dependency thoth-storages from 0.22.0 to 0.22.1
* Add default value when user does not provided Pipfile.lock
* Add template for releases
* Revert to flexmock(GraphDatabase)
* GraphDatabase->graph
* follow python standards
* add more flex
* back to should receive after storages update
* :pushpin: Automatic update of dependency thoth-storages from 0.21.11 to 0.22.0
* Update .thoth.yaml
* change to should call
* initialize graph
* abi-compat-sieve tests
* :pushpin: Automatic update of dependency hypothesis from 5.4.2 to 5.5.1
* Run workflow even if adviser fails
* add env variable
* Use correct storage to store results
* State thoth-s2i in integration
* Propagate information about missing configuration in report
* Add a wrap for adding info about no observations
* Update docstring
* :pushpin: Automatic update of dependency hypothesis from 5.4.1 to 5.4.2
* Make decision type and recommendation type lowercase
* Modify parameters for GitHub App
* remove metadata
* Move cache to storage level
* cache query results
* shortcut if package requires no symbols
* self.image_symbols is now a set
* Create abi sieve
* Adjust script in finished webhook
* adjust script in finished webhook template
* remove service account argo
* Adjust inner workflow for GitHub App
* :pushpin: Automatic update of dependency hypothesis from 4.57.1 to 5.4.1
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.3 to 1.1.4
* :pushpin: Automatic update of dependency matplotlib from 3.1.2 to 3.1.3
* :pushpin: Automatic update of dependency pytest from 5.3.4 to 5.3.5
* Do identity check instead of equality check
* Capture CLI parameters in resolver's context
* :pushpin: Automatic update of dependency thoth-storages from 0.21.10 to 0.21.11
* Log information about future solver runs of unsolved dependencies
* Fix Coala complains
* Introduce normalization of score returned by step units
* Introduce RHEL version boot for RHEL major releases
* :pushpin: Automatic update of dependency packaging from 20.0 to 20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.21.9 to 0.21.10
* :pushpin: Automatic update of dependency thoth-storages from 0.21.8 to 0.21.9
* :pushpin: Automatic update of dependency pytest from 5.3.3 to 5.3.4
* :pushpin: Automatic update of dependency thoth-storages from 0.21.7 to 0.21.8
* Try its best to always come up with a latest stack
* Rename template for workflow-operator
* Disable dry run for Thoth's recommendations
* Fix a bug when env is not fully specified and env marker filters out deps
* :pushpin: Automatic update of dependency pytest from 5.3.2 to 5.3.3
* Do not show information about results being submitted to result API
* Use WARNING log level in thoth.common
* Ask for thoth.adviser log to have clean logs and respect log configuration
* Use epsilon greedy strategy for picking the latest version
* Adjust limit latest versions and beam width
* Introduce version constrain sieve pipeline unit
* Assign correct default value
* Do not keep history in adviser runs
* Fix default value key
* Add missing metadata to adviser job template
* Fix handling of --dry-run parameter
* Show version of direct dependencies explictly
* Include random decision stride only explictly
* Introduce stride for getting one version in a stack
* :pushpin: Automatic update of dependency thoth-storages from 0.21.6 to 0.21.7
* Move log_once to utils function
* Optimize state removal out of beam
* Terminal output is slow, log only after N stacks generated
* Optimize handling of the top score kept in beam
* Prevent annealing from being stuck
* Fix bug shown when sieves or steps filtered out dependecies
* Log stack counter in a more human readable form
* Propagate also expanded package tuple to reward signal
* Mention behavior for the default value
* Refactor keep history into an utility function for reusability
* Log pipeline speed
* Release of version 0.7.3
* Raise an error if no direct dependencies were found
* Report error on resolution failure
* Create more descriptive message
* Add tests for no dependencies cases during resolution
* Rebase and simplify code
* Fix log message reported
* Log interesting checkpoints during resolution to user
* Reward signal now propagates state for which the reward signal is computed
* Introduce a method for getting a state by its id
* Fix exception error messages produced
* Fix beam method signatures
* Remove unused import statement
* Introduce approximating latest predictor
* :pushpin: Automatic update of dependency thoth-storages from 0.21.5 to 0.21.6
* Re-add state with no unresolved dependencies back to beam on resolution
* Remvoe accidentally committed print statement
* Introduce finalizers for predictor's memory footprint optimization
* Predictor should pick key to beam
* Introduce assigned context to predictor
* Extend docs with MDP
* :pushpin: Automatic update of dependency thoth-storages from 0.21.4 to 0.21.5
* Release of version 0.7.2
* :pushpin: Automatic update of dependency thoth-storages from 0.21.3 to 0.21.4
* Release of version 0.7.1
* Set random walk as default predictor for Dependency Monkey
* Inspection endpoint does not accept runtime environment
* Fix submitting inspections
* :pushpin: Automatic update of dependency thoth-storages from 0.21.2 to 0.21.3
* Add a boot that checks for fully specified environment
* Add ability to block pipeline units during pipeline build
* :pushpin: Automatic update of dependency thoth-storages from 0.21.1 to 0.21.2
* :pushpin: Automatic update of dependency thoth-storages from 0.21.0 to 0.21.1
* Bump template patch version
* Fix decision type environment variable name
* There is no option for DEPENDENDENCY_MONKEY_LIMIT
* :pushpin: Automatic update of dependency thoth-storages from 0.20.6 to 0.21.0
* did not save merge before merging
* Yield from iterator to keep context
* Add a note on requirements.txt
* State pip/pip-compile support in integration section
* Correct wrong key in template
* Adjust testsuite accordingly
* Sort direct dependencies for reproducible resolver runs
* :pushpin: Automatic update of dependency thoth-python from 0.9.0 to 0.9.1
* Do not prefer recent versions in random walk and sampling
* Optimize arithmetics a bit
* Be more explicit about the function call in docstring
* Use r""" if any backslashes in a docstring
* Introduce termial function to prefer more recent versions randomly
* Extend resolver testsuite
* :pushpin: Automatic update of dependency thoth-solver from 1.4.1 to 1.5.0
* Adjust env variable name
* :pushpin: Automatic update of dependency thoth-python from 0.8.0 to 0.9.0
* :pushpin: Automatic update of dependency thoth-storages from 0.20.5 to 0.20.6
* Boots can raise not acceptable
* Do not run adviser from bc in debug mode
* Do not run adviser from bc in debug mode
* Add testsuite for solved software environment pipeline unit
* Register solved software environment boot
* Sort reported environments
* Introduce solved software environment boot
* :pushpin: Automatic update of dependency thoth-storages from 0.20.4 to 0.20.5
* :pushpin: Automatic update of dependency thoth-python from 0.7.1 to 0.8.0
* :pushpin: Automatic update of dependency pytest-timeout from 1.3.3 to 1.3.4
* :pushpin: Automatic update of dependency pyyaml from 5.2 to 5.3
* :pushpin: Automatic update of dependency thoth-storages from 0.20.3 to 0.20.4
* :pushpin: Automatic update of dependency thoth-storages from 0.20.2 to 0.20.3
* Beam is part of context, no need to pass it explictly
* Fixed missing emptyDir in the Adviser Workflow
* Limit number of software stacks to 1 on LATEST
* Adjust testsuite to correctly propagate reward signal
* Introduce beam.reset()
* Introduce beam.get_random()
* Reward signal now accepts resolver context
* Remove environment serialization - it takes some time during runs
* Random walk and initial configuration change
* Fixed too many blank lines in Workflow template
* Fixed adviser Workflow template
* :pushpin: Automatic update of dependency thoth-storages from 0.20.1 to 0.20.2
* Happy new year!
* :pushpin: Automatic update of dependency thoth-storages from 0.20.0 to 0.20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.30 to 0.20.0
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.2 to 1.1.3
* :pushpin: Automatic update of dependency hypothesis from 4.57.0 to 4.57.1
* :pushpin: Automatic update of dependency hypothesis from 4.56.3 to 4.57.0
* Adjust documentation for the new predictor run API
* :pushpin: Automatic update of dependency hypothesis from 4.56.2 to 4.56.3
* :pushpin: Automatic update of dependency hypothesis from 4.56.1 to 4.56.2
* Predictors now return also packages that should be resolved from states
* Fix docstring of boot
* Add few more asserts
* Add tests for leaf node expansion with marker set to False
* Add a boot for mapping UBI to RHEL
* Exclude reports from run error in Sentry
* :pushpin: Automatic update of dependency hypothesis from 4.56.0 to 4.56.1
* :pushpin: Automatic update of dependency hypothesis from 4.55.4 to 4.56.0
* :pushpin: Automatic update of dependency hypothesis from 4.55.3 to 4.55.4
* :pushpin: Automatic update of dependency hypothesis from 4.55.2 to 4.55.3
* Add checks for special cases when environment markers apply to leaf nodes
* Register CVE step only for STABLE and TESTING recommendation types
* Automatically choose the most appropriate predictor based on CLI
* :sparkles: added an Argo Workflow to run an advise
* Adjust API and tests to the new change
* :see_no_evil: ignoring the xml report coverage file
* :pushpin: Automatic update of dependency thoth-storages from 0.19.27 to 0.19.30
* :pushpin: Automatic update of dependency hypothesis from 4.55.1 to 4.55.2
* Format using black
* Counter is no longer used
* Improve multi-key sorting of states in the beam
* Log warning about shared dependencies in the dependency graph
* :pushpin: Automatic update of dependency hypothesis from 4.55.0 to 4.55.1
* Do not retrieve markers during resolution
* Fix logging format expansion
* Log also beam size
* :pushpin: Automatic update of dependency hypothesis from 4.54.2 to 4.55.0
* Match only first part of tuple
* Fix computing top state in the beam
* Simplify creation of initial states
* Adjust relative order for steps registration
* :pushpin: Automatic update of dependency hypothesis from 4.54.1 to 4.54.2
* :pushpin: Automatic update of dependency hypothesis from 4.54.0 to 4.54.1
* Fix Coala complains
* Keep track of dependencies added
* Accepted final states can be 0
* Revert "Add new iteration method for sieves and steps"
* Make temperature function a function of iteration as well
* :pushpin: Automatic update of dependency hypothesis from 4.53.3 to 4.54.0
* :pushpin: Automatic update of dependency hypothesis from 4.53.2 to 4.53.3
* :pushpin: Automatic update of dependency pytest from 5.3.1 to 5.3.2
* Keep beam in context
* Implement a dropout step
* :pushpin: Automatic update of dependency hypothesis from 4.53.1 to 4.53.2
* Bump version in templates
* Fork only in the cluster
* Fix coala complains
* Document new iteration round methods
* Add new iteration method for sieves and steps
* Adjust docs for limit latest versions
* Always bind context
* Add tests for limit latest versions and semver sort
* Adjust test suite
* Adjust semantics of limit latest versions
* Add a note on shared dependencies
* Refactor plotting primitives
* Do not keep history if not plotting in CLI
* Rename and move history related bits in predictors
* Remove debug print
* Implement resolving stop when SIGINT is caught
* Use SIGINT in liveness probe
* Implement version clash boot
* Tests for hill climbing and sampling, minor refactoring
* Add locked sieve
* Beam width is stated two times
* Document OpenShift s2i build integration
* Fix issue when there are no unresolved dependencies left in the state
* Document beam width and how to plot it
* Document build-watcher
* Log correct file location for beam history plots
* :pushpin: Automatic update of dependency hypothesis from 4.53.0 to 4.53.1
* Document build-watcher
* :pushpin: Automatic update of dependency hypothesis from 4.52.0 to 4.53.0
* :pushpin: Automatic update of dependency hypothesis from 4.51.1 to 4.52.0
* :pushpin: Automatic update of dependency hypothesis from 4.51.0 to 4.51.1
* Add a link to Thamos documentation
* Point to Thamos documentation instead of GitHub repo
* Add a link to performance article published
* Add architecture diagram
* State also core repository
* docs: Architecture overview section
* :pushpin: Automatic update of dependency hypothesis from 4.50.8 to 4.51.0
* Remove graph cache bits no longer used
* Document pipeline configuration instrumentation
* Point documentation to other libraries
* Add developer's guide to documentation
* Use RHEL instead of UBI
* Update Thoth configuration file and Thoth's s2i configuration
* Remove old comment
* Add note to step docs - no adjustment in step or beam
* No need to clone a state before running steps
* Do not show not relevant logs to users
* Point to source code documentation for described methods
* Fix exit code propagation of the forked child
* Add validation of count and limit resolver attributes
* Produce more descriptive message if any of direct dependencies was not resolved
* :pushpin: Automatic update of dependency thoth-storages from 0.19.26 to 0.19.27
* Adjust parameters for adviser and dependency-monkey
* Propagate information about package that has CVE to justification in CVE step
* :pushpin: Automatic update of dependency hypothesis from 4.50.7 to 4.50.8
* :pushpin: Automatic update of dependency thoth-storages from 0.19.25 to 0.19.26
* :pushpin: Automatic update of dependency thoth-solver from 1.4.0 to 1.4.1
* Add Google Analytics
* Fix reference to sieve in docs
* Fix references to the source code
* Release of version 0.7.0
* :pushpin: Automatic update of dependency hypothesis from 4.50.6 to 4.50.7
* Graph cache is not used anymore
* Fix coala complains
* Enhance exception
* Give more information dependencies were not resolved
* Set beam width template in the adviser template job
* Fix coala complains
* Fix coala complains
* Some docs for readers and developers
* Fix stride signature
* Fix boot docstring
* Fix tests
* Optimizations of beam
* Fix Coala complains
* Use generators to retrieve items
* Provide property for run executor that prints report
* Provide an option to configure pipeline via file/dict
* Log package version before pipeline step execution
* Remove unused method
* Test simulated annealing primitives, refactor core annealing part
* Step should not return Nan/Inf
* Use backtracking to run steps
* Make coala happy again
* Add tests for two corner cases for package clash during resolution
* Fix beam top manipulation
* Add logic for registering a final state
* Add dependencies only if they were previously considered based on env marker
* Remove print used during debugging
* :pushpin: Automatic update of dependency hypothesis from 4.50.5 to 4.50.6
* :pushpin: Automatic update of dependency hypothesis from 4.50.4 to 4.50.5
* :pushpin: Automatic update of dependency hypothesis from 4.50.3 to 4.50.4
* :pushpin: Automatic update of dependency hypothesis from 4.50.2 to 4.50.3
* Change default number of stacks returned on call
* Fix parameter to adviser CLI
* Adjust logged messages
* Make beam instance of resolver
* Adjust limit latest versions signature, do not perform shallow copy
* Sieve now accepts and returns a generator of package versions
* :pushpin: Automatic update of dependency thoth-storages from 0.19.24 to 0.19.25
* Address review comments
* :pushpin: Automatic update of dependency hypothesis from 4.50.1 to 4.50.2
* Fix coala issues
* Fix typo in docstring
* :pushpin: Automatic update of dependency hypothesis from 4.50.0 to 4.50.1
* :pushpin: Automatic update of dependency hypothesis from 4.49.0 to 4.50.0
* Optimize retrieval of environment markers
* :pushpin: Automatic update of dependency hypothesis from 4.48.0 to 4.49.0
* :pushpin: Automatic update of dependency hypothesis from 4.47.4 to 4.48.0
* Even more tests
* :pushpin: Automatic update of dependency hypothesis from 4.47.3 to 4.47.4
* Propagate document id into jobs
* More tests
* :pushpin: Automatic update of dependency hypothesis from 4.47.2 to 4.47.3
* :pushpin: Automatic update of dependency pytest from 5.3.0 to 5.3.1
* :pushpin: Automatic update of dependency hypothesis from 4.47.1 to 4.47.2
* :pushpin: Automatic update of dependency hypothesis from 4.47.0 to 4.47.1
* :pushpin: Automatic update of dependency hypothesis from 4.46.1 to 4.47.0
* :pushpin: Automatic update of dependency hypothesis from 4.46.0 to 4.46.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.23 to 0.19.24
* :pushpin: Automatic update of dependency hypothesis from 4.45.1 to 4.46.0
* :pushpin: Automatic update of dependency matplotlib from 3.1.1 to 3.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.22 to 0.19.23
* Remove unused imports
* :pushpin: Automatic update of dependency hypothesis from 4.45.0 to 4.45.1
* :pushpin: Automatic update of dependency hypothesis from 4.44.4 to 4.45.0
* :pushpin: Automatic update of dependency hypothesis from 4.44.2 to 4.44.4
* :pushpin: Automatic update of dependency pytest from 5.2.4 to 5.3.0
* :pushpin: Automatic update of dependency thoth-storages from 0.19.21 to 0.19.22
* :pushpin: Automatic update of dependency thoth-storages from 0.19.19 to 0.19.21
* Bump library versions
* Fix hashes representation in the generated Pipfile.lock
* Remove score filter stride
* Remove Dgraph leftovers
* Hotfix for obtained hashes
* Minor typo fixes
* Notify when a new pipeline product was produced
* Notify user when computing recommendations
* Update dependencies
* :pushpin: Automatic update of dependency thoth-storages from 0.19.18 to 0.19.19
* Fix coala complains
* Plotting environment variables were renamed
* Split adviser implementation for extensibility and testing
* :pushpin: Automatic update of dependency hypothesis from 4.44.1 to 4.44.2
* :pushpin: Automatic update of dependency hypothesis from 4.44.0 to 4.44.1
* :pushpin: Automatic update of dependency hypothesis from 4.43.8 to 4.44.0
* Add missing modules
* :pushpin: Automatic update of dependency thoth-storages from 0.19.17 to 0.19.18
* Update dependencies for new API
* :pushpin: Automatic update of dependency hypothesis from 4.43.6 to 4.43.8
* New thoth-python uses packaging's Version with different API
* Remove old test - solver does not support latest versions anymore
* Fix coala issues - reformat using black
* Use new solver implementation
* Update README to show how to run adviser locally
* :pushpin: Automatic update of dependency hypothesis from 4.43.5 to 4.43.6
* :pushpin: Automatic update of dependency thoth-storages from 0.19.15 to 0.19.17
* Adjust provenance-checker output to be in alaign with adviser and dm
* Revert "runtime_environment var should be dict in parameter"
* Fix exit code propagation to the main process
* runtime_environment var should be dict in parameter
* Release of version 0.6.1
* :pushpin: Automatic update of dependency hypothesis from 4.43.4 to 4.43.5
* :pushpin: Automatic update of dependency hypothesis from 4.43.3 to 4.43.4
* :pushpin: Automatic update of dependency hypothesis from 4.43.2 to 4.43.3
* Cache queries for retrieving enabled indexes
* :pushpin: Automatic update of dependency hypothesis from 4.43.1 to 4.43.2
* Use slots on pipeline unit instances
* Fix resolving direct dependencies when pagination is used
* :pushpin: Automatic update of dependency thoth-storages from 0.19.14 to 0.19.15
* :pushpin: Automatic update of dependency hypothesis from 4.43.0 to 4.43.1
* :pushpin: Automatic update of dependency hypothesis from 4.42.10 to 4.43.0
* :pushpin: Automatic update of dependency pytest-mypy from 0.4.1 to 0.4.2
* :pushpin: Automatic update of dependency hypothesis from 4.42.9 to 4.42.10
* :pushpin: Automatic update of dependency hypothesis from 4.42.8 to 4.42.9
* :pushpin: Automatic update of dependency hypothesis from 4.42.7 to 4.42.8
* :pushpin: Automatic update of dependency hypothesis from 4.42.6 to 4.42.7
* :pushpin: Automatic update of dependency hypothesis from 4.42.5 to 4.42.6
* :pushpin: Automatic update of dependency hypothesis from 4.42.4 to 4.42.5
* Release of version 0.6.0
* :pushpin: Automatic update of dependency hypothesis from 4.42.0 to 4.42.4
* Start using adaptive simulated annealing
* Release of version 0.6.0
* Use THOTH_ADVISE variable for consistency
* updated templates with annotations and param thoth-advise-value
* :pushpin: Automatic update of dependency methodtools from 0.1.1 to 0.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.11 to 0.19.12
* Do not use cached adviser
* :pushpin: Automatic update of dependency thoth-storages from 0.19.10 to 0.19.11
* :pushpin: Automatic update of dependency pytest from 5.2.1 to 5.2.2
* :pushpin: Automatic update of dependency methodtools from 0.1.0 to 0.1.1
* Pin thoth libraries which will have incompatible release
* :pushpin: Automatic update of dependency thoth-python from 0.6.4 to 0.6.5
* :pushpin: Automatic update of dependency pylint from 2.4.2 to 2.4.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.9 to 0.19.10
* :pushpin: Automatic update of dependency thoth-python from 0.6.3 to 0.6.4
* Add spaces to fix toml issues
* :pushpin: Automatic update of dependency thoth-common from 0.9.12 to 0.9.14
* :pushpin: Automatic update of dependency thoth-common from 0.9.11 to 0.9.12
* :pushpin: Automatic update of dependency pytest from 5.2.0 to 5.2.1
* :pushpin: Automatic update of dependency pytest-cov from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency pytest-cov from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency thoth-common from 0.9.10 to 0.9.11
* :pushpin: Automatic update of dependency pylint from 2.4.1 to 2.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.8 to 0.19.9
* :pushpin: Automatic update of dependency pytest from 5.1.3 to 5.2.0
* Fix duration
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.3 to 0.1.4
* :pushpin: Automatic update of dependency thoth-storages from 0.19.7 to 0.19.8
* Fix duration calculation
* Add duration to Adviser
* Re-anable operating system sieve
* Check we do not raise exception if os sieve wants to filter out all packages
* Introduce sieve for limiting number of latest versions in direct dependencies
* Add a new sieve for limiting pre-releases in direct dependencies
* Introduce semver sorting on direct dependnecies - sieve
* Just a minor change to make code great again
* :pushpin: Automatic update of dependency pylint from 2.4.0 to 2.4.1
* Introduce a stable sorting of packages in sieve context
* :pushpin: Automatic update of dependency thoth-storages from 0.19.6 to 0.19.7
* :pushpin: Automatic update of dependency pylint from 2.3.1 to 2.4.0
* use postgresql hostname from thoth configmap
* Add check for upstream tensorflow parsing
* :pushpin: Automatic update of dependency thoth-python from 0.6.2 to 0.6.3
* Adjust os sieve testsuite to reflect changes
* Introduce tests for checking correct parsing of AICoE releases
* :pushpin: Automatic update of dependency thoth-storages from 0.19.5 to 0.19.6
* :pushpin: Automatic update of dependency pytest from 5.1.2 to 5.1.3
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.2 to 0.1.3
* Add seldon and seldon-core to cached packages
* Create a check and test case to handle errors when trying to resolve unsolved packages
* :pushpin: Automatic update of dependency thoth-common from 0.9.9 to 0.9.10
* :pushpin: Automatic update of dependency thoth-storages from 0.19.4 to 0.19.5
* :pushpin: Automatic update of dependency thoth-common from 0.9.8 to 0.9.9
* Corrected typos
* :pushpin: Automatic update of dependency thoth-storages from 0.19.3 to 0.19.4
* Add Sentry DSN to build of adviser-cached
* :pushpin: Automatic update of dependency thoth-storages from 0.19.2 to 0.19.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.1 to 0.19.2
* Propagate deployment name to have reports when cache is built
* Propagate deployment name for sentry environment
* :pushpin: Automatic update of dependency thoth-storages from 0.19.0 to 0.19.1
* Fix testsuite
* Make coala happy
* Fix indentation issues
* Relock requirements
* Fix exception message
* Print out packages before each pipeline unit
* Implement solved sieve
* Changes needed for PostgreSQL migration
* Add a pipeline step which removes unsolved packages
* Do not use -e flag
* Store and restore cache on builds
* Add more packages to cache config file
* Adjust cache not to cache graph database adapter
* Create adviser cache during container build
* :pushpin: Automatic update of dependency thoth-python from 0.6.1 to 0.6.2
* :pushpin: Automatic update of dependency thoth-storages from 0.18.6 to 0.19.0
* Propagate runtime environment explicitly
* Use more generic env var names
* Remove performance related tests
* Drop generic performance querying
* Start using PostgreSQL in deployment
* :pushpin: Automatic update of dependency semantic-version from 2.8.1 to 2.8.2
* :pushpin: Automatic update of dependency pytest from 5.1.1 to 5.1.2
* :pushpin: Automatic update of dependency semantic-version from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency semantic-version from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency semantic-version from 2.7.0 to 2.7.1
* :pushpin: Automatic update of dependency semantic-version from 2.6.0 to 2.7.0
* Turn error into warning
* :pushpin: Automatic update of dependency pytest from 5.1.0 to 5.1.1
* Improve error message reported if no releases were found
* State how to integrate with Thoth in docs
* Do not use setuptools.find_namespace_packages() for now
* Start using Thoth's s2i base image
* Fix missing packages in adviser's package
* :pushpin: Automatic update of dependency pytest from 5.0.1 to 5.1.0
* :pushpin: Automatic update of dependency pydocstyle from 4.0.0 to 4.0.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.5 to 0.18.6
* :pushpin: Automatic update of dependency thoth-common from 0.9.7 to 0.9.8
* :pushpin: Automatic update of dependency thoth-common from 0.9.6 to 0.9.7
* Document how to make changes in the dependency graph while it changes
* A package can be removed in the previous sub-graphs removals
* :pushpin: Automatic update of dependency voluptuous from 0.11.5 to 0.11.7
* :pushpin: Automatic update of dependency thoth-python from 0.6.0 to 0.6.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.4 to 0.18.5
* Change name of Thoth template to make Coala happy
* Start using Thoth in OpenShift's s2i
* Adjust testsuite to use only_solved flag
* Ask graph database only for packages which were already solved
* Do not remove package tuples which are direct dependencies
* Do not treat builds as pre-releases
* Fix reference to variable - do not pass class
* Fix resolving direct dependencies based on the score
* add metadata
* :pushpin: Automatic update of dependency thoth-storages from 0.18.3 to 0.18.4
* Introduce sieves
* :pushpin: Automatic update of dependency thoth-common from 0.9.5 to 0.9.6
* Update docs with sieves
* Add docs for performance indicators
* :pushpin: Automatic update of dependency thoth-storages from 0.18.1 to 0.18.3
* :pushpin: Automatic update of dependency thoth-storages from 0.18.0 to 0.18.1
* :pushpin: Automatic update of dependency thoth-storages from 0.17.0 to 0.18.0
* Release of version 0.5.0
* :pushpin: Automatic update of dependency thoth-storages from 0.16.0 to 0.17.0
* Deinstantiate solver once it is no longer needed
* Fix instantiation of edges
* Adjust testsuite so that it works with new implementation
* :pushpin: Automatic update of dependency thoth-storages from 0.15.2 to 0.16.0
* Fix handling of additional pytest arguments in setup.py test
* Fix handling of additional pytest arguments in setup.py test
* Move logic of stack candidates preparation to finalization part
* :pushpin: Automatic dependency re-locking
* Remove unused import
* Improve some logger messages
* Rewrite core adviser logic for dependency graph manipulation
* Optimize retrieval of transitive dependencies to avoid list copies
* Optimize instantiation of objects when resolved from graph database
* :pushpin: Automatic update of dependency thoth-storages from 0.15.1 to 0.15.2
* :pushpin: Automatic update of dependency thoth-python from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency thoth-solver from 1.2.1 to 1.2.2
* :pushpin: Automatic update of dependency thoth-storages from 0.15.0 to 0.15.1
* Inform user that the missing release will be analyzed later on
* Remove invalid configuration entry APP_FILE in build config
* :pushpin: Automatic update of dependency thoth-storages from 0.14.8 to 0.15.0
* Fix transitive query - correctly propagate runtime information
* Improve warning message
* :pushpin: Automatic update of dependency thoth-common from 0.9.3 to 0.9.4
* Adjust testing recommendation type for now
* Remove score based cut-off step, observation reduction takes its position
* Add tests for observation based reduction
* Introduce observation reduction step to reduce subgraphs with no observations
* Add error message if no stacks were produced
* Report error if no recommendation was produced
* Introduce routines for iterating over develop and non-develop deps
* :sparkles: added the standard github configuration and a CODEOWNERS file
* Update lockfile
* Report used pipeline configuration of adviser to user
* Additional fixes and additions
* Minor changes
* Use CXXABI_1.3.8
* Use black for formatting
* Rework optimizations
* Adjust testsuite for new implementation
* Implement structure for dependency graph adjustment
* Report packages forming a found stack inside to a log
* Print out estimated number of stacks in scientific form
* Use only packages with known index
* Increase default adviser's requests and limits
* :pushpin: Automatic update of dependency thoth-storages from 0.11.4 to 0.14.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.11 to 0.9.0
* Add build trigger using generic webhook
* :pushpin: Automatic update of dependency pytest from 4.6.2 to 4.6.3
* Updated Readme to Dgraph examples
* :pushpin: Automatic update of dependency thoth-common from 0.8.7 to 0.8.11
* :pushpin: Automatic update of dependency pytest from 4.5.0 to 4.6.2
* Optimize package removal by working on indexes instead of package tuples
* Keep stats for package removals per step run
* Update documentation to respect current state
* Use uint16_t for representing packages in libdependency graph
* Simplify module structure to libdependency_graph library
* :pushpin: Automatic update of dependency thoth-common from 0.8.5 to 0.8.7
* Give adviser more time to process rest of the stacks in queue
* Provide better report to user on why adviser has stopped prematurely
* Use defaults of -1 for "unlimited" numbers in the cluster
* Parse a special value of -1 in the cluster to workaround click's errors
* Be more user-friendly in cluster logs
* Place toolchain cut after semver sort
* :pushpin: Automatic update of dependency pytest from 4.4.2 to 4.5.0
* :pushpin: Automatic update of dependency thoth-storages from 0.11.3 to 0.11.4
* Re-introduce filedump for fixes on long-lasting queries
* Log number of packages considered during dependency graph traversals
* Fix testsuite
* Create pipeline builder abstraction
* :pushpin: Automatic update of dependency thoth-storages from 0.11.2 to 0.11.3
* Release of version 0.4.0
* Fix coala issues
* :pushpin: Automatic update of dependency pytest from 4.4.1 to 4.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.11.1 to 0.11.2
* Use new method to obtain even large stacks from graph database
* :pushpin: Automatic update of dependency mock from 3.0.4 to 3.0.5
* :pushpin: Automatic update of dependency mock from 3.0.3 to 3.0.4
* Add information about library usage to pipeline and OpenShift job
* Build-time error filtering should be a very first step
* Propagate information about project runtime when checking buildtime error
* Fix issue happening in semver sort after a package is removed
* Remove toolchain to always use latest toolchain release
* Fix empty paths if there is raised an exception about invalid pkg removal
* :pushpin: Automatic update of dependency thoth-storages from 0.11.0 to 0.11.1
* Log message was missleading if package_tuple gets overwritten
* Provide fast-path when checking for already removed packages
* :pushpin: Automatic update of dependency pytest-cov from 2.6.1 to 2.7.1
* Implement build-time error filtering step
* :pushpin: Automatic update of dependency mock from 3.0.2 to 3.0.3
* :pushpin: Automatic update of dependency mock from 2.0.0 to 3.0.2
* :pushpin: Automatic update of dependency thoth-storages from 0.10.0 to 0.11.0
* Adjust provenance-checker template to use Dgraph
* Adjust Dependency Monkey to use Dgraph
* Adjust adviser template to use Dgraph
* Report overall score of a stack
* Remove is_solvable flag as done in Dgraph implementation
* Added the method to read version from project to conf.py
* Remove JanusGraph specific bits
* Do not depend on specific graph adapter from specific module
* Remove JanusGraph specific bits
* :pushpin: Automatic update of dependency thoth-storages from 0.9.7 to 0.10.0
* Trigger dependency monkey reports sync into graph database
* :pushpin: Automatic update of dependency pytest from 4.4.0 to 4.4.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.4 to 0.8.5
* Automatic update of dependency thoth-common from 0.8.3 to 0.8.4
* Create a workaround for click argument parsing from env vars
* :sparkles: added the Registry to be used for image pulling to the templates
* Adviser implementation using stack generation pipeline
* Automatic update of dependency thoth-common from 0.8.2 to 0.8.3
* Make Isis a proper adapter
* Automatic update of dependency thoth-common from 0.8.1 to 0.8.2
* Automatic update of dependency pytest from 4.3.1 to 4.4.0
* :bug: put some sane default for IMAGE_STREAM_NAMESPACE into each template
* hot fixing the timeout
* :sparkles: ImageStream Tag and Namespace
* Automatic update of dependency flexmock from 0.10.3 to 0.10.4
* Report premature end of stack stream
* Improve handling of long-running advises
* Add timeout seconds for adviser to let it submit results
* Top score is now 100
* Automatic update of dependency thoth-storages from 0.9.6 to 0.9.7
* Automatic update of dependency thoth-python from 0.4.6 to 0.5.0
* Make reports more human readable
* Fix testsuite
* Add Thoth's configuration file
* Make Isis instance attribute
* Always kill stack producer if there is no consumer of stacks
* Fix Coala issues
* Do not score more than requested number of latest stacks
* Introduce stack producer timeout
* Use Sphinx for documentation
* Fix some test errors
* Minor improvements
* Introduce parameters for limiting number of versions
* Introduce limit parameter to limit number of packages of a same type
* Fix usage of package_t in libdependency_graph.so
* Use safe_load
* Fix coala complains
* Report any exception which occurred during dependency monkey run
* Introduce checks on configuration
* Make sure Isis is a singleton
* Minor fix in logged message
* Use Isis API from configmap
* Introduce performance based queries to Isis
* Make Coala happy again
* Use black for formatting
* Add missing file
* Make sure versions are sorted, add tests for adviser
* Use black for formatting tests
* Fix tests
* Log runtime environment when computing advises
* Address coala issues
* Add an optional graph database adapter to reduce number of connections
* Take into account packages that are not installable into the given env
* Update README, state local run in a container
* Report CVE count only if there were some found
* Remove unused env variables
* Provide Sentry and Prometheus configuration
* Add metadata information shown in result reports
* Update Pipfile.lock
* Register provenance-checker to graph-sync-scheduler
* Use runtime information during runtime-specific resolution
* Use runtime environment as provided by user
* Use click echo instead of raw print
* Fix wrong order of tuples
* Provide generic stack information
* Score and report CVEs in the application stack to the user
* Report version on each run
* Do not be too verbose
* Open source documentation for dependency graph
* Document dependency graph build
* Report number of stacks scored
* Raise an exception on premature stream end
* Minor changes in comment and logging message
* Fix coala complains
* Wait for parent to score stacks in stack producer
* Add shared library for CentOS:7
* Provide Dockerfile for container-build
* Add linked library
* Initial dependency graph implementation in C++
* Correctly handle end of pipe
* Adjust .gitignore
* Run dependency graph as a standalone process, produce stacks into pipe
* It's already 2019
* Use proper loglevel for debug message
* Restrict indexes in dependency monkey runs
* Schedule graph syncs for adviser runs by graph-sync-operator
* Fix hashes collision in generated Pipfile.locks
* Implement dependency graph in C++
* Reuse connected graph adapter do reduce number of connections
* Amun API URL is used by Dependency Monkey
* Argument has to be named otherwise cannot be used as kwargs
* Increase run time for dependency monkey
* Propagate whitelisted sources to provenance checks
* Increase dependency monkey requests
* Correctly propagate job ids from workload operator
* Fix CI by updating thoth-python package
* Remove duplicit parameter from template
* Increase adviser job run limit
* Provide limit and count defaults in template
* Add coverage file to .gitignore
* Fix linter issues
* Fix wrong variable usage
* Report limit if limit was reached
* Remove unused imports
* Minor docs fixes
* Link to Dependency Monkey design document
* Add dependency monkey design document into docs
* Cut off and minor adjustmets
* Refactor test suite
* Use black for formatting
* Minor code refactoring, update requirements
* Use to_tuple_locked method as we have locked packages
* Fix missing import
* Construct Pipfile from resolved dependencies
* Print estimated number of software stacks
* Remove unused if statement
* Adjust dependency graph to use ids
* The decision function is now not optional
* Performance based scoring on exact stack match
* Do not pass None values in runtime environment to_dict
* Simplify work with dependency graph
* Fix handling of runtime environment, remove unused bits
* Avoid possibly inserting same package versions multiple times
* Utilize iter_dependencies locked method
* Use Python 3.6 by default
* Discard original sources when creating a new project
* Fix transitive dependencies retrieval
* Don't be too verbose in logs
* Mark jobs for cleanup
* Fetch digests from graph database in provenance checks
* Remove unused perf type
* Prepare dependency graph for graph slicing
* Minor fixes in decision functions
* Restructure scoring and decision functions
* Capture all the layers of dependencies
* Minor code refactoring
* Do not print reasoning into logs
* Fix injecting digests into generated stacks
* Minor fixes in dependency monkey
* Do not forget to package requirements.txt
* Minor fixes
* Raise an exception if no matching versions were found
* Consider also version when creating dependency graph
* Move relevant test files to thoth-python package
* Correctly fill stacks with package digests
* Remove files that were moved to thoth-python
* Include index when retrieving packages from the graph database
* Fill package hashes from the graph database
* Fix import errors
* Structure error reports correctly respecting schema
* Use thoth-python package
* CI fixes
* Fix janusgraph port
* Fix Coala complains
* Fixes and improvements
* Adjust temporary filling package hashes
* Fix missing import
* Pass index to be none always
* Fill package digets in advises
* Be consistent with subcommand naming
* Minor fix in docstring
* Introduce limit in dependency monkey template
* Introduce limit and count in adviser template
* First implementation of the Adviser class
* Default to stdout in dependency monkey
* Refactor dependency monkey so that it can be used in notebooks
* Perform deepcopy to report the correct input
* Fix filling hashes multiple times
* Seed and count can be empty string
* Convert required parameters to ints
* Fix environment variable name
* Place all decision functions at one place
* Improve logging
* Fix missing import
* Make sure queries respect python package names according to PEP
* Improve logging to make sure its visible what's going on
* Fix syntax error
* Fix import error
* Add missing import
* Add ability to submit a testing stack
* Issue warning when submitting to Amun API
* Remove duplicit code for loading Amun context
* Handle exceptions happening when submitting to Amun API
* CI fixes
* Add exception if constraints cannot be met
* Temporary fill package digests by querying PyPI index
* Always check which source in a warehouse
* Adjust output methods
* Adjust dependency monkey job template
* Minor improvements in implementation
* Aaa
* Fixes in the dependency graph implementation
* A package version is distinguished by name, version and index
* Add missing imports
* Check first layer of dependencies for validity
* Sanity check for adding non-locked version to lock
* Add testsuite for graph solver, dependency graph implementation
* Introduce graph Python solver
* Add testsuite for graph solver
* Introduce dependency graph
* Introduce graph Python solver
* reading README from file, its the long_description...
* Check for latest packages present on indexes
* Release of version 0.3.0
* fixing coala
* typo :/
* using thoth zuul jobs now
* Adjust setup.py to run testsuite correctly
* Run testsuite using setup.py
* Output to JSON in adviser
* Link PackageVersion to Source index used
* Report dict reporesentation of input instead of raw strings
* Add missing parameters to template
* Fix labels section in template
* Dependency monkey is a template
* Move dependency monkey to a job template
* Rename adviser template to be more clear
* Move from Pods to Jobs
* Directly pass adviser subcommand that should be run
* Introduce Dependency Monkey template
* Update README file
* Fix link to Thamos
* Introduce method for converting model to object
* Possible different source is info
* Add Codacy badge
* Fix testsuite respecting last changes
* Link to Pipenv docs for specifying package indexes
* Fix console figure
* State configured index in the report message
* Adjust reported issue id for possible different source
* Add installation section and adjust based on review comments
* Document provenance checks
* Quote relevant parts of string
* Add the current PyPI index to default warehouses
* Make artifact names lowercase by deafult
* Finish provenance reports
* Report directly findings in the provenance check report
* Adviser report should be always an array
* Report back error if we cannot conclude on application stack
* Ignore s2i's virtualenv in which adviser is run
* Increase memory for adviser due to OOMs
* Release of version 0.2.0
* Introduce add_source and add_package methods
* Do not use command in openshift template
* Release of version 0.1.1
* Setuptools find_packages does not respect namespaces
* Release of version 0.1.0
* Initial dependency lock
* Add forgotten lxml library for bs4 parsing
* Provide JanusGraph configuration in provenance-checker template
* Provide JanusGraph configuration in adviser template
* Pass full path to Python3 in s2i
* Make CLI executable
* Install forgotten packages
* Add execute bit to app.sh
* State we want to run provenance rather than adviser in template
* Revert "Provide entrypoint for OpenShift s2i"
* Provide a script to run desired subcommand
* Provide entrypoint for OpenShift s2i
* Remove unused script as adviser is s2i now
* Remove Dockerfile as adviser is s2i now
* Let's reuse parameter names from adviser
* Use local tensorflow index page for gathering versions
* Fix warehouse test
* Some CI fixes
* Initial dependency lock
* Let Kebechet pin down deps
* Remove old TODO
* Implement sorting based on semver
* Create abstraction classes
* Initial python recommendation implementation
* Automatic update of dependency thoth-common from 0.2.6 to 0.2.7
* Automatic update of dependency thoth-common from 0.2.5 to 0.2.6
* Introduce provenance checker template
* Automatic update of dependency thoth-storages from 0.5.1 to 0.5.2
* Automatic update of dependency thoth-common from 0.2.4 to 0.2.5
* Automatic update of dependency thoth-common from 0.2.3 to 0.2.4
* change the queue
* Automatic update of dependency thoth-common from 0.2.2 to 0.2.3
* Automatic update of dependency thoth-storages from 0.5.0 to 0.5.1
* Automatic update of dependency thoth-storages from 0.4.0 to 0.5.0
* Automatic update of dependency thoth-storages from 0.3.0 to 0.4.0
* Automatic update of dependency thoth-storages from 0.2.0 to 0.3.0
* Automatic update of dependency thoth-storages from 0.1.1 to 0.2.0
* State all template parameters
* Be consistent with label naming
* Update requirements.txt respecting requirements in Pipfile
* Automatic update of dependency thoth-common from 0.2.1 to 0.2.2
* Automatic update of dependency thoth-storages from 0.1.0 to 0.1.1
* Add app=thoth label to pod template
* Adjust template labels
* Fix image stream kind in template
* Fix coala naming convention configuration
* Add OpenShift templates for deployment
* Automatic update of dependency thoth-storages from 0.0.33 to 0.1.0
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Initial dependency lock
* Delete Pipfile.lock for relocking dependencies
* relocked, travis removed, zuul added
* Automatic update of dependency thoth-common from 0.0.9 to 0.1.0
* Automatic update of dependency thoth-analyzer from 0.0.6 to 0.0.7
* Automatic update of dependency thoth-analyzer from 0.0.5 to 0.0.6
* Automatic update of dependency thoth-storages from 0.0.32 to 0.0.33
* Automatic update of dependency thoth-storages from 0.0.29 to 0.0.32
* Automatic update of dependency thoth-common from 0.0.6 to 0.0.9
* Update thoth packageswq
* Automatic update of dependency thoth-storages from 0.0.25 to 0.0.28
* Do not restrict Thoth packages
* Another CI fix
* Another CI fix
* Run coala in non-interactive mode
* CI fix
* Run coala in CI
* Create OWNERS
* Remove dependencies.yml
* Use coala for code checks
* Fix package name in license header
* Add LICENSE and license headers
* Use thoth's common logging
* Add README file
* Version 0.0.2
* State only direct dependencies in requirements.txt
* Version 0.0.1
* Update dependencies
* Update thoth-storages from 0.0.3 to 0.0.4
* Rename environment variables to respect user-api arguments passing
* Create initial dependencies.yml config
* Change envvar for --requirements option
* Expose advise_pypi function
* Version 0.0.0
* Build adviser image in CI
* Fix naming typo
* Initial template for implementation
* Initial project import

## Release 0.9.4 (2020-04-06T14:48:43)
* Empty commit to trigger the new release

## Release 0.9.5 (2020-05-25T20:15:31)
* :pushpin: Automatic update of dependency pytest-cov from 2.8.1 to 2.9.0
* :pushpin: Automatic update of dependency thoth-storages from 0.22.10 to 0.22.11
* :pushpin: Automatic update of dependency hypothesis from 5.15.0 to 5.15.1
* Add unsolved-package-handler to adviser workflow
* :pushpin: Automatic update of dependency hypothesis from 5.14.0 to 5.15.0
* update versions
* Use thoth-toolbox
* Use thamos from upstream
* :pushpin: Automatic update of dependency packaging from 20.3 to 20.4
* Fix links to docs and add s2i migration video
* :pushpin: Automatic update of dependency toml from 0.10.0 to 0.10.1
* :pushpin: Automatic update of dependency hypothesis from 5.13.1 to 5.14.0
* :pushpin: Automatic update of dependency hypothesis from 5.11.0 to 5.13.1
* :pushpin: Automatic update of dependency thoth-storages from 0.22.9 to 0.22.10
* :pushpin: Automatic update of dependency pytest from 5.4.1 to 5.4.2
* Improve message provided to user
* :pushpin: Automatic update of dependency hypothesis from 5.10.5 to 5.11.0
* Point to s2i-example-migration
* :pushpin: Automatic update of dependency thoth-storages from 0.22.8 to 0.22.9
* :pushpin: Automatic update of dependency hypothesis from 5.10.4 to 5.10.5
* Sync variable fix for provenance check
* Update dependencies to pass the test suite
* Implement platform boot
* Adviser Dev env var added to template
* Include MKL warning also in dependency monkey runs
* intel-tensorflow is built with MKL support
* :pushpin: Automatic update of dependency hypothesis from 5.9.1 to 5.10.0
* Handle exit code regardless core file is produced
* :pushpin: Automatic update of dependency hypothesis from 5.9.0 to 5.9.1
* fixed coala errors
* fixed coala complaint
* fixed the apiVersion of all the OpenShift Templates
* :pushpin: Automatic update of dependency hypothesis from 5.8.6 to 5.9.0
* :pushpin: Automatic update of dependency hypothesis from 5.8.5 to 5.8.6
* :pushpin: Automatic update of dependency hypothesis from 5.8.4 to 5.8.5
* :pushpin: Automatic update of dependency hypothesis from 5.8.3 to 5.8.4
* Create a wrap for Intel's MKL env variable configuration
* :pushpin: Automatic update of dependency hypothesis from 5.8.2 to 5.8.3
* :pushpin: Automatic update of dependency hypothesis from 5.8.1 to 5.8.2
* :pushpin: Automatic update of dependency hypothesis from 5.8.0 to 5.8.1
* Fixed readme link
* consistency in using secrets
* Fix liveness probe
* Add missing liveness probe to advise workflow
* Export variable as adviser forks a sub-process

## Release 0.10.0 (2020-06-11T20:52:00)
* :pushpin: Automatic update of dependency hypothesis from 5.16.0 to 5.16.1
* Respect review comments
* Update docs/source/deployment.rst
* Call destructor of the final state explictly once done with the state
* Note down beam width once the resolution is terminated
* Document deployment and configuring adviser in a deployment
* More optimizations to speed up adviser
* Coala fix
* :recycle: Removed unnecessary tempalates
* Do not use OrderedDict for internal state representation
* Add a boot for tracing memory consumption
* Preserve order in pre and post run methods
* adjust kebechet run-results workflow
* add conditional to workflow
* add default output params
* indent to follow coala styling
* Added black
* :pushpin: Automatic update of dependency pytest from 5.4.2 to 5.4.3
* Added pyproject.toml
* Use trigger integration in adviser workflow
* add is_missing to mock tests
* correct typo
* use workflow-helpers
* Add outputs
* remove imagestream envs
* Change to trigger integration task
* kebechet->KEBECHET because of enum values
* remove image stream params
* add ssh to adviser workflow
* secret mount WorkflowTemplate->Workflow
* add ssh volume mount
* remove debugging step
* added a 'tekton trigger tag_release pipeline issue'
* add volume mount for proper output
* :pushpin: Automatic update of dependency thoth-storages from 0.22.11 to 0.22.12
* fix parameter passing
* change env name
* :pushpin: Automatic update of dependency hypothesis from 5.15.1 to 5.16.0
* add run-result to adviser workflow
* add is missing resolver
* use THOTH_ in fron env
* use workflow-helpers for tasks
* clean up tasks, remove unnecessary stuff
* first attempt at kebechet run results task
* Remove sieve and use inital query
* added to do for thoth.storages
* create sieve for missing package versions

## Release 0.11.0 (2020-07-10T10:25:10)
* :pushpin: Automatic update of dependency thoth-storages from 0.24.0 to 0.24.2 (#1048)
* Document Wrap pipeline unit type (#1047)
* Remove tempalates handled by thoth-application (#1046)
* :sparkles: added the cyborg-supervisors team to prow univers, after we have had it as a github team
* Add link to Provenance Checks (#1045)
* Introduce a mock score step for experimenting with predictors
* Implement a pipeline step for recommending AVX2 builds of AICoE Tenso… (#1020)
* :pushpin: Automatic update of dependency hypothesis from 5.18.3 to 5.19.0 (#1043)
* Introduce a wrap for recommending Python3.8 on RHEL 8.2 (#1042)
* :pushpin: Automatic update of dependency hypothesis from 5.18.0 to 5.18.3 (#1041)
* Remove provenance-checker job template
* Update OWNERS
* :pushpin: Automatic update of dependency hypothesis from 5.16.3 to 5.18.0
* :pushpin: Automatic update of dependency thoth-storages from 0.23.2 to 0.24.0
* Remove latest versions limitation
* Adjust MANIFEST.in
* :pushpin: Automatic update of dependency hypothesis from 5.16.1 to 5.16.3
* :pushpin: Automatic update of dependency matplotlib from 3.2.1 to 3.2.2
* :pushpin: Automatic update of dependency thoth-storages from 0.23.0 to 0.23.2
* :pushpin: Automatic update of dependency thoth-python from 0.9.2 to 0.10.0
* add secondsAfterFailure
* Increase time for SLI
* Remove dependency
* Include each marker of a type just once
* Disable setup.py processing in s2i builds
* Add a check for available platforms
* Disable provenance checks

## Release 0.12.0 (2020-07-16T13:14:51)
* :pushpin: Automatic update of dependency pytest-timeout from 1.4.1 to 1.4.2 (#1054)
* :pushpin: Automatic update of dependency thoth-storages from 0.24.2 to 0.24.3 (#1051)
* Release of version 0.11.0 (#1052)
* :pushpin: Automatic update of dependency thoth-storages from 0.24.0 to 0.24.2 (#1048)
* Document Wrap pipeline unit type (#1047)
* Remove tempalates handled by thoth-application (#1046)
* :sparkles: added the cyborg-supervisors team to prow univers, after we have had it as a github team
* Add link to Provenance Checks (#1045)
* Introduce a mock score step for experimenting with predictors
* Implement a pipeline step for recommending AVX2 builds of AICoE Tenso… (#1020)
* :pushpin: Automatic update of dependency hypothesis from 5.18.3 to 5.19.0 (#1043)
* Introduce a wrap for recommending Python3.8 on RHEL 8.2 (#1042)
* :pushpin: Automatic update of dependency hypothesis from 5.18.0 to 5.18.3 (#1041)
* Remove provenance-checker job template
* Update OWNERS
* :pushpin: Automatic update of dependency hypothesis from 5.16.3 to 5.18.0
* :pushpin: Automatic update of dependency thoth-storages from 0.23.2 to 0.24.0
* Remove latest versions limitation
* Adjust MANIFEST.in
* :pushpin: Automatic update of dependency hypothesis from 5.16.1 to 5.16.3
* :pushpin: Automatic update of dependency matplotlib from 3.2.1 to 3.2.2
* :pushpin: Automatic update of dependency thoth-storages from 0.23.0 to 0.23.2
* :pushpin: Automatic update of dependency thoth-python from 0.9.2 to 0.10.0
* add secondsAfterFailure
* Increase time for SLI
* Remove dependency
* Include each marker of a type just once
* Dependency relocking to fix CI
* Release of version 0.10.0
* :pushpin: Automatic update of dependency thoth-storages from 0.22.12 to 0.23.0
* Disable setup.py processing in s2i builds
* :pushpin: Automatic update of dependency hypothesis from 5.16.0 to 5.16.1
* Respect review comments
* Update docs/source/deployment.rst
* Call destructor of the final state explictly once done with the state
* Note down beam width once the resolution is terminated
* Document deployment and configuring adviser in a deployment
* More optimizations to speed up adviser
* Coala fix
* :recycle: Removed unnecessary tempalates
* Do not use OrderedDict for internal state representation
* Add a boot for tracing memory consumption
* Preserve order in pre and post run methods
* Add a check for available platforms
* adjust kebechet run-results workflow
* add conditional to workflow
* add default output params
* indent to follow coala styling
* Added black
* :pushpin: Automatic update of dependency pytest from 5.4.2 to 5.4.3
* Added pyproject.toml
* Use trigger integration in adviser workflow
* add is_missing to mock tests
* correct typo
* use workflow-helpers
* Add outputs
* remove imagestream envs
* Change to trigger integration task
* kebechet->KEBECHET because of enum values
* remove image stream params
* add ssh to adviser workflow
* secret mount WorkflowTemplate->Workflow
* add ssh volume mount
* remove debugging step
* added a 'tekton trigger tag_release pipeline issue'
* add volume mount for proper output
* :pushpin: Automatic update of dependency thoth-storages from 0.22.11 to 0.22.12
* fix parameter passing
* change env name
* :pushpin: Automatic update of dependency hypothesis from 5.15.1 to 5.16.0
* add run-result to adviser workflow
* add is missing resolver
* use THOTH_ in fron env
* use workflow-helpers for tasks
* Release of version 0.9.5
* :pushpin: Automatic update of dependency pytest-cov from 2.8.1 to 2.9.0
* :pushpin: Automatic update of dependency thoth-storages from 0.22.10 to 0.22.11
* :pushpin: Automatic update of dependency hypothesis from 5.15.0 to 5.15.1
* Add unsolved-package-handler to adviser workflow
* clean up tasks, remove unnecessary stuff
* first attempt at kebechet run results task
* Remove sieve and use inital query
* :pushpin: Automatic update of dependency hypothesis from 5.14.0 to 5.15.0
* update versions
* Use thoth-toolbox
* Use thamos from upstream
* :pushpin: Automatic update of dependency packaging from 20.3 to 20.4
* added to do for thoth.storages
* Fix links to docs and add s2i migration video
* create sieve for missing package versions
* :pushpin: Automatic update of dependency toml from 0.10.0 to 0.10.1
* :pushpin: Automatic update of dependency hypothesis from 5.13.1 to 5.14.0
* :pushpin: Automatic update of dependency hypothesis from 5.11.0 to 5.13.1
* :pushpin: Automatic update of dependency thoth-storages from 0.22.9 to 0.22.10
* :pushpin: Automatic update of dependency pytest from 5.4.1 to 5.4.2
* Improve message provided to user
* :pushpin: Automatic update of dependency hypothesis from 5.10.5 to 5.11.0
* Point to s2i-example-migration
* :pushpin: Automatic update of dependency thoth-storages from 0.22.8 to 0.22.9
* :pushpin: Automatic update of dependency hypothesis from 5.10.4 to 5.10.5
* Sync variable fix for provenance check
* Update dependencies to pass the test suite
* Implement platform boot
* Adviser Dev env var added to template
* Include MKL warning also in dependency monkey runs
* intel-tensorflow is built with MKL support
* :pushpin: Automatic update of dependency hypothesis from 5.9.1 to 5.10.0
* Handle exit code regardless core file is produced
* :pushpin: Automatic update of dependency hypothesis from 5.9.0 to 5.9.1
* fixed coala errors
* fixed coala complaint
* fixed the apiVersion of all the OpenShift Templates
* :pushpin: Automatic update of dependency hypothesis from 5.8.6 to 5.9.0
* :pushpin: Automatic update of dependency hypothesis from 5.8.5 to 5.8.6
* :pushpin: Automatic update of dependency hypothesis from 5.8.4 to 5.8.5
* :pushpin: Automatic update of dependency hypothesis from 5.8.3 to 5.8.4
* Create a wrap for Intel's MKL env variable configuration
* :pushpin: Automatic update of dependency hypothesis from 5.8.2 to 5.8.3
* :pushpin: Automatic update of dependency hypothesis from 5.8.1 to 5.8.2
* :pushpin: Automatic update of dependency hypothesis from 5.8.0 to 5.8.1
* Fixed readme link
* consistency in using secrets
* Fix liveness probe
* Add missing liveness probe to advise workflow
* Export variable as adviser forks a sub-process
* Release of version 0.9.4
* Empty commit to trigger the new release
* Introduce heat up phase for the latest predictor
* Setup TTL strategy to reduce preassure causing OOM
* :pushpin: Automatic update of dependency pytest-mypy from 0.6.0 to 0.6.1
* Adjust test accordingly
* Adjust the message produced
* Reduce beam width to address OOM issues for large stacks in the cluster
* Improve message when adviser is stopped based on CPU time
* Recommendation type is not lowercase
* Disable provenance checks
* Release of version 0.9.3
* Release of version 0.9.2
* Fixes needed to make this package available on PyPI
* Tweak temperature function for ASA, TD and MCTS
* Adjust parameters in deployment
* Release of version 0.9.1
* Fix bug causing adviser halt for shared resolved packages
* Release of version 0.9.0
* Fix info message causing issues when the beam is empty
* Add fext to application requirements
* Remove unusued parameter
* Re-enable fext for beam's internal state handling
* consistency in openshift templates to run provenance
* :pushpin: Automatic update of dependency pyyaml from 3.13 to 5.3.1
* Introduce heat up part of MCTS
* Prioritize releases by AICoE
* :pushpin: Automatic update of dependency thoth-solver from 1.5.0 to 1.5.1
* :pushpin: Automatic update of dependency thoth-storages from 0.22.6 to 0.22.7
* Do not keep beam history if not necessary
* :pushpin: Automatic update of dependency thoth-storages from 0.22.5 to 0.22.6
* Add option consider/do not consider dev dependencies
* Increase timeout for running tests
* Increase timeout for running tests
* No need to initialize logging multiple times
* Minor fixes in api_compat
* Use MCTS predictor for stable and testing recommendations
* Optimize termial of n computation
* Fix scoring of the user stack
* Optimize termial of n computation
* Address issues spotted in resolution when MCTS is used
* Document provenance checks
* :pushpin: Automatic update of dependency pyyaml from 5.3.1 to 3.13
* Fix context handling when passing in as raw JSON
* Fix dependency monkey invocation flag
* :pushpin: Automatic update of dependency hypothesis from 5.7.2 to 5.8.0
* :pushpin: Automatic update of dependency hypothesis from 5.7.1 to 5.7.2
* :pushpin: Automatic update of dependency pyyaml from 3.13 to 5.3.1
* Log resolver progress each 10%
* :pushpin: Automatic update of dependency hypothesis from 5.7.0 to 5.7.1
* Missing parenthesis prevent sync on Ceph
* Test suite and duplicate code refactoring
* Fix docstring
* Updates to the new beam API
* Reduce memory footprint
* Implement MCTS predictor
* Additional changes for TD
* Fix annealing testsuite
* Introduce Temporal Difference based predictor using annealing based scheduling
* Fix coala complains
* Introduce user stack scoring as a base for comparision
* Make sure the error report for adviser exceptions is always present
* :pushpin: Automatic update of dependency thoth-storages from 0.22.4 to 0.22.5
* :pushpin: Automatic update of dependency thoth-storages from 0.22.3 to 0.22.4
* Rewrite beam so that it does not use fext
* Wrong variable name
* :pushpin: Automatic update of dependency hypothesis from 5.6.1 to 5.7.0
* :pushpin: Automatic update of dependency hypothesis from 5.6.0 to 5.6.1
* :pushpin: Automatic update of dependency matplotlib from 3.2.0 to 3.2.1
* Correct space for exception
* Fix handling of environment markers when multiple packages use marker
* Release of version 0.8.0
* Fix defaults in CLI, they are lowercase now
* Resolver does not check runtime environment specification during state resolving
* Add Python version boot
* Start using fext in adviser
* :pushpin: Automatic update of dependency pytest from 5.3.5 to 5.4.1
* :pushpin: Automatic update of dependency pytest-mypy from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency pyyaml from 5.3 to 3.13
* Adjust string for image and key
* Add registry env variables
* remove default values
* Generalize variables for Ceph for the workflows
* fixed coala
* Fixed error log and old api
* Prevent from OSError when the requirements string is too large
* :pushpin: Automatic update of dependency click from 7.0 to 7.1.1
* :pushpin: Automatic update of dependency click from 7.0 to 7.1.1
* :pushpin: Automatic update of dependency packaging from 20.1 to 20.3
* :pushpin: Automatic update of dependency matplotlib from 3.1.3 to 3.2.0
* Add voluptous to requirements.txt
* Introduce package source index sieve for filtering based on index
* Remove typeshed
* UBI boot has to be before boot that checks RHEL version
* Solved software environment has to be run after changes to environment
* Adjust testsuite
* Propagate the original runtime environment used in resolving in pipeline products
* Use the correct condition for checking parameters
* Increase timeout for pytest tests
* Fix test suite
* Ignore the run logger for dependency monkey runs
* Fix type
* Propagate metdata to products
* Allow context to be passed as a file
* Update thoth-storages to address import issue
* Update dependencies
* Propagate metdata to products
* Bump template version
* OpenShift templates are referenced by label
* Update dependencies
* Distinguish different types of errors of adviser runs for SLO
* Child exists with status code 256
* Do not overwrite results computed in the forked process
* Adviser workflow when using Thamos CLI
* Add URLs to GitHub and PyPI
* :pushpin: Automatic update of dependency hypothesis from 5.5.3 to 5.5.4
* :pushpin: Automatic update of dependency hypothesis from 5.5.2 to 5.5.3
* No deafult value null for metadata
* :pushpin: Automatic update of dependency hypothesis from 5.5.1 to 5.5.2
* :pushpin: Automatic update of dependency thoth-storages from 0.22.1 to 0.22.2
* Adjust version and use correct keys
* :pushpin: Automatic update of dependency thoth-storages from 0.22.0 to 0.22.1
* Add default value when user does not provided Pipfile.lock
* Add template for releases
* Revert to flexmock(GraphDatabase)
* GraphDatabase->graph
* follow python standards
* add more flex
* back to should receive after storages update
* :pushpin: Automatic update of dependency thoth-storages from 0.21.11 to 0.22.0
* Update .thoth.yaml
* change to should call
* initialize graph
* abi-compat-sieve tests
* :pushpin: Automatic update of dependency hypothesis from 5.4.2 to 5.5.1
* Run workflow even if adviser fails
* add env variable
* Use correct storage to store results
* State thoth-s2i in integration
* Propagate information about missing configuration in report
* Add a wrap for adding info about no observations
* Update docstring
* :pushpin: Automatic update of dependency hypothesis from 5.4.1 to 5.4.2
* Make decision type and recommendation type lowercase
* Modify parameters for GitHub App
* remove metadata
* Move cache to storage level
* cache query results
* shortcut if package requires no symbols
* self.image_symbols is now a set
* Create abi sieve
* Adjust script in finished webhook
* adjust script in finished webhook template
* remove service account argo
* Adjust inner workflow for GitHub App
* :pushpin: Automatic update of dependency hypothesis from 4.57.1 to 5.4.1
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.3 to 1.1.4
* :pushpin: Automatic update of dependency matplotlib from 3.1.2 to 3.1.3
* :pushpin: Automatic update of dependency pytest from 5.3.4 to 5.3.5
* Do identity check instead of equality check
* Capture CLI parameters in resolver's context
* :pushpin: Automatic update of dependency thoth-storages from 0.21.10 to 0.21.11
* Log information about future solver runs of unsolved dependencies
* Fix Coala complains
* Introduce normalization of score returned by step units
* Introduce RHEL version boot for RHEL major releases
* :pushpin: Automatic update of dependency packaging from 20.0 to 20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.21.9 to 0.21.10
* :pushpin: Automatic update of dependency thoth-storages from 0.21.8 to 0.21.9
* :pushpin: Automatic update of dependency pytest from 5.3.3 to 5.3.4
* :pushpin: Automatic update of dependency thoth-storages from 0.21.7 to 0.21.8
* Try its best to always come up with a latest stack
* Rename template for workflow-operator
* Disable dry run for Thoth's recommendations
* Fix a bug when env is not fully specified and env marker filters out deps
* :pushpin: Automatic update of dependency pytest from 5.3.2 to 5.3.3
* Do not show information about results being submitted to result API
* Use WARNING log level in thoth.common
* Ask for thoth.adviser log to have clean logs and respect log configuration
* Use epsilon greedy strategy for picking the latest version
* Adjust limit latest versions and beam width
* Introduce version constrain sieve pipeline unit
* Assign correct default value
* Do not keep history in adviser runs
* Fix default value key
* Add missing metadata to adviser job template
* Fix handling of --dry-run parameter
* Show version of direct dependencies explictly
* Include random decision stride only explictly
* Introduce stride for getting one version in a stack
* :pushpin: Automatic update of dependency thoth-storages from 0.21.6 to 0.21.7
* Move log_once to utils function
* Optimize state removal out of beam
* Terminal output is slow, log only after N stacks generated
* Optimize handling of the top score kept in beam
* Prevent annealing from being stuck
* Fix bug shown when sieves or steps filtered out dependecies
* Log stack counter in a more human readable form
* Propagate also expanded package tuple to reward signal
* Mention behavior for the default value
* Refactor keep history into an utility function for reusability
* Log pipeline speed
* Release of version 0.7.3
* Raise an error if no direct dependencies were found
* Report error on resolution failure
* Create more descriptive message
* Add tests for no dependencies cases during resolution
* Rebase and simplify code
* Fix log message reported
* Log interesting checkpoints during resolution to user
* Reward signal now propagates state for which the reward signal is computed
* Introduce a method for getting a state by its id
* Fix exception error messages produced
* Fix beam method signatures
* Remove unused import statement
* Introduce approximating latest predictor
* :pushpin: Automatic update of dependency thoth-storages from 0.21.5 to 0.21.6
* Re-add state with no unresolved dependencies back to beam on resolution
* Remvoe accidentally committed print statement
* Introduce finalizers for predictor's memory footprint optimization
* Predictor should pick key to beam
* Introduce assigned context to predictor
* Extend docs with MDP
* :pushpin: Automatic update of dependency thoth-storages from 0.21.4 to 0.21.5
* Release of version 0.7.2
* :pushpin: Automatic update of dependency thoth-storages from 0.21.3 to 0.21.4
* Release of version 0.7.1
* Set random walk as default predictor for Dependency Monkey
* Inspection endpoint does not accept runtime environment
* Fix submitting inspections
* :pushpin: Automatic update of dependency thoth-storages from 0.21.2 to 0.21.3
* Add a boot that checks for fully specified environment
* Add ability to block pipeline units during pipeline build
* :pushpin: Automatic update of dependency thoth-storages from 0.21.1 to 0.21.2
* :pushpin: Automatic update of dependency thoth-storages from 0.21.0 to 0.21.1
* Bump template patch version
* Fix decision type environment variable name
* There is no option for DEPENDENDENCY_MONKEY_LIMIT
* :pushpin: Automatic update of dependency thoth-storages from 0.20.6 to 0.21.0
* did not save merge before merging
* Yield from iterator to keep context
* Add a note on requirements.txt
* State pip/pip-compile support in integration section
* Correct wrong key in template
* Adjust testsuite accordingly
* Sort direct dependencies for reproducible resolver runs
* :pushpin: Automatic update of dependency thoth-python from 0.9.0 to 0.9.1
* Do not prefer recent versions in random walk and sampling
* Optimize arithmetics a bit
* Be more explicit about the function call in docstring
* Use r""" if any backslashes in a docstring
* Introduce termial function to prefer more recent versions randomly
* Extend resolver testsuite
* :pushpin: Automatic update of dependency thoth-solver from 1.4.1 to 1.5.0
* Adjust env variable name
* :pushpin: Automatic update of dependency thoth-python from 0.8.0 to 0.9.0
* :pushpin: Automatic update of dependency thoth-storages from 0.20.5 to 0.20.6
* Boots can raise not acceptable
* Do not run adviser from bc in debug mode
* Do not run adviser from bc in debug mode
* Add testsuite for solved software environment pipeline unit
* Register solved software environment boot
* Sort reported environments
* Introduce solved software environment boot
* :pushpin: Automatic update of dependency thoth-storages from 0.20.4 to 0.20.5
* :pushpin: Automatic update of dependency thoth-python from 0.7.1 to 0.8.0
* :pushpin: Automatic update of dependency pytest-timeout from 1.3.3 to 1.3.4
* :pushpin: Automatic update of dependency pyyaml from 5.2 to 5.3
* :pushpin: Automatic update of dependency thoth-storages from 0.20.3 to 0.20.4
* :pushpin: Automatic update of dependency thoth-storages from 0.20.2 to 0.20.3
* Beam is part of context, no need to pass it explictly
* Fixed missing emptyDir in the Adviser Workflow
* Limit number of software stacks to 1 on LATEST
* Adjust testsuite to correctly propagate reward signal
* Introduce beam.reset()
* Introduce beam.get_random()
* Reward signal now accepts resolver context
* Remove environment serialization - it takes some time during runs
* Random walk and initial configuration change
* Fixed too many blank lines in Workflow template
* Fixed adviser Workflow template
* :pushpin: Automatic update of dependency thoth-storages from 0.20.1 to 0.20.2
* Happy new year!
* :pushpin: Automatic update of dependency thoth-storages from 0.20.0 to 0.20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.30 to 0.20.0
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.2 to 1.1.3
* :pushpin: Automatic update of dependency hypothesis from 4.57.0 to 4.57.1
* :pushpin: Automatic update of dependency hypothesis from 4.56.3 to 4.57.0
* Adjust documentation for the new predictor run API
* :pushpin: Automatic update of dependency hypothesis from 4.56.2 to 4.56.3
* :pushpin: Automatic update of dependency hypothesis from 4.56.1 to 4.56.2
* Predictors now return also packages that should be resolved from states
* Fix docstring of boot
* Add few more asserts
* Add tests for leaf node expansion with marker set to False
* Add a boot for mapping UBI to RHEL
* Exclude reports from run error in Sentry
* :pushpin: Automatic update of dependency hypothesis from 4.56.0 to 4.56.1
* :pushpin: Automatic update of dependency hypothesis from 4.55.4 to 4.56.0
* :pushpin: Automatic update of dependency hypothesis from 4.55.3 to 4.55.4
* :pushpin: Automatic update of dependency hypothesis from 4.55.2 to 4.55.3
* Add checks for special cases when environment markers apply to leaf nodes
* Register CVE step only for STABLE and TESTING recommendation types
* Automatically choose the most appropriate predictor based on CLI
* :sparkles: added an Argo Workflow to run an advise
* Adjust API and tests to the new change
* :see_no_evil: ignoring the xml report coverage file
* :pushpin: Automatic update of dependency thoth-storages from 0.19.27 to 0.19.30
* :pushpin: Automatic update of dependency hypothesis from 4.55.1 to 4.55.2
* Format using black
* Counter is no longer used
* Improve multi-key sorting of states in the beam
* Log warning about shared dependencies in the dependency graph
* :pushpin: Automatic update of dependency hypothesis from 4.55.0 to 4.55.1
* Do not retrieve markers during resolution
* Fix logging format expansion
* Log also beam size
* :pushpin: Automatic update of dependency hypothesis from 4.54.2 to 4.55.0
* Match only first part of tuple
* Fix computing top state in the beam
* Simplify creation of initial states
* Adjust relative order for steps registration
* :pushpin: Automatic update of dependency hypothesis from 4.54.1 to 4.54.2
* :pushpin: Automatic update of dependency hypothesis from 4.54.0 to 4.54.1
* Fix Coala complains
* Keep track of dependencies added
* Accepted final states can be 0
* Revert "Add new iteration method for sieves and steps"
* Make temperature function a function of iteration as well
* :pushpin: Automatic update of dependency hypothesis from 4.53.3 to 4.54.0
* :pushpin: Automatic update of dependency hypothesis from 4.53.2 to 4.53.3
* :pushpin: Automatic update of dependency pytest from 5.3.1 to 5.3.2
* Keep beam in context
* Implement a dropout step
* :pushpin: Automatic update of dependency hypothesis from 4.53.1 to 4.53.2
* Bump version in templates
* Fork only in the cluster
* Fix coala complains
* Document new iteration round methods
* Add new iteration method for sieves and steps
* Adjust docs for limit latest versions
* Always bind context
* Add tests for limit latest versions and semver sort
* Adjust test suite
* Adjust semantics of limit latest versions
* Add a note on shared dependencies
* Refactor plotting primitives
* Do not keep history if not plotting in CLI
* Rename and move history related bits in predictors
* Remove debug print
* Implement resolving stop when SIGINT is caught
* Use SIGINT in liveness probe
* Implement version clash boot
* Tests for hill climbing and sampling, minor refactoring
* Add locked sieve
* Beam width is stated two times
* Document OpenShift s2i build integration
* Fix issue when there are no unresolved dependencies left in the state
* Document beam width and how to plot it
* Document build-watcher
* Log correct file location for beam history plots
* :pushpin: Automatic update of dependency hypothesis from 4.53.0 to 4.53.1
* Document build-watcher
* :pushpin: Automatic update of dependency hypothesis from 4.52.0 to 4.53.0
* :pushpin: Automatic update of dependency hypothesis from 4.51.1 to 4.52.0
* :pushpin: Automatic update of dependency hypothesis from 4.51.0 to 4.51.1
* Add a link to Thamos documentation
* Point to Thamos documentation instead of GitHub repo
* Add a link to performance article published
* Add architecture diagram
* State also core repository
* docs: Architecture overview section
* :pushpin: Automatic update of dependency hypothesis from 4.50.8 to 4.51.0
* Remove graph cache bits no longer used
* Document pipeline configuration instrumentation
* Point documentation to other libraries
* Add developer's guide to documentation
* Use RHEL instead of UBI
* Update Thoth configuration file and Thoth's s2i configuration
* Remove old comment
* Add note to step docs - no adjustment in step or beam
* No need to clone a state before running steps
* Do not show not relevant logs to users
* Point to source code documentation for described methods
* Fix exit code propagation of the forked child
* Add validation of count and limit resolver attributes
* Produce more descriptive message if any of direct dependencies was not resolved
* :pushpin: Automatic update of dependency thoth-storages from 0.19.26 to 0.19.27
* Adjust parameters for adviser and dependency-monkey
* Propagate information about package that has CVE to justification in CVE step
* :pushpin: Automatic update of dependency hypothesis from 4.50.7 to 4.50.8
* :pushpin: Automatic update of dependency thoth-storages from 0.19.25 to 0.19.26
* :pushpin: Automatic update of dependency thoth-solver from 1.4.0 to 1.4.1
* Add Google Analytics
* Fix reference to sieve in docs
* Fix references to the source code
* Release of version 0.7.0
* :pushpin: Automatic update of dependency hypothesis from 4.50.6 to 4.50.7
* Graph cache is not used anymore
* Fix coala complains
* Enhance exception
* Give more information dependencies were not resolved
* Set beam width template in the adviser template job
* Fix coala complains
* Fix coala complains
* Some docs for readers and developers
* Fix stride signature
* Fix boot docstring
* Fix tests
* Optimizations of beam
* Fix Coala complains
* Use generators to retrieve items
* Provide property for run executor that prints report
* Provide an option to configure pipeline via file/dict
* Log package version before pipeline step execution
* Remove unused method
* Test simulated annealing primitives, refactor core annealing part
* Step should not return Nan/Inf
* Use backtracking to run steps
* Make coala happy again
* Add tests for two corner cases for package clash during resolution
* Fix beam top manipulation
* Add logic for registering a final state
* Add dependencies only if they were previously considered based on env marker
* Remove print used during debugging
* :pushpin: Automatic update of dependency hypothesis from 4.50.5 to 4.50.6
* :pushpin: Automatic update of dependency hypothesis from 4.50.4 to 4.50.5
* :pushpin: Automatic update of dependency hypothesis from 4.50.3 to 4.50.4
* :pushpin: Automatic update of dependency hypothesis from 4.50.2 to 4.50.3
* Change default number of stacks returned on call
* Fix parameter to adviser CLI
* Adjust logged messages
* Make beam instance of resolver
* Adjust limit latest versions signature, do not perform shallow copy
* Sieve now accepts and returns a generator of package versions
* :pushpin: Automatic update of dependency thoth-storages from 0.19.24 to 0.19.25
* Address review comments
* :pushpin: Automatic update of dependency hypothesis from 4.50.1 to 4.50.2
* Fix coala issues
* Fix typo in docstring
* :pushpin: Automatic update of dependency hypothesis from 4.50.0 to 4.50.1
* :pushpin: Automatic update of dependency hypothesis from 4.49.0 to 4.50.0
* Optimize retrieval of environment markers
* :pushpin: Automatic update of dependency hypothesis from 4.48.0 to 4.49.0
* :pushpin: Automatic update of dependency hypothesis from 4.47.4 to 4.48.0
* Even more tests
* :pushpin: Automatic update of dependency hypothesis from 4.47.3 to 4.47.4
* Propagate document id into jobs
* More tests
* :pushpin: Automatic update of dependency hypothesis from 4.47.2 to 4.47.3
* :pushpin: Automatic update of dependency pytest from 5.3.0 to 5.3.1
* :pushpin: Automatic update of dependency hypothesis from 4.47.1 to 4.47.2
* :pushpin: Automatic update of dependency hypothesis from 4.47.0 to 4.47.1
* :pushpin: Automatic update of dependency hypothesis from 4.46.1 to 4.47.0
* :pushpin: Automatic update of dependency hypothesis from 4.46.0 to 4.46.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.23 to 0.19.24
* :pushpin: Automatic update of dependency hypothesis from 4.45.1 to 4.46.0
* :pushpin: Automatic update of dependency matplotlib from 3.1.1 to 3.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.22 to 0.19.23
* Remove unused imports
* :pushpin: Automatic update of dependency hypothesis from 4.45.0 to 4.45.1
* :pushpin: Automatic update of dependency hypothesis from 4.44.4 to 4.45.0
* :pushpin: Automatic update of dependency hypothesis from 4.44.2 to 4.44.4
* :pushpin: Automatic update of dependency pytest from 5.2.4 to 5.3.0
* :pushpin: Automatic update of dependency thoth-storages from 0.19.21 to 0.19.22
* :pushpin: Automatic update of dependency thoth-storages from 0.19.19 to 0.19.21
* Bump library versions
* Fix hashes representation in the generated Pipfile.lock
* Remove score filter stride
* Remove Dgraph leftovers
* Hotfix for obtained hashes
* Minor typo fixes
* Notify when a new pipeline product was produced
* Notify user when computing recommendations
* Update dependencies
* :pushpin: Automatic update of dependency thoth-storages from 0.19.18 to 0.19.19
* Fix coala complains
* Plotting environment variables were renamed
* Split adviser implementation for extensibility and testing
* :pushpin: Automatic update of dependency hypothesis from 4.44.1 to 4.44.2
* :pushpin: Automatic update of dependency hypothesis from 4.44.0 to 4.44.1
* :pushpin: Automatic update of dependency hypothesis from 4.43.8 to 4.44.0
* Add missing modules
* :pushpin: Automatic update of dependency thoth-storages from 0.19.17 to 0.19.18
* Update dependencies for new API
* :pushpin: Automatic update of dependency hypothesis from 4.43.6 to 4.43.8
* New thoth-python uses packaging's Version with different API
* Remove old test - solver does not support latest versions anymore
* Fix coala issues - reformat using black
* Use new solver implementation
* Update README to show how to run adviser locally
* :pushpin: Automatic update of dependency hypothesis from 4.43.5 to 4.43.6
* :pushpin: Automatic update of dependency thoth-storages from 0.19.15 to 0.19.17
* Adjust provenance-checker output to be in alaign with adviser and dm
* Revert "runtime_environment var should be dict in parameter"
* Fix exit code propagation to the main process
* runtime_environment var should be dict in parameter
* Release of version 0.6.1
* :pushpin: Automatic update of dependency hypothesis from 4.43.4 to 4.43.5
* :pushpin: Automatic update of dependency hypothesis from 4.43.3 to 4.43.4
* :pushpin: Automatic update of dependency hypothesis from 4.43.2 to 4.43.3
* Cache queries for retrieving enabled indexes
* :pushpin: Automatic update of dependency hypothesis from 4.43.1 to 4.43.2
* Use slots on pipeline unit instances
* Fix resolving direct dependencies when pagination is used
* :pushpin: Automatic update of dependency thoth-storages from 0.19.14 to 0.19.15
* :pushpin: Automatic update of dependency hypothesis from 4.43.0 to 4.43.1
* :pushpin: Automatic update of dependency hypothesis from 4.42.10 to 4.43.0
* :pushpin: Automatic update of dependency pytest-mypy from 0.4.1 to 0.4.2
* :pushpin: Automatic update of dependency hypothesis from 4.42.9 to 4.42.10
* :pushpin: Automatic update of dependency hypothesis from 4.42.8 to 4.42.9
* :pushpin: Automatic update of dependency hypothesis from 4.42.7 to 4.42.8
* :pushpin: Automatic update of dependency hypothesis from 4.42.6 to 4.42.7
* :pushpin: Automatic update of dependency hypothesis from 4.42.5 to 4.42.6
* :pushpin: Automatic update of dependency hypothesis from 4.42.4 to 4.42.5
* Release of version 0.6.0
* :pushpin: Automatic update of dependency hypothesis from 4.42.0 to 4.42.4
* Start using adaptive simulated annealing
* Release of version 0.6.0
* Use THOTH_ADVISE variable for consistency
* updated templates with annotations and param thoth-advise-value
* :pushpin: Automatic update of dependency methodtools from 0.1.1 to 0.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.11 to 0.19.12
* Do not use cached adviser
* :pushpin: Automatic update of dependency thoth-storages from 0.19.10 to 0.19.11
* :pushpin: Automatic update of dependency pytest from 5.2.1 to 5.2.2
* :pushpin: Automatic update of dependency methodtools from 0.1.0 to 0.1.1
* Pin thoth libraries which will have incompatible release
* :pushpin: Automatic update of dependency thoth-python from 0.6.4 to 0.6.5
* :pushpin: Automatic update of dependency pylint from 2.4.2 to 2.4.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.9 to 0.19.10
* :pushpin: Automatic update of dependency thoth-python from 0.6.3 to 0.6.4
* Add spaces to fix toml issues
* :pushpin: Automatic update of dependency thoth-common from 0.9.12 to 0.9.14
* :pushpin: Automatic update of dependency thoth-common from 0.9.11 to 0.9.12
* :pushpin: Automatic update of dependency pytest from 5.2.0 to 5.2.1
* :pushpin: Automatic update of dependency pytest-cov from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency pytest-cov from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency thoth-common from 0.9.10 to 0.9.11
* :pushpin: Automatic update of dependency pylint from 2.4.1 to 2.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.8 to 0.19.9
* :pushpin: Automatic update of dependency pytest from 5.1.3 to 5.2.0
* Fix duration
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.3 to 0.1.4
* :pushpin: Automatic update of dependency thoth-storages from 0.19.7 to 0.19.8
* Fix duration calculation
* Add duration to Adviser
* Re-anable operating system sieve
* Check we do not raise exception if os sieve wants to filter out all packages
* Introduce sieve for limiting number of latest versions in direct dependencies
* Add a new sieve for limiting pre-releases in direct dependencies
* Introduce semver sorting on direct dependnecies - sieve
* Just a minor change to make code great again
* :pushpin: Automatic update of dependency pylint from 2.4.0 to 2.4.1
* Introduce a stable sorting of packages in sieve context
* :pushpin: Automatic update of dependency thoth-storages from 0.19.6 to 0.19.7
* :pushpin: Automatic update of dependency pylint from 2.3.1 to 2.4.0
* use postgresql hostname from thoth configmap
* Add check for upstream tensorflow parsing
* :pushpin: Automatic update of dependency thoth-python from 0.6.2 to 0.6.3
* Adjust os sieve testsuite to reflect changes
* Introduce tests for checking correct parsing of AICoE releases
* :pushpin: Automatic update of dependency thoth-storages from 0.19.5 to 0.19.6
* :pushpin: Automatic update of dependency pytest from 5.1.2 to 5.1.3
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.2 to 0.1.3
* Add seldon and seldon-core to cached packages
* Create a check and test case to handle errors when trying to resolve unsolved packages
* :pushpin: Automatic update of dependency thoth-common from 0.9.9 to 0.9.10
* :pushpin: Automatic update of dependency thoth-storages from 0.19.4 to 0.19.5
* :pushpin: Automatic update of dependency thoth-common from 0.9.8 to 0.9.9
* Corrected typos
* :pushpin: Automatic update of dependency thoth-storages from 0.19.3 to 0.19.4
* Add Sentry DSN to build of adviser-cached
* :pushpin: Automatic update of dependency thoth-storages from 0.19.2 to 0.19.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.1 to 0.19.2
* Propagate deployment name to have reports when cache is built
* Propagate deployment name for sentry environment
* :pushpin: Automatic update of dependency thoth-storages from 0.19.0 to 0.19.1
* Fix testsuite
* Make coala happy
* Fix indentation issues
* Relock requirements
* Fix exception message
* Print out packages before each pipeline unit
* Implement solved sieve
* Changes needed for PostgreSQL migration
* Add a pipeline step which removes unsolved packages
* Do not use -e flag
* Store and restore cache on builds
* Add more packages to cache config file
* Adjust cache not to cache graph database adapter
* Create adviser cache during container build
* :pushpin: Automatic update of dependency thoth-python from 0.6.1 to 0.6.2
* :pushpin: Automatic update of dependency thoth-storages from 0.18.6 to 0.19.0
* Propagate runtime environment explicitly
* Use more generic env var names
* Remove performance related tests
* Drop generic performance querying
* Start using PostgreSQL in deployment
* :pushpin: Automatic update of dependency semantic-version from 2.8.1 to 2.8.2
* :pushpin: Automatic update of dependency pytest from 5.1.1 to 5.1.2
* :pushpin: Automatic update of dependency semantic-version from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency semantic-version from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency semantic-version from 2.7.0 to 2.7.1
* :pushpin: Automatic update of dependency semantic-version from 2.6.0 to 2.7.0
* Turn error into warning
* :pushpin: Automatic update of dependency pytest from 5.1.0 to 5.1.1
* Improve error message reported if no releases were found
* State how to integrate with Thoth in docs
* Do not use setuptools.find_namespace_packages() for now
* Start using Thoth's s2i base image
* Fix missing packages in adviser's package
* :pushpin: Automatic update of dependency pytest from 5.0.1 to 5.1.0
* :pushpin: Automatic update of dependency pydocstyle from 4.0.0 to 4.0.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.5 to 0.18.6
* :pushpin: Automatic update of dependency thoth-common from 0.9.7 to 0.9.8
* :pushpin: Automatic update of dependency thoth-common from 0.9.6 to 0.9.7
* Document how to make changes in the dependency graph while it changes
* A package can be removed in the previous sub-graphs removals
* :pushpin: Automatic update of dependency voluptuous from 0.11.5 to 0.11.7
* :pushpin: Automatic update of dependency thoth-python from 0.6.0 to 0.6.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.4 to 0.18.5
* Change name of Thoth template to make Coala happy
* Start using Thoth in OpenShift's s2i
* Adjust testsuite to use only_solved flag
* Ask graph database only for packages which were already solved
* Do not remove package tuples which are direct dependencies
* Do not treat builds as pre-releases
* Fix reference to variable - do not pass class
* Fix resolving direct dependencies based on the score
* add metadata
* :pushpin: Automatic update of dependency thoth-storages from 0.18.3 to 0.18.4
* Introduce sieves
* :pushpin: Automatic update of dependency thoth-common from 0.9.5 to 0.9.6
* Update docs with sieves
* Add docs for performance indicators
* :pushpin: Automatic update of dependency thoth-storages from 0.18.1 to 0.18.3
* :pushpin: Automatic update of dependency thoth-storages from 0.18.0 to 0.18.1
* :pushpin: Automatic update of dependency thoth-storages from 0.17.0 to 0.18.0
* Release of version 0.5.0
* :pushpin: Automatic update of dependency thoth-storages from 0.16.0 to 0.17.0
* Deinstantiate solver once it is no longer needed
* Fix instantiation of edges
* Adjust testsuite so that it works with new implementation
* :pushpin: Automatic update of dependency thoth-storages from 0.15.2 to 0.16.0
* Fix handling of additional pytest arguments in setup.py test
* Fix handling of additional pytest arguments in setup.py test
* Move logic of stack candidates preparation to finalization part
* :pushpin: Automatic dependency re-locking
* Remove unused import
* Improve some logger messages
* Rewrite core adviser logic for dependency graph manipulation
* Optimize retrieval of transitive dependencies to avoid list copies
* Optimize instantiation of objects when resolved from graph database
* :pushpin: Automatic update of dependency thoth-storages from 0.15.1 to 0.15.2
* :pushpin: Automatic update of dependency thoth-python from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency thoth-solver from 1.2.1 to 1.2.2
* :pushpin: Automatic update of dependency thoth-storages from 0.15.0 to 0.15.1
* Inform user that the missing release will be analyzed later on
* Remove invalid configuration entry APP_FILE in build config
* :pushpin: Automatic update of dependency thoth-storages from 0.14.8 to 0.15.0
* Fix transitive query - correctly propagate runtime information
* Improve warning message
* :pushpin: Automatic update of dependency thoth-common from 0.9.3 to 0.9.4
* Adjust testing recommendation type for now
* Remove score based cut-off step, observation reduction takes its position
* Add tests for observation based reduction
* Introduce observation reduction step to reduce subgraphs with no observations
* Add error message if no stacks were produced
* Report error if no recommendation was produced
* Introduce routines for iterating over develop and non-develop deps
* :sparkles: added the standard github configuration and a CODEOWNERS file
* Update lockfile
* Report used pipeline configuration of adviser to user
* Additional fixes and additions
* Minor changes
* Use CXXABI_1.3.8
* Use black for formatting
* Rework optimizations
* Adjust testsuite for new implementation
* Implement structure for dependency graph adjustment
* Report packages forming a found stack inside to a log
* Print out estimated number of stacks in scientific form
* Use only packages with known index
* Increase default adviser's requests and limits
* :pushpin: Automatic update of dependency thoth-storages from 0.11.4 to 0.14.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.11 to 0.9.0
* Add build trigger using generic webhook
* :pushpin: Automatic update of dependency pytest from 4.6.2 to 4.6.3
* Updated Readme to Dgraph examples
* :pushpin: Automatic update of dependency thoth-common from 0.8.7 to 0.8.11
* :pushpin: Automatic update of dependency pytest from 4.5.0 to 4.6.2
* Optimize package removal by working on indexes instead of package tuples
* Keep stats for package removals per step run
* Update documentation to respect current state
* Use uint16_t for representing packages in libdependency graph
* Simplify module structure to libdependency_graph library
* :pushpin: Automatic update of dependency thoth-common from 0.8.5 to 0.8.7
* Give adviser more time to process rest of the stacks in queue
* Provide better report to user on why adviser has stopped prematurely
* Use defaults of -1 for "unlimited" numbers in the cluster
* Parse a special value of -1 in the cluster to workaround click's errors
* Be more user-friendly in cluster logs
* Place toolchain cut after semver sort
* :pushpin: Automatic update of dependency pytest from 4.4.2 to 4.5.0
* :pushpin: Automatic update of dependency thoth-storages from 0.11.3 to 0.11.4
* Re-introduce filedump for fixes on long-lasting queries
* Log number of packages considered during dependency graph traversals
* Fix testsuite
* Create pipeline builder abstraction
* :pushpin: Automatic update of dependency thoth-storages from 0.11.2 to 0.11.3
* Release of version 0.4.0
* Fix coala issues
* :pushpin: Automatic update of dependency pytest from 4.4.1 to 4.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.11.1 to 0.11.2
* Use new method to obtain even large stacks from graph database
* :pushpin: Automatic update of dependency mock from 3.0.4 to 3.0.5
* :pushpin: Automatic update of dependency mock from 3.0.3 to 3.0.4
* Add information about library usage to pipeline and OpenShift job
* Build-time error filtering should be a very first step
* Propagate information about project runtime when checking buildtime error
* Fix issue happening in semver sort after a package is removed
* Remove toolchain to always use latest toolchain release
* Fix empty paths if there is raised an exception about invalid pkg removal
* :pushpin: Automatic update of dependency thoth-storages from 0.11.0 to 0.11.1
* Log message was missleading if package_tuple gets overwritten
* Provide fast-path when checking for already removed packages
* :pushpin: Automatic update of dependency pytest-cov from 2.6.1 to 2.7.1
* Implement build-time error filtering step
* :pushpin: Automatic update of dependency mock from 3.0.2 to 3.0.3
* :pushpin: Automatic update of dependency mock from 2.0.0 to 3.0.2
* :pushpin: Automatic update of dependency thoth-storages from 0.10.0 to 0.11.0
* Adjust provenance-checker template to use Dgraph
* Adjust Dependency Monkey to use Dgraph
* Adjust adviser template to use Dgraph
* Report overall score of a stack
* Remove is_solvable flag as done in Dgraph implementation
* Added the method to read version from project to conf.py
* Remove JanusGraph specific bits
* Do not depend on specific graph adapter from specific module
* Remove JanusGraph specific bits
* :pushpin: Automatic update of dependency thoth-storages from 0.9.7 to 0.10.0
* Trigger dependency monkey reports sync into graph database
* :pushpin: Automatic update of dependency pytest from 4.4.0 to 4.4.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.4 to 0.8.5
* Automatic update of dependency thoth-common from 0.8.3 to 0.8.4
* Create a workaround for click argument parsing from env vars
* :sparkles: added the Registry to be used for image pulling to the templates
* Adviser implementation using stack generation pipeline
* Automatic update of dependency thoth-common from 0.8.2 to 0.8.3
* Make Isis a proper adapter
* Automatic update of dependency thoth-common from 0.8.1 to 0.8.2
* Automatic update of dependency pytest from 4.3.1 to 4.4.0
* :bug: put some sane default for IMAGE_STREAM_NAMESPACE into each template
* hot fixing the timeout
* :sparkles: ImageStream Tag and Namespace
* Automatic update of dependency flexmock from 0.10.3 to 0.10.4
* Report premature end of stack stream
* Improve handling of long-running advises
* Add timeout seconds for adviser to let it submit results
* Top score is now 100
* Automatic update of dependency thoth-storages from 0.9.6 to 0.9.7
* Automatic update of dependency thoth-python from 0.4.6 to 0.5.0
* Make reports more human readable
* Fix testsuite
* Add Thoth's configuration file
* Make Isis instance attribute
* Always kill stack producer if there is no consumer of stacks
* Fix Coala issues
* Do not score more than requested number of latest stacks
* Introduce stack producer timeout
* Use Sphinx for documentation
* Fix some test errors
* Minor improvements
* Introduce parameters for limiting number of versions
* Introduce limit parameter to limit number of packages of a same type
* Fix usage of package_t in libdependency_graph.so
* Use safe_load
* Fix coala complains
* Report any exception which occurred during dependency monkey run
* Introduce checks on configuration
* Make sure Isis is a singleton
* Minor fix in logged message
* Use Isis API from configmap
* Introduce performance based queries to Isis
* Make Coala happy again
* Use black for formatting
* Add missing file
* Make sure versions are sorted, add tests for adviser
* Use black for formatting tests
* Fix tests
* Log runtime environment when computing advises
* Address coala issues
* Add an optional graph database adapter to reduce number of connections
* Take into account packages that are not installable into the given env
* Update README, state local run in a container
* Report CVE count only if there were some found
* Remove unused env variables
* Provide Sentry and Prometheus configuration
* Add metadata information shown in result reports
* Update Pipfile.lock
* Register provenance-checker to graph-sync-scheduler
* Use runtime information during runtime-specific resolution
* Use runtime environment as provided by user
* Use click echo instead of raw print
* Fix wrong order of tuples
* Provide generic stack information
* Score and report CVEs in the application stack to the user
* Report version on each run
* Do not be too verbose
* Open source documentation for dependency graph
* Document dependency graph build
* Report number of stacks scored
* Raise an exception on premature stream end
* Minor changes in comment and logging message
* Fix coala complains
* Wait for parent to score stacks in stack producer
* Add shared library for CentOS:7
* Provide Dockerfile for container-build
* Add linked library
* Initial dependency graph implementation in C++
* Correctly handle end of pipe
* Adjust .gitignore
* Run dependency graph as a standalone process, produce stacks into pipe
* It's already 2019
* Use proper loglevel for debug message
* Restrict indexes in dependency monkey runs
* Schedule graph syncs for adviser runs by graph-sync-operator
* Fix hashes collision in generated Pipfile.locks
* Implement dependency graph in C++
* Reuse connected graph adapter do reduce number of connections
* Amun API URL is used by Dependency Monkey
* Argument has to be named otherwise cannot be used as kwargs
* Increase run time for dependency monkey
* Propagate whitelisted sources to provenance checks
* Increase dependency monkey requests
* Correctly propagate job ids from workload operator
* Fix CI by updating thoth-python package
* Remove duplicit parameter from template
* Increase adviser job run limit
* Provide limit and count defaults in template
* Add coverage file to .gitignore
* Fix linter issues
* Fix wrong variable usage
* Report limit if limit was reached
* Remove unused imports
* Minor docs fixes
* Link to Dependency Monkey design document
* Add dependency monkey design document into docs
* Cut off and minor adjustmets
* Refactor test suite
* Use black for formatting
* Minor code refactoring, update requirements
* Use to_tuple_locked method as we have locked packages
* Fix missing import
* Construct Pipfile from resolved dependencies
* Print estimated number of software stacks
* Remove unused if statement
* Adjust dependency graph to use ids
* The decision function is now not optional
* Performance based scoring on exact stack match
* Do not pass None values in runtime environment to_dict
* Simplify work with dependency graph
* Fix handling of runtime environment, remove unused bits
* Avoid possibly inserting same package versions multiple times
* Utilize iter_dependencies locked method
* Use Python 3.6 by default
* Discard original sources when creating a new project
* Fix transitive dependencies retrieval
* Don't be too verbose in logs
* Mark jobs for cleanup
* Fetch digests from graph database in provenance checks
* Remove unused perf type
* Prepare dependency graph for graph slicing
* Minor fixes in decision functions
* Restructure scoring and decision functions
* Capture all the layers of dependencies
* Minor code refactoring
* Do not print reasoning into logs
* Fix injecting digests into generated stacks
* Minor fixes in dependency monkey
* Do not forget to package requirements.txt
* Minor fixes
* Raise an exception if no matching versions were found
* Consider also version when creating dependency graph
* Move relevant test files to thoth-python package
* Correctly fill stacks with package digests
* Remove files that were moved to thoth-python
* Include index when retrieving packages from the graph database
* Fill package hashes from the graph database
* Fix import errors
* Structure error reports correctly respecting schema
* Use thoth-python package
* CI fixes
* Fix janusgraph port
* Fix Coala complains
* Fixes and improvements
* Adjust temporary filling package hashes
* Fix missing import
* Pass index to be none always
* Fill package digets in advises
* Be consistent with subcommand naming
* Minor fix in docstring
* Introduce limit in dependency monkey template
* Introduce limit and count in adviser template
* First implementation of the Adviser class
* Default to stdout in dependency monkey
* Refactor dependency monkey so that it can be used in notebooks
* Perform deepcopy to report the correct input
* Fix filling hashes multiple times
* Seed and count can be empty string
* Convert required parameters to ints
* Fix environment variable name
* Place all decision functions at one place
* Improve logging
* Fix missing import
* Make sure queries respect python package names according to PEP
* Improve logging to make sure its visible what's going on
* Fix syntax error
* Fix import error
* Add missing import
* Add ability to submit a testing stack
* Issue warning when submitting to Amun API
* Remove duplicit code for loading Amun context
* Handle exceptions happening when submitting to Amun API
* CI fixes
* Add exception if constraints cannot be met
* Temporary fill package digests by querying PyPI index
* Always check which source in a warehouse
* Adjust output methods
* Adjust dependency monkey job template
* Minor improvements in implementation
* Aaa
* Fixes in the dependency graph implementation
* A package version is distinguished by name, version and index
* Add missing imports
* Check first layer of dependencies for validity
* Sanity check for adding non-locked version to lock
* Add testsuite for graph solver, dependency graph implementation
* Introduce graph Python solver
* Add testsuite for graph solver
* Introduce dependency graph
* Introduce graph Python solver
* reading README from file, its the long_description...
* Check for latest packages present on indexes
* Release of version 0.3.0
* fixing coala
* typo :/
* using thoth zuul jobs now
* Adjust setup.py to run testsuite correctly
* Run testsuite using setup.py
* Output to JSON in adviser
* Link PackageVersion to Source index used
* Report dict reporesentation of input instead of raw strings
* Add missing parameters to template
* Fix labels section in template
* Dependency monkey is a template
* Move dependency monkey to a job template
* Rename adviser template to be more clear
* Move from Pods to Jobs
* Directly pass adviser subcommand that should be run
* Introduce Dependency Monkey template
* Update README file
* Fix link to Thamos
* Introduce method for converting model to object
* Possible different source is info
* Add Codacy badge
* Fix testsuite respecting last changes
* Link to Pipenv docs for specifying package indexes
* Fix console figure
* State configured index in the report message
* Adjust reported issue id for possible different source
* Add installation section and adjust based on review comments
* Document provenance checks
* Quote relevant parts of string
* Add the current PyPI index to default warehouses
* Make artifact names lowercase by deafult
* Finish provenance reports
* Report directly findings in the provenance check report
* Adviser report should be always an array
* Report back error if we cannot conclude on application stack
* Ignore s2i's virtualenv in which adviser is run
* Increase memory for adviser due to OOMs
* Release of version 0.2.0
* Introduce add_source and add_package methods
* Do not use command in openshift template
* Release of version 0.1.1
* Setuptools find_packages does not respect namespaces
* Release of version 0.1.0
* Initial dependency lock
* Add forgotten lxml library for bs4 parsing
* Provide JanusGraph configuration in provenance-checker template
* Provide JanusGraph configuration in adviser template
* Pass full path to Python3 in s2i
* Make CLI executable
* Install forgotten packages
* Add execute bit to app.sh
* State we want to run provenance rather than adviser in template
* Revert "Provide entrypoint for OpenShift s2i"
* Provide a script to run desired subcommand
* Provide entrypoint for OpenShift s2i
* Remove unused script as adviser is s2i now
* Remove Dockerfile as adviser is s2i now
* Let's reuse parameter names from adviser
* Use local tensorflow index page for gathering versions
* Fix warehouse test
* Some CI fixes
* Initial dependency lock
* Let Kebechet pin down deps
* Remove old TODO
* Implement sorting based on semver
* Create abstraction classes
* Initial python recommendation implementation
* Automatic update of dependency thoth-common from 0.2.6 to 0.2.7
* Automatic update of dependency thoth-common from 0.2.5 to 0.2.6
* Introduce provenance checker template
* Automatic update of dependency thoth-storages from 0.5.1 to 0.5.2
* Automatic update of dependency thoth-common from 0.2.4 to 0.2.5
* Automatic update of dependency thoth-common from 0.2.3 to 0.2.4
* change the queue
* Automatic update of dependency thoth-common from 0.2.2 to 0.2.3
* Automatic update of dependency thoth-storages from 0.5.0 to 0.5.1
* Automatic update of dependency thoth-storages from 0.4.0 to 0.5.0
* Automatic update of dependency thoth-storages from 0.3.0 to 0.4.0
* Automatic update of dependency thoth-storages from 0.2.0 to 0.3.0
* Automatic update of dependency thoth-storages from 0.1.1 to 0.2.0
* State all template parameters
* Be consistent with label naming
* Update requirements.txt respecting requirements in Pipfile
* Automatic update of dependency thoth-common from 0.2.1 to 0.2.2
* Automatic update of dependency thoth-storages from 0.1.0 to 0.1.1
* Add app=thoth label to pod template
* Adjust template labels
* Fix image stream kind in template
* Fix coala naming convention configuration
* Add OpenShift templates for deployment
* Automatic update of dependency thoth-storages from 0.0.33 to 0.1.0
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Initial dependency lock
* Delete Pipfile.lock for relocking dependencies
* relocked, travis removed, zuul added
* Automatic update of dependency thoth-common from 0.0.9 to 0.1.0
* Automatic update of dependency thoth-analyzer from 0.0.6 to 0.0.7
* Automatic update of dependency thoth-analyzer from 0.0.5 to 0.0.6
* Automatic update of dependency thoth-storages from 0.0.32 to 0.0.33
* Automatic update of dependency thoth-storages from 0.0.29 to 0.0.32
* Automatic update of dependency thoth-common from 0.0.6 to 0.0.9
* Update thoth packageswq
* Automatic update of dependency thoth-storages from 0.0.25 to 0.0.28
* Do not restrict Thoth packages
* Another CI fix
* Another CI fix
* Run coala in non-interactive mode
* CI fix
* Run coala in CI
* Create OWNERS
* Remove dependencies.yml
* Use coala for code checks
* Fix package name in license header
* Add LICENSE and license headers
* Use thoth's common logging
* Add README file
* Version 0.0.2
* State only direct dependencies in requirements.txt
* Version 0.0.1
* Update dependencies
* Update thoth-storages from 0.0.3 to 0.0.4
* Rename environment variables to respect user-api arguments passing
* Create initial dependencies.yml config
* Change envvar for --requirements option
* Expose advise_pypi function
* Version 0.0.0
* Build adviser image in CI
* Fix naming typo
* Initial template for implementation
* Initial project import

## Release 0.13.0 (2020-07-23T12:27:28)
* Stack information is never None
* :pushpin: Automatic update of dependency hypothesis from 5.20.2 to 5.20.3 (#1073)
* Add pull request template (#1065)
* :pushpin: Automatic update of dependency hypothesis from 5.19.3 to 5.20.2
* :pushpin: Automatic update of dependency matplotlib from 3.2.2 to 3.3.0
* :pushpin: Automatic update of dependency thoth-storages from 0.24.3 to 0.24.4
* State aicoe and upstream specific build info for TensorFlow (#1070)
* Add information about backports to stack info (#1069)
* Fix pre-commit complains
* remove file which is unused
* Introduce boots for Python backports
* Extend recommendation types
* Remove latest versions limitation
* Release of version 0.12.0 (#1056)
* :pushpin: Automatic update of dependency hypothesis from 5.19.0 to 5.19.3 (#1055)
* :pushpin: Automatic update of dependency pytest-timeout from 1.4.1 to 1.4.2 (#1054)
* fix pytest failures by moving attributes due to bad instantiation order
* :pushpin: Automatic update of dependency thoth-storages from 0.24.2 to 0.24.3 (#1051)
* Release of version 0.11.0 (#1052)
* Require newer version of attrs when running mypy
* Introduce a sieve to filter out incompatible setuptools for Python 3.6
* Change some mypy typing to comments to get aroudn subscripting errors
* :pushpin: Automatic update of dependency thoth-storages from 0.24.0 to 0.24.2 (#1048)
* MyPy type annotations and checking
* Document Wrap pipeline unit type (#1047)
* Remove tempalates handled by thoth-application (#1046)
* add pre-commit and fix all except mypy errors
* :sparkles: added the cyborg-supervisors team to prow univers, after we have had it as a github team
* Add link to Provenance Checks (#1045)
* Introduce a mock score step for experimenting with predictors
* Implement a pipeline step for recommending AVX2 builds of AICoE Tenso… (#1020)
* :pushpin: Automatic update of dependency hypothesis from 5.18.3 to 5.19.0 (#1043)
* Introduce a wrap for recommending Python3.8 on RHEL 8.2 (#1042)
* :pushpin: Automatic update of dependency hypothesis from 5.18.0 to 5.18.3 (#1041)
* Remove provenance-checker job template
* Remove adviser job template
* Remove Dependency Monkey job template
* Update OWNERS
* :pushpin: Automatic update of dependency hypothesis from 5.16.3 to 5.18.0
* :pushpin: Automatic update of dependency thoth-storages from 0.23.2 to 0.24.0
* Remove latest versions limitation
* Adjust MANIFEST.in
* :pushpin: Automatic update of dependency hypothesis from 5.16.1 to 5.16.3
* :pushpin: Automatic update of dependency matplotlib from 3.2.1 to 3.2.2
* :pushpin: Automatic update of dependency thoth-storages from 0.23.0 to 0.23.2
* :pushpin: Automatic update of dependency thoth-python from 0.9.2 to 0.10.0
* add secondsAfterFailure
* Increase time for SLI
* Remove dependency
* Include each marker of a type just once
* Dependency relocking to fix CI
* Release of version 0.10.0
* :pushpin: Automatic update of dependency thoth-storages from 0.22.12 to 0.23.0
* Disable setup.py processing in s2i builds
* :pushpin: Automatic update of dependency hypothesis from 5.16.0 to 5.16.1
* Respect review comments
* Update docs/source/deployment.rst
* Call destructor of the final state explictly once done with the state
* Note down beam width once the resolution is terminated
* Document deployment and configuring adviser in a deployment
* More optimizations to speed up adviser
* Coala fix
* :recycle: Removed unnecessary tempalates
* Do not use OrderedDict for internal state representation
* Add a boot for tracing memory consumption
* Preserve order in pre and post run methods
* Add a check for available platforms
* adjust kebechet run-results workflow
* add conditional to workflow
* add default output params
* indent to follow coala styling
* Added black
* :pushpin: Automatic update of dependency pytest from 5.4.2 to 5.4.3
* Added pyproject.toml
* Use trigger integration in adviser workflow
* add is_missing to mock tests
* correct typo
* use workflow-helpers
* Add outputs
* remove imagestream envs
* Change to trigger integration task
* kebechet->KEBECHET because of enum values
* remove image stream params
* add ssh to adviser workflow
* secret mount WorkflowTemplate->Workflow
* add ssh volume mount
* remove debugging step
* added a 'tekton trigger tag_release pipeline issue'
* add volume mount for proper output
* :pushpin: Automatic update of dependency thoth-storages from 0.22.11 to 0.22.12
* fix parameter passing
* change env name
* :pushpin: Automatic update of dependency hypothesis from 5.15.1 to 5.16.0
* add run-result to adviser workflow
* add is missing resolver
* use THOTH_ in fron env
* use workflow-helpers for tasks
* Release of version 0.9.5
* :pushpin: Automatic update of dependency pytest-cov from 2.8.1 to 2.9.0
* :pushpin: Automatic update of dependency thoth-storages from 0.22.10 to 0.22.11
* :pushpin: Automatic update of dependency hypothesis from 5.15.0 to 5.15.1
* Add unsolved-package-handler to adviser workflow
* clean up tasks, remove unnecessary stuff
* first attempt at kebechet run results task
* Remove sieve and use inital query
* :pushpin: Automatic update of dependency hypothesis from 5.14.0 to 5.15.0
* update versions
* Use thoth-toolbox
* Use thamos from upstream
* :pushpin: Automatic update of dependency packaging from 20.3 to 20.4
* added to do for thoth.storages
* Fix links to docs and add s2i migration video
* create sieve for missing package versions
* :pushpin: Automatic update of dependency toml from 0.10.0 to 0.10.1
* :pushpin: Automatic update of dependency hypothesis from 5.13.1 to 5.14.0
* :pushpin: Automatic update of dependency hypothesis from 5.11.0 to 5.13.1
* :pushpin: Automatic update of dependency thoth-storages from 0.22.9 to 0.22.10
* :pushpin: Automatic update of dependency pytest from 5.4.1 to 5.4.2
* Improve message provided to user
* :pushpin: Automatic update of dependency hypothesis from 5.10.5 to 5.11.0
* Point to s2i-example-migration
* :pushpin: Automatic update of dependency thoth-storages from 0.22.8 to 0.22.9
* :pushpin: Automatic update of dependency hypothesis from 5.10.4 to 5.10.5
* Sync variable fix for provenance check
* Update dependencies to pass the test suite
* Implement platform boot
* Adviser Dev env var added to template
* Include MKL warning also in dependency monkey runs
* intel-tensorflow is built with MKL support
* :pushpin: Automatic update of dependency hypothesis from 5.9.1 to 5.10.0
* Handle exit code regardless core file is produced
* :pushpin: Automatic update of dependency hypothesis from 5.9.0 to 5.9.1
* fixed coala errors
* fixed coala complaint
* fixed the apiVersion of all the OpenShift Templates
* :pushpin: Automatic update of dependency hypothesis from 5.8.6 to 5.9.0
* :pushpin: Automatic update of dependency hypothesis from 5.8.5 to 5.8.6
* :pushpin: Automatic update of dependency hypothesis from 5.8.4 to 5.8.5
* :pushpin: Automatic update of dependency hypothesis from 5.8.3 to 5.8.4
* Create a wrap for Intel's MKL env variable configuration
* :pushpin: Automatic update of dependency hypothesis from 5.8.2 to 5.8.3
* :pushpin: Automatic update of dependency hypothesis from 5.8.1 to 5.8.2
* :pushpin: Automatic update of dependency hypothesis from 5.8.0 to 5.8.1
* Fixed readme link
* consistency in using secrets
* Fix liveness probe
* Add missing liveness probe to advise workflow
* Export variable as adviser forks a sub-process
* Release of version 0.9.4
* Empty commit to trigger the new release
* Introduce heat up phase for the latest predictor
* Setup TTL strategy to reduce preassure causing OOM
* :pushpin: Automatic update of dependency pytest-mypy from 0.6.0 to 0.6.1
* Adjust test accordingly
* Adjust the message produced
* Reduce beam width to address OOM issues for large stacks in the cluster
* Improve message when adviser is stopped based on CPU time
* Recommendation type is not lowercase
* Disable provenance checks
* Release of version 0.9.3
* Release of version 0.9.2
* Fixes needed to make this package available on PyPI
* Tweak temperature function for ASA, TD and MCTS
* Adjust parameters in deployment
* Release of version 0.9.1
* Fix bug causing adviser halt for shared resolved packages
* Release of version 0.9.0
* Fix info message causing issues when the beam is empty
* Add fext to application requirements
* Remove unusued parameter
* Re-enable fext for beam's internal state handling
* consistency in openshift templates to run provenance
* :pushpin: Automatic update of dependency pyyaml from 3.13 to 5.3.1
* Introduce heat up part of MCTS
* Prioritize releases by AICoE
* :pushpin: Automatic update of dependency thoth-solver from 1.5.0 to 1.5.1
* :pushpin: Automatic update of dependency thoth-storages from 0.22.6 to 0.22.7
* Do not keep beam history if not necessary
* :pushpin: Automatic update of dependency thoth-storages from 0.22.5 to 0.22.6
* Add option consider/do not consider dev dependencies
* Increase timeout for running tests
* Increase timeout for running tests
* No need to initialize logging multiple times
* Minor fixes in api_compat
* Use MCTS predictor for stable and testing recommendations
* Optimize termial of n computation
* Fix scoring of the user stack
* Optimize termial of n computation
* Address issues spotted in resolution when MCTS is used
* Document provenance checks
* :pushpin: Automatic update of dependency pyyaml from 5.3.1 to 3.13
* Fix context handling when passing in as raw JSON
* Fix dependency monkey invocation flag
* :pushpin: Automatic update of dependency hypothesis from 5.7.2 to 5.8.0
* :pushpin: Automatic update of dependency hypothesis from 5.7.1 to 5.7.2
* :pushpin: Automatic update of dependency pyyaml from 3.13 to 5.3.1
* Log resolver progress each 10%
* :pushpin: Automatic update of dependency hypothesis from 5.7.0 to 5.7.1
* Missing parenthesis prevent sync on Ceph
* Test suite and duplicate code refactoring
* Fix docstring
* Updates to the new beam API
* Reduce memory footprint
* Implement MCTS predictor
* Additional changes for TD
* Fix annealing testsuite
* Introduce Temporal Difference based predictor using annealing based scheduling
* Fix coala complains
* Introduce user stack scoring as a base for comparision
* Make sure the error report for adviser exceptions is always present
* :pushpin: Automatic update of dependency thoth-storages from 0.22.4 to 0.22.5
* :pushpin: Automatic update of dependency thoth-storages from 0.22.3 to 0.22.4
* Rewrite beam so that it does not use fext
* Wrong variable name
* :pushpin: Automatic update of dependency hypothesis from 5.6.1 to 5.7.0
* :pushpin: Automatic update of dependency hypothesis from 5.6.0 to 5.6.1
* :pushpin: Automatic update of dependency matplotlib from 3.2.0 to 3.2.1
* Correct space for exception
* Fix handling of environment markers when multiple packages use marker
* Release of version 0.8.0
* Fix defaults in CLI, they are lowercase now
* Resolver does not check runtime environment specification during state resolving
* Add Python version boot
* Start using fext in adviser
* :pushpin: Automatic update of dependency pytest from 5.3.5 to 5.4.1
* :pushpin: Automatic update of dependency pytest-mypy from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency pyyaml from 5.3 to 3.13
* Adjust string for image and key
* Add registry env variables
* remove default values
* Generalize variables for Ceph for the workflows
* fixed coala
* Fixed error log and old api
* Prevent from OSError when the requirements string is too large
* :pushpin: Automatic update of dependency click from 7.0 to 7.1.1
* :pushpin: Automatic update of dependency click from 7.0 to 7.1.1
* :pushpin: Automatic update of dependency packaging from 20.1 to 20.3
* :pushpin: Automatic update of dependency matplotlib from 3.1.3 to 3.2.0
* Add voluptous to requirements.txt
* Introduce package source index sieve for filtering based on index
* Remove typeshed
* UBI boot has to be before boot that checks RHEL version
* Solved software environment has to be run after changes to environment
* Adjust testsuite
* Propagate the original runtime environment used in resolving in pipeline products
* Use the correct condition for checking parameters
* Increase timeout for pytest tests
* Fix test suite
* Ignore the run logger for dependency monkey runs
* Fix type
* Propagate metdata to products
* Allow context to be passed as a file
* Update thoth-storages to address import issue
* Update dependencies
* Propagate metdata to products
* Bump template version
* OpenShift templates are referenced by label
* Update dependencies
* Distinguish different types of errors of adviser runs for SLO
* Child exists with status code 256
* Do not overwrite results computed in the forked process
* Adviser workflow when using Thamos CLI
* Add URLs to GitHub and PyPI
* :pushpin: Automatic update of dependency hypothesis from 5.5.3 to 5.5.4
* :pushpin: Automatic update of dependency hypothesis from 5.5.2 to 5.5.3
* No deafult value null for metadata
* :pushpin: Automatic update of dependency hypothesis from 5.5.1 to 5.5.2
* :pushpin: Automatic update of dependency thoth-storages from 0.22.1 to 0.22.2
* Adjust version and use correct keys
* :pushpin: Automatic update of dependency thoth-storages from 0.22.0 to 0.22.1
* Add default value when user does not provided Pipfile.lock
* Add template for releases
* Revert to flexmock(GraphDatabase)
* GraphDatabase->graph
* follow python standards
* add more flex
* back to should receive after storages update
* :pushpin: Automatic update of dependency thoth-storages from 0.21.11 to 0.22.0
* Update .thoth.yaml
* change to should call
* initialize graph
* abi-compat-sieve tests
* :pushpin: Automatic update of dependency hypothesis from 5.4.2 to 5.5.1
* Run workflow even if adviser fails
* add env variable
* Use correct storage to store results
* State thoth-s2i in integration
* Propagate information about missing configuration in report
* Add a wrap for adding info about no observations
* Update docstring
* :pushpin: Automatic update of dependency hypothesis from 5.4.1 to 5.4.2
* Make decision type and recommendation type lowercase
* Modify parameters for GitHub App
* remove metadata
* Move cache to storage level
* cache query results
* shortcut if package requires no symbols
* self.image_symbols is now a set
* Create abi sieve
* Adjust script in finished webhook
* adjust script in finished webhook template
* remove service account argo
* Adjust inner workflow for GitHub App
* :pushpin: Automatic update of dependency hypothesis from 4.57.1 to 5.4.1
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.3 to 1.1.4
* :pushpin: Automatic update of dependency matplotlib from 3.1.2 to 3.1.3
* :pushpin: Automatic update of dependency pytest from 5.3.4 to 5.3.5
* Do identity check instead of equality check
* Capture CLI parameters in resolver's context
* :pushpin: Automatic update of dependency thoth-storages from 0.21.10 to 0.21.11
* Log information about future solver runs of unsolved dependencies
* Fix Coala complains
* Introduce normalization of score returned by step units
* Introduce RHEL version boot for RHEL major releases
* :pushpin: Automatic update of dependency packaging from 20.0 to 20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.21.9 to 0.21.10
* :pushpin: Automatic update of dependency thoth-storages from 0.21.8 to 0.21.9
* :pushpin: Automatic update of dependency pytest from 5.3.3 to 5.3.4
* :pushpin: Automatic update of dependency thoth-storages from 0.21.7 to 0.21.8
* Try its best to always come up with a latest stack
* Rename template for workflow-operator
* Disable dry run for Thoth's recommendations
* Fix a bug when env is not fully specified and env marker filters out deps
* :pushpin: Automatic update of dependency pytest from 5.3.2 to 5.3.3
* Do not show information about results being submitted to result API
* Use WARNING log level in thoth.common
* Ask for thoth.adviser log to have clean logs and respect log configuration
* Use epsilon greedy strategy for picking the latest version
* Adjust limit latest versions and beam width
* Introduce version constrain sieve pipeline unit
* Assign correct default value
* Do not keep history in adviser runs
* Fix default value key
* Add missing metadata to adviser job template
* Fix handling of --dry-run parameter
* Show version of direct dependencies explictly
* Include random decision stride only explictly
* Introduce stride for getting one version in a stack
* :pushpin: Automatic update of dependency thoth-storages from 0.21.6 to 0.21.7
* Move log_once to utils function
* Optimize state removal out of beam
* Terminal output is slow, log only after N stacks generated
* Optimize handling of the top score kept in beam
* Prevent annealing from being stuck
* Fix bug shown when sieves or steps filtered out dependecies
* Log stack counter in a more human readable form
* Propagate also expanded package tuple to reward signal
* Mention behavior for the default value
* Refactor keep history into an utility function for reusability
* Log pipeline speed
* Release of version 0.7.3
* Raise an error if no direct dependencies were found
* Report error on resolution failure
* Create more descriptive message
* Add tests for no dependencies cases during resolution
* Rebase and simplify code
* Fix log message reported
* Log interesting checkpoints during resolution to user
* Reward signal now propagates state for which the reward signal is computed
* Introduce a method for getting a state by its id
* Fix exception error messages produced
* Fix beam method signatures
* Remove unused import statement
* Introduce approximating latest predictor
* :pushpin: Automatic update of dependency thoth-storages from 0.21.5 to 0.21.6
* Re-add state with no unresolved dependencies back to beam on resolution
* Remvoe accidentally committed print statement
* Introduce finalizers for predictor's memory footprint optimization
* Predictor should pick key to beam
* Introduce assigned context to predictor
* Extend docs with MDP
* :pushpin: Automatic update of dependency thoth-storages from 0.21.4 to 0.21.5
* Release of version 0.7.2
* :pushpin: Automatic update of dependency thoth-storages from 0.21.3 to 0.21.4
* Release of version 0.7.1
* Set random walk as default predictor for Dependency Monkey
* Inspection endpoint does not accept runtime environment
* Fix submitting inspections
* :pushpin: Automatic update of dependency thoth-storages from 0.21.2 to 0.21.3
* Add a boot that checks for fully specified environment
* Add ability to block pipeline units during pipeline build
* :pushpin: Automatic update of dependency thoth-storages from 0.21.1 to 0.21.2
* :pushpin: Automatic update of dependency thoth-storages from 0.21.0 to 0.21.1
* Bump template patch version
* Fix decision type environment variable name
* There is no option for DEPENDENDENCY_MONKEY_LIMIT
* :pushpin: Automatic update of dependency thoth-storages from 0.20.6 to 0.21.0
* did not save merge before merging
* Yield from iterator to keep context
* Add a note on requirements.txt
* State pip/pip-compile support in integration section
* Correct wrong key in template
* Adjust testsuite accordingly
* Sort direct dependencies for reproducible resolver runs
* :pushpin: Automatic update of dependency thoth-python from 0.9.0 to 0.9.1
* Do not prefer recent versions in random walk and sampling
* Optimize arithmetics a bit
* Be more explicit about the function call in docstring
* Use r""" if any backslashes in a docstring
* Introduce termial function to prefer more recent versions randomly
* Extend resolver testsuite
* :pushpin: Automatic update of dependency thoth-solver from 1.4.1 to 1.5.0
* Adjust env variable name
* :pushpin: Automatic update of dependency thoth-python from 0.8.0 to 0.9.0
* :pushpin: Automatic update of dependency thoth-storages from 0.20.5 to 0.20.6
* Boots can raise not acceptable
* Do not run adviser from bc in debug mode
* Do not run adviser from bc in debug mode
* Add testsuite for solved software environment pipeline unit
* Register solved software environment boot
* Sort reported environments
* Introduce solved software environment boot
* :pushpin: Automatic update of dependency thoth-storages from 0.20.4 to 0.20.5
* :pushpin: Automatic update of dependency thoth-python from 0.7.1 to 0.8.0
* :pushpin: Automatic update of dependency pytest-timeout from 1.3.3 to 1.3.4
* :pushpin: Automatic update of dependency pyyaml from 5.2 to 5.3
* :pushpin: Automatic update of dependency thoth-storages from 0.20.3 to 0.20.4
* :pushpin: Automatic update of dependency thoth-storages from 0.20.2 to 0.20.3
* Beam is part of context, no need to pass it explictly
* Fixed missing emptyDir in the Adviser Workflow
* Limit number of software stacks to 1 on LATEST
* Adjust testsuite to correctly propagate reward signal
* Introduce beam.reset()
* Introduce beam.get_random()
* Reward signal now accepts resolver context
* Remove environment serialization - it takes some time during runs
* Random walk and initial configuration change
* Fixed too many blank lines in Workflow template
* Fixed adviser Workflow template
* :pushpin: Automatic update of dependency thoth-storages from 0.20.1 to 0.20.2
* Happy new year!
* :pushpin: Automatic update of dependency thoth-storages from 0.20.0 to 0.20.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.30 to 0.20.0
* :pushpin: Automatic update of dependency hypothesis-auto from 1.1.2 to 1.1.3
* :pushpin: Automatic update of dependency hypothesis from 4.57.0 to 4.57.1
* :pushpin: Automatic update of dependency hypothesis from 4.56.3 to 4.57.0
* Adjust documentation for the new predictor run API
* :pushpin: Automatic update of dependency hypothesis from 4.56.2 to 4.56.3
* :pushpin: Automatic update of dependency hypothesis from 4.56.1 to 4.56.2
* Predictors now return also packages that should be resolved from states
* Fix docstring of boot
* Add few more asserts
* Add tests for leaf node expansion with marker set to False
* Add a boot for mapping UBI to RHEL
* Exclude reports from run error in Sentry
* :pushpin: Automatic update of dependency hypothesis from 4.56.0 to 4.56.1
* :pushpin: Automatic update of dependency hypothesis from 4.55.4 to 4.56.0
* :pushpin: Automatic update of dependency hypothesis from 4.55.3 to 4.55.4
* :pushpin: Automatic update of dependency hypothesis from 4.55.2 to 4.55.3
* Add checks for special cases when environment markers apply to leaf nodes
* Register CVE step only for STABLE and TESTING recommendation types
* Automatically choose the most appropriate predictor based on CLI
* :sparkles: added an Argo Workflow to run an advise
* Adjust API and tests to the new change
* :see_no_evil: ignoring the xml report coverage file
* :pushpin: Automatic update of dependency thoth-storages from 0.19.27 to 0.19.30
* :pushpin: Automatic update of dependency hypothesis from 4.55.1 to 4.55.2
* Format using black
* Counter is no longer used
* Improve multi-key sorting of states in the beam
* Log warning about shared dependencies in the dependency graph
* :pushpin: Automatic update of dependency hypothesis from 4.55.0 to 4.55.1
* Do not retrieve markers during resolution
* Fix logging format expansion
* Log also beam size
* :pushpin: Automatic update of dependency hypothesis from 4.54.2 to 4.55.0
* Match only first part of tuple
* Fix computing top state in the beam
* Simplify creation of initial states
* Adjust relative order for steps registration
* :pushpin: Automatic update of dependency hypothesis from 4.54.1 to 4.54.2
* :pushpin: Automatic update of dependency hypothesis from 4.54.0 to 4.54.1
* Fix Coala complains
* Keep track of dependencies added
* Accepted final states can be 0
* Revert "Add new iteration method for sieves and steps"
* Make temperature function a function of iteration as well
* :pushpin: Automatic update of dependency hypothesis from 4.53.3 to 4.54.0
* :pushpin: Automatic update of dependency hypothesis from 4.53.2 to 4.53.3
* :pushpin: Automatic update of dependency pytest from 5.3.1 to 5.3.2
* Keep beam in context
* Implement a dropout step
* :pushpin: Automatic update of dependency hypothesis from 4.53.1 to 4.53.2
* Bump version in templates
* Fork only in the cluster
* Fix coala complains
* Document new iteration round methods
* Add new iteration method for sieves and steps
* Adjust docs for limit latest versions
* Always bind context
* Add tests for limit latest versions and semver sort
* Adjust test suite
* Adjust semantics of limit latest versions
* Add a note on shared dependencies
* Refactor plotting primitives
* Do not keep history if not plotting in CLI
* Rename and move history related bits in predictors
* Remove debug print
* Implement resolving stop when SIGINT is caught
* Use SIGINT in liveness probe
* Implement version clash boot
* Tests for hill climbing and sampling, minor refactoring
* Add locked sieve
* Beam width is stated two times
* Document OpenShift s2i build integration
* Fix issue when there are no unresolved dependencies left in the state
* Document beam width and how to plot it
* Document build-watcher
* Log correct file location for beam history plots
* :pushpin: Automatic update of dependency hypothesis from 4.53.0 to 4.53.1
* Document build-watcher
* :pushpin: Automatic update of dependency hypothesis from 4.52.0 to 4.53.0
* :pushpin: Automatic update of dependency hypothesis from 4.51.1 to 4.52.0
* :pushpin: Automatic update of dependency hypothesis from 4.51.0 to 4.51.1
* Add a link to Thamos documentation
* Point to Thamos documentation instead of GitHub repo
* Add a link to performance article published
* Add architecture diagram
* State also core repository
* docs: Architecture overview section
* :pushpin: Automatic update of dependency hypothesis from 4.50.8 to 4.51.0
* Remove graph cache bits no longer used
* Document pipeline configuration instrumentation
* Point documentation to other libraries
* Add developer's guide to documentation
* Use RHEL instead of UBI
* Update Thoth configuration file and Thoth's s2i configuration
* Remove old comment
* Add note to step docs - no adjustment in step or beam
* No need to clone a state before running steps
* Do not show not relevant logs to users
* Point to source code documentation for described methods
* Fix exit code propagation of the forked child
* Add validation of count and limit resolver attributes
* Produce more descriptive message if any of direct dependencies was not resolved
* :pushpin: Automatic update of dependency thoth-storages from 0.19.26 to 0.19.27
* Adjust parameters for adviser and dependency-monkey
* Propagate information about package that has CVE to justification in CVE step
* :pushpin: Automatic update of dependency hypothesis from 4.50.7 to 4.50.8
* :pushpin: Automatic update of dependency thoth-storages from 0.19.25 to 0.19.26
* :pushpin: Automatic update of dependency thoth-solver from 1.4.0 to 1.4.1
* Add Google Analytics
* Fix reference to sieve in docs
* Fix references to the source code
* Release of version 0.7.0
* :pushpin: Automatic update of dependency hypothesis from 4.50.6 to 4.50.7
* Graph cache is not used anymore
* Fix coala complains
* Enhance exception
* Give more information dependencies were not resolved
* Set beam width template in the adviser template job
* Fix coala complains
* Fix coala complains
* Some docs for readers and developers
* Fix stride signature
* Fix boot docstring
* Fix tests
* Optimizations of beam
* Fix Coala complains
* Use generators to retrieve items
* Provide property for run executor that prints report
* Provide an option to configure pipeline via file/dict
* Log package version before pipeline step execution
* Remove unused method
* Test simulated annealing primitives, refactor core annealing part
* Step should not return Nan/Inf
* Use backtracking to run steps
* Make coala happy again
* Add tests for two corner cases for package clash during resolution
* Fix beam top manipulation
* Add logic for registering a final state
* Add dependencies only if they were previously considered based on env marker
* Remove print used during debugging
* :pushpin: Automatic update of dependency hypothesis from 4.50.5 to 4.50.6
* :pushpin: Automatic update of dependency hypothesis from 4.50.4 to 4.50.5
* :pushpin: Automatic update of dependency hypothesis from 4.50.3 to 4.50.4
* :pushpin: Automatic update of dependency hypothesis from 4.50.2 to 4.50.3
* Change default number of stacks returned on call
* Fix parameter to adviser CLI
* Adjust logged messages
* Make beam instance of resolver
* Adjust limit latest versions signature, do not perform shallow copy
* Sieve now accepts and returns a generator of package versions
* :pushpin: Automatic update of dependency thoth-storages from 0.19.24 to 0.19.25
* Address review comments
* :pushpin: Automatic update of dependency hypothesis from 4.50.1 to 4.50.2
* Fix coala issues
* Fix typo in docstring
* :pushpin: Automatic update of dependency hypothesis from 4.50.0 to 4.50.1
* :pushpin: Automatic update of dependency hypothesis from 4.49.0 to 4.50.0
* Optimize retrieval of environment markers
* :pushpin: Automatic update of dependency hypothesis from 4.48.0 to 4.49.0
* :pushpin: Automatic update of dependency hypothesis from 4.47.4 to 4.48.0
* Even more tests
* :pushpin: Automatic update of dependency hypothesis from 4.47.3 to 4.47.4
* Propagate document id into jobs
* More tests
* :pushpin: Automatic update of dependency hypothesis from 4.47.2 to 4.47.3
* :pushpin: Automatic update of dependency pytest from 5.3.0 to 5.3.1
* :pushpin: Automatic update of dependency hypothesis from 4.47.1 to 4.47.2
* :pushpin: Automatic update of dependency hypothesis from 4.47.0 to 4.47.1
* :pushpin: Automatic update of dependency hypothesis from 4.46.1 to 4.47.0
* :pushpin: Automatic update of dependency hypothesis from 4.46.0 to 4.46.1
* :pushpin: Automatic update of dependency thoth-storages from 0.19.23 to 0.19.24
* :pushpin: Automatic update of dependency hypothesis from 4.45.1 to 4.46.0
* :pushpin: Automatic update of dependency matplotlib from 3.1.1 to 3.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.22 to 0.19.23
* Remove unused imports
* :pushpin: Automatic update of dependency hypothesis from 4.45.0 to 4.45.1
* :pushpin: Automatic update of dependency hypothesis from 4.44.4 to 4.45.0
* :pushpin: Automatic update of dependency hypothesis from 4.44.2 to 4.44.4
* :pushpin: Automatic update of dependency pytest from 5.2.4 to 5.3.0
* :pushpin: Automatic update of dependency thoth-storages from 0.19.21 to 0.19.22
* :pushpin: Automatic update of dependency thoth-storages from 0.19.19 to 0.19.21
* Bump library versions
* Fix hashes representation in the generated Pipfile.lock
* Remove score filter stride
* Remove Dgraph leftovers
* Hotfix for obtained hashes
* Minor typo fixes
* Notify when a new pipeline product was produced
* Notify user when computing recommendations
* Update dependencies
* :pushpin: Automatic update of dependency thoth-storages from 0.19.18 to 0.19.19
* Fix coala complains
* Plotting environment variables were renamed
* Split adviser implementation for extensibility and testing
* :pushpin: Automatic update of dependency hypothesis from 4.44.1 to 4.44.2
* :pushpin: Automatic update of dependency hypothesis from 4.44.0 to 4.44.1
* :pushpin: Automatic update of dependency hypothesis from 4.43.8 to 4.44.0
* Add missing modules
* :pushpin: Automatic update of dependency thoth-storages from 0.19.17 to 0.19.18
* Update dependencies for new API
* :pushpin: Automatic update of dependency hypothesis from 4.43.6 to 4.43.8
* New thoth-python uses packaging's Version with different API
* Remove old test - solver does not support latest versions anymore
* Fix coala issues - reformat using black
* Use new solver implementation
* Update README to show how to run adviser locally
* :pushpin: Automatic update of dependency hypothesis from 4.43.5 to 4.43.6
* :pushpin: Automatic update of dependency thoth-storages from 0.19.15 to 0.19.17
* Adjust provenance-checker output to be in alaign with adviser and dm
* Revert "runtime_environment var should be dict in parameter"
* Fix exit code propagation to the main process
* runtime_environment var should be dict in parameter
* Release of version 0.6.1
* :pushpin: Automatic update of dependency hypothesis from 4.43.4 to 4.43.5
* :pushpin: Automatic update of dependency hypothesis from 4.43.3 to 4.43.4
* :pushpin: Automatic update of dependency hypothesis from 4.43.2 to 4.43.3
* Cache queries for retrieving enabled indexes
* :pushpin: Automatic update of dependency hypothesis from 4.43.1 to 4.43.2
* Use slots on pipeline unit instances
* Fix resolving direct dependencies when pagination is used
* :pushpin: Automatic update of dependency thoth-storages from 0.19.14 to 0.19.15
* :pushpin: Automatic update of dependency hypothesis from 4.43.0 to 4.43.1
* :pushpin: Automatic update of dependency hypothesis from 4.42.10 to 4.43.0
* :pushpin: Automatic update of dependency pytest-mypy from 0.4.1 to 0.4.2
* :pushpin: Automatic update of dependency hypothesis from 4.42.9 to 4.42.10
* :pushpin: Automatic update of dependency hypothesis from 4.42.8 to 4.42.9
* :pushpin: Automatic update of dependency hypothesis from 4.42.7 to 4.42.8
* :pushpin: Automatic update of dependency hypothesis from 4.42.6 to 4.42.7
* :pushpin: Automatic update of dependency hypothesis from 4.42.5 to 4.42.6
* :pushpin: Automatic update of dependency hypothesis from 4.42.4 to 4.42.5
* Release of version 0.6.0
* :pushpin: Automatic update of dependency hypothesis from 4.42.0 to 4.42.4
* Start using adaptive simulated annealing
* Release of version 0.6.0
* Use THOTH_ADVISE variable for consistency
* updated templates with annotations and param thoth-advise-value
* :pushpin: Automatic update of dependency methodtools from 0.1.1 to 0.1.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.11 to 0.19.12
* Do not use cached adviser
* :pushpin: Automatic update of dependency thoth-storages from 0.19.10 to 0.19.11
* :pushpin: Automatic update of dependency pytest from 5.2.1 to 5.2.2
* :pushpin: Automatic update of dependency methodtools from 0.1.0 to 0.1.1
* Pin thoth libraries which will have incompatible release
* :pushpin: Automatic update of dependency thoth-python from 0.6.4 to 0.6.5
* :pushpin: Automatic update of dependency pylint from 2.4.2 to 2.4.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.9 to 0.19.10
* :pushpin: Automatic update of dependency thoth-python from 0.6.3 to 0.6.4
* Add spaces to fix toml issues
* :pushpin: Automatic update of dependency thoth-common from 0.9.12 to 0.9.14
* :pushpin: Automatic update of dependency thoth-common from 0.9.11 to 0.9.12
* :pushpin: Automatic update of dependency pytest from 5.2.0 to 5.2.1
* :pushpin: Automatic update of dependency pytest-cov from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency pytest-cov from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency thoth-common from 0.9.10 to 0.9.11
* :pushpin: Automatic update of dependency pylint from 2.4.1 to 2.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.19.8 to 0.19.9
* :pushpin: Automatic update of dependency pytest from 5.1.3 to 5.2.0
* Fix duration
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.3 to 0.1.4
* :pushpin: Automatic update of dependency thoth-storages from 0.19.7 to 0.19.8
* Fix duration calculation
* Add duration to Adviser
* Re-anable operating system sieve
* Check we do not raise exception if os sieve wants to filter out all packages
* Introduce sieve for limiting number of latest versions in direct dependencies
* Add a new sieve for limiting pre-releases in direct dependencies
* Introduce semver sorting on direct dependnecies - sieve
* Just a minor change to make code great again
* :pushpin: Automatic update of dependency pylint from 2.4.0 to 2.4.1
* Introduce a stable sorting of packages in sieve context
* :pushpin: Automatic update of dependency thoth-storages from 0.19.6 to 0.19.7
* :pushpin: Automatic update of dependency pylint from 2.3.1 to 2.4.0
* use postgresql hostname from thoth configmap
* Add check for upstream tensorflow parsing
* :pushpin: Automatic update of dependency thoth-python from 0.6.2 to 0.6.3
* Adjust os sieve testsuite to reflect changes
* Introduce tests for checking correct parsing of AICoE releases
* :pushpin: Automatic update of dependency thoth-storages from 0.19.5 to 0.19.6
* :pushpin: Automatic update of dependency pytest from 5.1.2 to 5.1.3
* :pushpin: Automatic update of dependency thoth-analyzer from 0.1.2 to 0.1.3
* Add seldon and seldon-core to cached packages
* Create a check and test case to handle errors when trying to resolve unsolved packages
* :pushpin: Automatic update of dependency thoth-common from 0.9.9 to 0.9.10
* :pushpin: Automatic update of dependency thoth-storages from 0.19.4 to 0.19.5
* :pushpin: Automatic update of dependency thoth-common from 0.9.8 to 0.9.9
* Corrected typos
* :pushpin: Automatic update of dependency thoth-storages from 0.19.3 to 0.19.4
* Add Sentry DSN to build of adviser-cached
* :pushpin: Automatic update of dependency thoth-storages from 0.19.2 to 0.19.3
* :pushpin: Automatic update of dependency thoth-storages from 0.19.1 to 0.19.2
* Propagate deployment name to have reports when cache is built
* Propagate deployment name for sentry environment
* :pushpin: Automatic update of dependency thoth-storages from 0.19.0 to 0.19.1
* Fix testsuite
* Make coala happy
* Fix indentation issues
* Relock requirements
* Fix exception message
* Print out packages before each pipeline unit
* Implement solved sieve
* Changes needed for PostgreSQL migration
* Add a pipeline step which removes unsolved packages
* Do not use -e flag
* Store and restore cache on builds
* Add more packages to cache config file
* Adjust cache not to cache graph database adapter
* Create adviser cache during container build
* :pushpin: Automatic update of dependency thoth-python from 0.6.1 to 0.6.2
* :pushpin: Automatic update of dependency thoth-storages from 0.18.6 to 0.19.0
* Propagate runtime environment explicitly
* Use more generic env var names
* Remove performance related tests
* Drop generic performance querying
* Start using PostgreSQL in deployment
* :pushpin: Automatic update of dependency semantic-version from 2.8.1 to 2.8.2
* :pushpin: Automatic update of dependency pytest from 5.1.1 to 5.1.2
* :pushpin: Automatic update of dependency semantic-version from 2.8.0 to 2.8.1
* :pushpin: Automatic update of dependency semantic-version from 2.7.1 to 2.8.0
* :pushpin: Automatic update of dependency semantic-version from 2.7.0 to 2.7.1
* :pushpin: Automatic update of dependency semantic-version from 2.6.0 to 2.7.0
* Turn error into warning
* :pushpin: Automatic update of dependency pytest from 5.1.0 to 5.1.1
* Improve error message reported if no releases were found
* State how to integrate with Thoth in docs
* Do not use setuptools.find_namespace_packages() for now
* Start using Thoth's s2i base image
* Fix missing packages in adviser's package
* :pushpin: Automatic update of dependency pytest from 5.0.1 to 5.1.0
* :pushpin: Automatic update of dependency pydocstyle from 4.0.0 to 4.0.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.5 to 0.18.6
* :pushpin: Automatic update of dependency thoth-common from 0.9.7 to 0.9.8
* :pushpin: Automatic update of dependency thoth-common from 0.9.6 to 0.9.7
* Document how to make changes in the dependency graph while it changes
* A package can be removed in the previous sub-graphs removals
* :pushpin: Automatic update of dependency voluptuous from 0.11.5 to 0.11.7
* :pushpin: Automatic update of dependency thoth-python from 0.6.0 to 0.6.1
* :pushpin: Automatic update of dependency thoth-storages from 0.18.4 to 0.18.5
* Change name of Thoth template to make Coala happy
* Start using Thoth in OpenShift's s2i
* Adjust testsuite to use only_solved flag
* Ask graph database only for packages which were already solved
* Do not remove package tuples which are direct dependencies
* Do not treat builds as pre-releases
* Fix reference to variable - do not pass class
* Fix resolving direct dependencies based on the score
* add metadata
* :pushpin: Automatic update of dependency thoth-storages from 0.18.3 to 0.18.4
* Introduce sieves
* :pushpin: Automatic update of dependency thoth-common from 0.9.5 to 0.9.6
* Update docs with sieves
* Add docs for performance indicators
* :pushpin: Automatic update of dependency thoth-storages from 0.18.1 to 0.18.3
* :pushpin: Automatic update of dependency thoth-storages from 0.18.0 to 0.18.1
* :pushpin: Automatic update of dependency thoth-storages from 0.17.0 to 0.18.0
* Release of version 0.5.0
* :pushpin: Automatic update of dependency thoth-storages from 0.16.0 to 0.17.0
* Deinstantiate solver once it is no longer needed
* Fix instantiation of edges
* Adjust testsuite so that it works with new implementation
* :pushpin: Automatic update of dependency thoth-storages from 0.15.2 to 0.16.0
* Fix handling of additional pytest arguments in setup.py test
* Fix handling of additional pytest arguments in setup.py test
* Move logic of stack candidates preparation to finalization part
* :pushpin: Automatic dependency re-locking
* Remove unused import
* Improve some logger messages
* Rewrite core adviser logic for dependency graph manipulation
* Optimize retrieval of transitive dependencies to avoid list copies
* Optimize instantiation of objects when resolved from graph database
* :pushpin: Automatic update of dependency thoth-storages from 0.15.1 to 0.15.2
* :pushpin: Automatic update of dependency thoth-python from 0.5.0 to 0.6.0
* :pushpin: Automatic update of dependency thoth-solver from 1.2.1 to 1.2.2
* :pushpin: Automatic update of dependency thoth-storages from 0.15.0 to 0.15.1
* Inform user that the missing release will be analyzed later on
* Remove invalid configuration entry APP_FILE in build config
* :pushpin: Automatic update of dependency thoth-storages from 0.14.8 to 0.15.0
* Fix transitive query - correctly propagate runtime information
* Improve warning message
* :pushpin: Automatic update of dependency thoth-common from 0.9.3 to 0.9.4
* Adjust testing recommendation type for now
* Remove score based cut-off step, observation reduction takes its position
* Add tests for observation based reduction
* Introduce observation reduction step to reduce subgraphs with no observations
* Add error message if no stacks were produced
* Report error if no recommendation was produced
* Introduce routines for iterating over develop and non-develop deps
* :sparkles: added the standard github configuration and a CODEOWNERS file
* Update lockfile
* Report used pipeline configuration of adviser to user
* Additional fixes and additions
* Minor changes
* Use CXXABI_1.3.8
* Use black for formatting
* Rework optimizations
* Adjust testsuite for new implementation
* Implement structure for dependency graph adjustment
* Report packages forming a found stack inside to a log
* Print out estimated number of stacks in scientific form
* Use only packages with known index
* Increase default adviser's requests and limits
* :pushpin: Automatic update of dependency thoth-storages from 0.11.4 to 0.14.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.11 to 0.9.0
* Add build trigger using generic webhook
* :pushpin: Automatic update of dependency pytest from 4.6.2 to 4.6.3
* Updated Readme to Dgraph examples
* :pushpin: Automatic update of dependency thoth-common from 0.8.7 to 0.8.11
* :pushpin: Automatic update of dependency pytest from 4.5.0 to 4.6.2
* Optimize package removal by working on indexes instead of package tuples
* Keep stats for package removals per step run
* Update documentation to respect current state
* Use uint16_t for representing packages in libdependency graph
* Simplify module structure to libdependency_graph library
* :pushpin: Automatic update of dependency thoth-common from 0.8.5 to 0.8.7
* Give adviser more time to process rest of the stacks in queue
* Provide better report to user on why adviser has stopped prematurely
* Use defaults of -1 for "unlimited" numbers in the cluster
* Parse a special value of -1 in the cluster to workaround click's errors
* Be more user-friendly in cluster logs
* Place toolchain cut after semver sort
* :pushpin: Automatic update of dependency pytest from 4.4.2 to 4.5.0
* :pushpin: Automatic update of dependency thoth-storages from 0.11.3 to 0.11.4
* Re-introduce filedump for fixes on long-lasting queries
* Log number of packages considered during dependency graph traversals
* Fix testsuite
* Create pipeline builder abstraction
* :pushpin: Automatic update of dependency thoth-storages from 0.11.2 to 0.11.3
* Release of version 0.4.0
* Fix coala issues
* :pushpin: Automatic update of dependency pytest from 4.4.1 to 4.4.2
* :pushpin: Automatic update of dependency thoth-storages from 0.11.1 to 0.11.2
* Use new method to obtain even large stacks from graph database
* :pushpin: Automatic update of dependency mock from 3.0.4 to 3.0.5
* :pushpin: Automatic update of dependency mock from 3.0.3 to 3.0.4
* Add information about library usage to pipeline and OpenShift job
* Build-time error filtering should be a very first step
* Propagate information about project runtime when checking buildtime error
* Fix issue happening in semver sort after a package is removed
* Remove toolchain to always use latest toolchain release
* Fix empty paths if there is raised an exception about invalid pkg removal
* :pushpin: Automatic update of dependency thoth-storages from 0.11.0 to 0.11.1
* Log message was missleading if package_tuple gets overwritten
* Provide fast-path when checking for already removed packages
* :pushpin: Automatic update of dependency pytest-cov from 2.6.1 to 2.7.1
* Implement build-time error filtering step
* :pushpin: Automatic update of dependency mock from 3.0.2 to 3.0.3
* :pushpin: Automatic update of dependency mock from 2.0.0 to 3.0.2
* :pushpin: Automatic update of dependency thoth-storages from 0.10.0 to 0.11.0
* Adjust provenance-checker template to use Dgraph
* Adjust Dependency Monkey to use Dgraph
* Adjust adviser template to use Dgraph
* Report overall score of a stack
* Remove is_solvable flag as done in Dgraph implementation
* Added the method to read version from project to conf.py
* Remove JanusGraph specific bits
* Do not depend on specific graph adapter from specific module
* Remove JanusGraph specific bits
* :pushpin: Automatic update of dependency thoth-storages from 0.9.7 to 0.10.0
* Trigger dependency monkey reports sync into graph database
* :pushpin: Automatic update of dependency pytest from 4.4.0 to 4.4.1
* :pushpin: Automatic update of dependency thoth-common from 0.8.4 to 0.8.5
* Automatic update of dependency thoth-common from 0.8.3 to 0.8.4
* Create a workaround for click argument parsing from env vars
* :sparkles: added the Registry to be used for image pulling to the templates
* Adviser implementation using stack generation pipeline
* Automatic update of dependency thoth-common from 0.8.2 to 0.8.3
* Make Isis a proper adapter
* Automatic update of dependency thoth-common from 0.8.1 to 0.8.2
* Automatic update of dependency pytest from 4.3.1 to 4.4.0
* :bug: put some sane default for IMAGE_STREAM_NAMESPACE into each template
* hot fixing the timeout
* :sparkles: ImageStream Tag and Namespace
* Automatic update of dependency flexmock from 0.10.3 to 0.10.4
* Report premature end of stack stream
* Improve handling of long-running advises
* Add timeout seconds for adviser to let it submit results
* Top score is now 100
* Automatic update of dependency thoth-storages from 0.9.6 to 0.9.7
* Automatic update of dependency thoth-python from 0.4.6 to 0.5.0
* Make reports more human readable
* Fix testsuite
* Add Thoth's configuration file
* Make Isis instance attribute
* Always kill stack producer if there is no consumer of stacks
* Fix Coala issues
* Do not score more than requested number of latest stacks
* Introduce stack producer timeout
* Use Sphinx for documentation
* Fix some test errors
* Minor improvements
* Introduce parameters for limiting number of versions
* Introduce limit parameter to limit number of packages of a same type
* Fix usage of package_t in libdependency_graph.so
* Use safe_load
* Fix coala complains
* Report any exception which occurred during dependency monkey run
* Introduce checks on configuration
* Make sure Isis is a singleton
* Minor fix in logged message
* Use Isis API from configmap
* Introduce performance based queries to Isis
* Make Coala happy again
* Use black for formatting
* Add missing file
* Make sure versions are sorted, add tests for adviser
* Use black for formatting tests
* Fix tests
* Log runtime environment when computing advises
* Address coala issues
* Add an optional graph database adapter to reduce number of connections
* Take into account packages that are not installable into the given env
* Update README, state local run in a container
* Report CVE count only if there were some found
* Remove unused env variables
* Provide Sentry and Prometheus configuration
* Add metadata information shown in result reports
* Update Pipfile.lock
* Register provenance-checker to graph-sync-scheduler
* Use runtime information during runtime-specific resolution
* Use runtime environment as provided by user
* Use click echo instead of raw print
* Fix wrong order of tuples
* Provide generic stack information
* Score and report CVEs in the application stack to the user
* Report version on each run
* Do not be too verbose
* Open source documentation for dependency graph
* Document dependency graph build
* Report number of stacks scored
* Raise an exception on premature stream end
* Minor changes in comment and logging message
* Fix coala complains
* Wait for parent to score stacks in stack producer
* Add shared library for CentOS:7
* Provide Dockerfile for container-build
* Add linked library
* Initial dependency graph implementation in C++
* Correctly handle end of pipe
* Adjust .gitignore
* Run dependency graph as a standalone process, produce stacks into pipe
* It's already 2019
* Use proper loglevel for debug message
* Restrict indexes in dependency monkey runs
* Schedule graph syncs for adviser runs by graph-sync-operator
* Fix hashes collision in generated Pipfile.locks
* Implement dependency graph in C++
* Reuse connected graph adapter do reduce number of connections
* Amun API URL is used by Dependency Monkey
* Argument has to be named otherwise cannot be used as kwargs
* Increase run time for dependency monkey
* Propagate whitelisted sources to provenance checks
* Increase dependency monkey requests
* Correctly propagate job ids from workload operator
* Fix CI by updating thoth-python package
* Remove duplicit parameter from template
* Increase adviser job run limit
* Provide limit and count defaults in template
* Add coverage file to .gitignore
* Fix linter issues
* Fix wrong variable usage
* Report limit if limit was reached
* Remove unused imports
* Minor docs fixes
* Link to Dependency Monkey design document
* Add dependency monkey design document into docs
* Cut off and minor adjustmets
* Refactor test suite
* Use black for formatting
* Minor code refactoring, update requirements
* Use to_tuple_locked method as we have locked packages
* Fix missing import
* Construct Pipfile from resolved dependencies
* Print estimated number of software stacks
* Remove unused if statement
* Adjust dependency graph to use ids
* The decision function is now not optional
* Performance based scoring on exact stack match
* Do not pass None values in runtime environment to_dict
* Simplify work with dependency graph
* Fix handling of runtime environment, remove unused bits
* Avoid possibly inserting same package versions multiple times
* Utilize iter_dependencies locked method
* Use Python 3.6 by default
* Discard original sources when creating a new project
* Fix transitive dependencies retrieval
* Don't be too verbose in logs
* Mark jobs for cleanup
* Fetch digests from graph database in provenance checks
* Remove unused perf type
* Prepare dependency graph for graph slicing
* Minor fixes in decision functions
* Restructure scoring and decision functions
* Capture all the layers of dependencies
* Minor code refactoring
* Do not print reasoning into logs
* Fix injecting digests into generated stacks
* Minor fixes in dependency monkey
* Do not forget to package requirements.txt
* Minor fixes
* Raise an exception if no matching versions were found
* Consider also version when creating dependency graph
* Move relevant test files to thoth-python package
* Correctly fill stacks with package digests
* Remove files that were moved to thoth-python
* Include index when retrieving packages from the graph database
* Fill package hashes from the graph database
* Fix import errors
* Structure error reports correctly respecting schema
* Use thoth-python package
* CI fixes
* Fix janusgraph port
* Fix Coala complains
* Fixes and improvements
* Adjust temporary filling package hashes
* Fix missing import
* Pass index to be none always
* Fill package digets in advises
* Be consistent with subcommand naming
* Minor fix in docstring
* Introduce limit in dependency monkey template
* Introduce limit and count in adviser template
* First implementation of the Adviser class
* Default to stdout in dependency monkey
* Refactor dependency monkey so that it can be used in notebooks
* Perform deepcopy to report the correct input
* Fix filling hashes multiple times
* Seed and count can be empty string
* Convert required parameters to ints
* Fix environment variable name
* Place all decision functions at one place
* Improve logging
* Fix missing import
* Make sure queries respect python package names according to PEP
* Improve logging to make sure its visible what's going on
* Fix syntax error
* Fix import error
* Add missing import
* Add ability to submit a testing stack
* Issue warning when submitting to Amun API
* Remove duplicit code for loading Amun context
* Handle exceptions happening when submitting to Amun API
* CI fixes
* Add exception if constraints cannot be met
* Temporary fill package digests by querying PyPI index
* Always check which source in a warehouse
* Adjust output methods
* Adjust dependency monkey job template
* Minor improvements in implementation
* Aaa
* Fixes in the dependency graph implementation
* A package version is distinguished by name, version and index
* Add missing imports
* Check first layer of dependencies for validity
* Sanity check for adding non-locked version to lock
* Add testsuite for graph solver, dependency graph implementation
* Introduce graph Python solver
* Add testsuite for graph solver
* Introduce dependency graph
* Introduce graph Python solver
* reading README from file, its the long_description...
* Check for latest packages present on indexes
* Release of version 0.3.0
* fixing coala
* typo :/
* using thoth zuul jobs now
* Adjust setup.py to run testsuite correctly
* Run testsuite using setup.py
* Output to JSON in adviser
* Link PackageVersion to Source index used
* Report dict reporesentation of input instead of raw strings
* Add missing parameters to template
* Fix labels section in template
* Dependency monkey is a template
* Move dependency monkey to a job template
* Rename adviser template to be more clear
* Move from Pods to Jobs
* Directly pass adviser subcommand that should be run
* Introduce Dependency Monkey template
* Update README file
* Fix link to Thamos
* Introduce method for converting model to object
* Possible different source is info
* Add Codacy badge
* Fix testsuite respecting last changes
* Link to Pipenv docs for specifying package indexes
* Fix console figure
* State configured index in the report message
* Adjust reported issue id for possible different source
* Add installation section and adjust based on review comments
* Document provenance checks
* Quote relevant parts of string
* Add the current PyPI index to default warehouses
* Make artifact names lowercase by deafult
* Finish provenance reports
* Report directly findings in the provenance check report
* Adviser report should be always an array
* Report back error if we cannot conclude on application stack
* Ignore s2i's virtualenv in which adviser is run
* Increase memory for adviser due to OOMs
* Release of version 0.2.0
* Introduce add_source and add_package methods
* Do not use command in openshift template
* Release of version 0.1.1
* Setuptools find_packages does not respect namespaces
* Release of version 0.1.0
* Initial dependency lock
* Add forgotten lxml library for bs4 parsing
* Provide JanusGraph configuration in provenance-checker template
* Provide JanusGraph configuration in adviser template
* Pass full path to Python3 in s2i
* Make CLI executable
* Install forgotten packages
* Add execute bit to app.sh
* State we want to run provenance rather than adviser in template
* Revert "Provide entrypoint for OpenShift s2i"
* Provide a script to run desired subcommand
* Provide entrypoint for OpenShift s2i
* Remove unused script as adviser is s2i now
* Remove Dockerfile as adviser is s2i now
* Let's reuse parameter names from adviser
* Use local tensorflow index page for gathering versions
* Fix warehouse test
* Some CI fixes
* Initial dependency lock
* Let Kebechet pin down deps
* Remove old TODO
* Implement sorting based on semver
* Create abstraction classes
* Initial python recommendation implementation
* Automatic update of dependency thoth-common from 0.2.6 to 0.2.7
* Automatic update of dependency thoth-common from 0.2.5 to 0.2.6
* Introduce provenance checker template
* Automatic update of dependency thoth-storages from 0.5.1 to 0.5.2
* Automatic update of dependency thoth-common from 0.2.4 to 0.2.5
* Automatic update of dependency thoth-common from 0.2.3 to 0.2.4
* change the queue
* Automatic update of dependency thoth-common from 0.2.2 to 0.2.3
* Automatic update of dependency thoth-storages from 0.5.0 to 0.5.1
* Automatic update of dependency thoth-storages from 0.4.0 to 0.5.0
* Automatic update of dependency thoth-storages from 0.3.0 to 0.4.0
* Automatic update of dependency thoth-storages from 0.2.0 to 0.3.0
* Automatic update of dependency thoth-storages from 0.1.1 to 0.2.0
* State all template parameters
* Be consistent with label naming
* Update requirements.txt respecting requirements in Pipfile
* Automatic update of dependency thoth-common from 0.2.1 to 0.2.2
* Automatic update of dependency thoth-storages from 0.1.0 to 0.1.1
* Add app=thoth label to pod template
* Adjust template labels
* Fix image stream kind in template
* Fix coala naming convention configuration
* Add OpenShift templates for deployment
* Automatic update of dependency thoth-storages from 0.0.33 to 0.1.0
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Automatic update of dependency thoth-common from 0.2.0 to 0.2.1
* Initial dependency lock
* Delete Pipfile.lock for relocking dependencies
* relocked, travis removed, zuul added
* Automatic update of dependency thoth-common from 0.0.9 to 0.1.0
* Automatic update of dependency thoth-analyzer from 0.0.6 to 0.0.7
* Automatic update of dependency thoth-analyzer from 0.0.5 to 0.0.6
* Automatic update of dependency thoth-storages from 0.0.32 to 0.0.33
* Automatic update of dependency thoth-storages from 0.0.29 to 0.0.32
* Automatic update of dependency thoth-common from 0.0.6 to 0.0.9
* Update thoth packageswq
* Automatic update of dependency thoth-storages from 0.0.25 to 0.0.28
* Do not restrict Thoth packages
* Another CI fix
* Another CI fix
* Run coala in non-interactive mode
* CI fix
* Run coala in CI
* Create OWNERS
* Remove dependencies.yml
* Use coala for code checks
* Fix package name in license header
* Add LICENSE and license headers
* Use thoth's common logging
* Add README file
* Version 0.0.2
* State only direct dependencies in requirements.txt
* Version 0.0.1
* Update dependencies
* Update thoth-storages from 0.0.3 to 0.0.4
* Rename environment variables to respect user-api arguments passing
* Create initial dependencies.yml config
* Change envvar for --requirements option
* Expose advise_pypi function
* Version 0.0.0
* Build adviser image in CI
* Fix naming typo
* Initial template for implementation
* Initial project import

## Release 0.14.0 (2020-08-17T10:32:30)
* :pushpin: Automatic update of dependency matplotlib from 3.3.0 to 3.3.1 (#1114)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.0 to 0.25.1 (#1113)
* :pushpin: Automatic update of dependency thoth-python from 0.10.0 to 0.10.1 (#1110)
* Adjust message when resolver does not find any stack (#1109)
* :pushpin: Automatic update of dependency hypothesis from 5.23.11 to 5.24.0 (#1107)
* Add docs for RL based predictors (#1105)
* :pushpin: Automatic update of dependency hypothesis from 5.23.9 to 5.23.11 (#1104)
* updated document with ceph deployment name specification (#1103)
* :pushpin: Automatic update of dependency hypothesis from 5.23.8 to 5.23.9 (#1102)
* Add a pipeline unit for suggesting Intel TensorFlow builds (#1093)

## Release 0.14.1 (2020-08-24T13:11:06)
* Fix detection of OOM when os.waitpid is used (#1138)
* Fix handling of return code when using os.waitpid (#1136)
* :pushpin: Automatic update of dependency hypothesis from 5.28.0 to 5.29.0 (#1137)
* :pushpin: Automatic update of dependency pytest-mypy from 0.6.2 to 0.7.0 (#1135)
* :pushpin: Automatic update of dependency hypothesis from 5.27.0 to 5.28.0 (#1133)
* :pushpin: Automatic update of dependency pytest-mypy from 0.6.2 to 0.7.0 (#1132)
* :pushpin: Automatic update of dependency hypothesis from 5.27.0 to 5.28.0 (#1131)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.2 to 0.25.5 (#1130)
* :pushpin: Automatic update of dependency attrs from 19.3.0 to 20.1.0 (#1129)
* :pushpin: Automatic update of dependency hypothesis from 5.26.0 to 5.27.0 (#1125)
* :pushpin: Automatic update of dependency hypothesis from 5.26.0 to 5.27.0 (#1124)
* :pushpin: Automatic update of dependency hypothesis from 5.26.0 to 5.27.0 (#1123)
* Fix f-string expansion in exception (#1120)
* :pushpin: Automatic update of dependency pytest-cov from 2.10.0 to 2.10.1 (#1122)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.1 to 0.25.2 (#1121)
* Introduce a stride for discarding non-unique stacks (#1119)
* :pushpin: Automatic update of dependency hypothesis from 5.24.0 to 5.26.0 (#1117)

## Release 0.15.0 (2020-08-26T12:09:41)
* Fix recommendation name - use security
* Fix performance recommendation name
* fix test and upgrade to warning
* clean-up tests
* give user more information
* add tests for si adviser step
* use self.configuration for weights
* include for stable recommendation and parameterize weights
* add security indicator step

## Release 0.15.1 (2020-08-27T20:40:51)
### Features
* Fix SI step inclusion (#1146)

## Release 0.16.0 (2020-09-07T18:41:30)
### Features
* Unresolved dependencies have to be set due to intersected deps
* Implement a predictor that generates package combinations
* Implement a predictor that generates package combinations
* Document raising EagerStopPipeline in predictor
* Fix issue caused when last unresolved dependency is removed
* Update unresolved dependencies during the resolution process
* Introduce prioritized packages to predictors (#1160)
* Introduce a way to parametrize predictor (#1159)
* Log warning about no SI just once per pipeline run (#1154)
* Apply limit of stacks only for the accepted stacks (#1155)
### Bug Fixes
* Adjust testsuite to the unresolved optimization fix
### Improvements
* Fix warnings produced during executing the test suite (#1162)
### Automatic Updates
* :pushpin: Automatic update of dependency hypothesis from 5.29.4 to 5.30.0 (#1153)
* :pushpin: Automatic update of dependency hypothesis from 5.29.3 to 5.29.4 (#1152)

## Release 0.17.0 (2020-09-17T06:28:26)
### Features
* Fix version checks - be accurate about TensorFlow versions (#1224)
* Fix the testsuite issue
* Make black happy
* Implement automatic schema checks in the testsuite (#1217)
* Be more specific about justification types provided
* Provide mechanism to verify justification schema
* Use cached Python version tuples
* Exclude test files from the package
* Additional changes to the implementation
* State unit implementation placemenet in docs
* Fix typing of advised manifest changes
* Fix rebase issue
* Make pre-commit happy
* Advise to add OMP_NUM_THREADS environment variable when MKL is used
* State advised manifest changes in the final product report
* Use kw_only parameters in product
* State manifest changes in the pipeline product
* include whiskey_lake microarch to list of avx2 containing archs
* Make pre-commit happy
* Restrict resolutions of tensorflow==2.2 with tensorflow-probability (#1202)
* Link to justification document when unresolved dependencies
* Perform copy of the manifest changes for each state clone
* Perform copy of the advised manifest changes on state clone
* Correct messages printed to users
* Fix message formatting
* Adjust testsuite to check for justification link
* Add an ability to specify manifest changes
* Provide a link to justification to pipeline units
* Revert "Provide a link to justification to each pipeline unit"
* Provide a link to justification to pipeline units
* Introduce a step prevents from resolving some combinations of urllib3 with TensorFlow=2.1
### Bug Fixes
* Do not accept stacks with TF 2.1 and urllib3 that cause issues
* Extend the tf-probability import error to all tensorflow-packages
* Add a wrap that notifies about a bug in the summary output
* Notify users about accuracy bug when TensorFlow 2.3 is used (#1200)
### Improvements
* Rephrase code to make pydocstyle and black happy at the same time
* Restructure how unit modules are shipped within the package
### Non-functional
* State is no longer using OrderedDict to gain performance
### Automatic Updates
* :pushpin: Automatic update of dependency thoth-storages from 0.25.9 to 0.25.10 (#1223)
* :pushpin: Automatic update of dependency hypothesis from 5.35.2 to 5.35.3
* :pushpin: Automatic update of dependency thoth-storages from 0.25.8 to 0.25.9 (#1209)
* :pushpin: Automatic update of dependency hypothesis from 5.35.0 to 5.35.2 (#1203)
* :pushpin: Automatic update of dependency matplotlib from 3.3.1 to 3.3.2 (#1201)
* :pushpin: Automatic update of dependency pytest from 6.0.1 to 6.0.2 (#1193)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.7 to 0.25.8 (#1192)
* :pushpin: Automatic update of dependency hypothesis from 5.34.1 to 5.35.0 (#1187)
* :pushpin: Automatic update of dependency hypothesis from 5.33.2 to 5.34.1
* :pushpin: Automatic update of dependency thoth-storages from 0.25.6 to 0.25.7 (#1185)
* :pushpin: Automatic update of dependency hypothesis from 5.33.1 to 5.33.2 (#1181)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.5 to 0.25.6 (#1180)
* :pushpin: Automatic update of dependency attrs from 20.1.0 to 20.2.0 (#1179)
* :pushpin: Automatic update of dependency attrs from 20.1.0 to 20.2.0 (#1175)
* :pushpin: Automatic update of dependency hypothesis from 5.30.0 to 5.33.1 (#1170)

## Release 0.18.0 (2020-09-24T19:44:26)
### Features
* Fix black complains (#1291)
* Fix master branch
* Rename sieve to conform naming convention
* Provide stack info in step pipeline units
* Provide stack info in pipeline sieves
* Add stack information in boots
* Fix complains of pre-commit (#1280)
* Introduce a step for removing scipy for TF>=2.1<2.3 releases (#1249)
* Add a link to Python version justification (#1273)
* Add a mechanism to skip packages from a stack based on pipeline steps
* Do not recommend using TensorFlow<2.3>=2.0 with NumPy>=1.19.0 (#1262)
* Prevent resolving TF<=1.14 with gast>0.2.2
* Implement a sieve that drops Pandas>=1.2 on Python 3.6 (#1264)
* Fix pre-commit issues reported (#1254)
* Fix formatting in backports
* Fix message printed
* Fix providing justification to CVE step
* Add justification links related to user stack scoring
* Add a step to make sure the correct version of NumPy is used for TF==1.13.1 (#1236)
* Link justification documents related to resolver messages (#1232)
* Fix wrong import
* Provide justification links to various parts of the resolution process
* Link justification for the approximating latest predictor
* Recommend TensorFlow release based on CUDA present in environment (#1225)
* Notify about proper usage of Intel's MKL
### Bug Fixes
* Do not accept CVEs when recommendation type is set to security
### Improvements
* Include pre-releases pipeline unit only if pre-releases are disabled (#1284)
* Turn warnings into errors reported when AICoE index cannot be parsed
* Add test for intel TensorFlow (#1231)
### Automatic Updates
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1299)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1297)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1296)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1295)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1294)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1289)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1278)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1277)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1276)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1274)
* :pushpin: Automatic update of dependency thoth-python from 0.10.1 to 0.10.2 (#1272)
* :pushpin: Automatic update of dependency hypothesis from 5.35.4 to 5.36.0 (#1271)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1270)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1269)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1267)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1265)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1259)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1258)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1257)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1256)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1255)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1251)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.10 to 0.25.11 (#1250)
* :pushpin: Automatic update of dependency hypothesis from 5.35.3 to 5.35.4
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0

## Release 0.19.0 (2020-10-26T23:56:28)
### Features
* Added documentation to integrate kebechet
* Reflect MULTI_PACKAGE_RESOLUTIONS change in docs
* Adjust testsuite so that it respects optimized wraps call
* Make pre-commit happy
* Add a note to wraps docs about wrap call optimization
* Adjust testsuite accordingly
* Call wraps only if products are in the final resolver result
* Fix testsuite
* Remove version clash boot
* Fix pre-commit complains
* Add imports to docs sample
* Fix manifest changes docs
* Add docs for advising manifest changes
* Fix pre-commit
* Fix docs formatting
* Fix indentation in docs
* Fix documentation for the package_name option in pseudonyms
* Point to the existing relevant justification document
* Provide stack info if direct dependencies were not resolved
* Improve message logged
* Make pre-commit happy
* Fix return type
* Add stack info when no stack is produced
* Fix history kept in TD-learning
* Temperature computation and probability does not need to be done for t=0
* Do not keep history by default
* Document latest predictor
* Remove unused import
* Mention the lib in docs
* Use C extension for computing termial random
* Do one step TD-learning and turn off trace
* Get random dependency for expansion
* Fix links to images
* Fix links to images
* Add docs for TD-learning
* Introduce trace parameter to TD learning
* Add MCTS demonstration
* Fix MCTS history keeping
* Docs update
* Minor adjustment to annealing docs
* Remove hill climbing copy-pasta leftover
* Add an image for random walk
* Fix path to images
* Adjust plot labels
* Fix index and add template files for predictors
* Switch to TD-learning with step==2 instead of Monte Carlo learning
* Fix log printed
* Fix formatting
* Add more weak condition when logging progress
* Log based on iteration not based on final states produced
* Enable probability assigning score when generating scores
* Fix assigning score based on probability
* Log the highest rated software stack found so far
* Implement a unit for deterministic score assignment
* Fix n-step TD-learning
* Fix message logged
* Be more accurate with plot label
* Allow assigning score when package version or index url is not set
* Set score can now generate random score if not explicitly provided
* Plot resolver history
* Register debug units so they can be easily run using supplied conf
* Clear beam history
* Implement n-step TD learning
* Units do not need to be stated in the configuration
* Provide probability configuration for assigning a score
* Adjust for pre-commit
* Remove tests related to policy shrink
* No need to shrink in TD learning
* No need to shrink learnt policy
* Allow null values in pipeline units listing (#1441)
* Add a note to README
* Remove unused exception
* Simplify units implementation based on calling contract (#1431)
* Test default configuration schema in units (#1433)
* Provide schema for security indicators step so that it is registered (#1432)
* Introduce capability for obtaining units inside a builder context (#1430)
* Implement package version in configuration for boots, strides and wraps
* Fix trailing white space (#1429)
* Link to justification document in each pipeline unit docs
* exclude hc hs if type is secure (#1416)
* Extend justifications section
* Add justifications section to the docs
* Add a link to RL resolution video
* Adjust sentence
* Turn html into an image so it's properly rendered by GitHub
* Add a link to RL video
* Fix links to YT video
* Adjust docs for Dependency Monkey
* Link to docs from README
* Adjust docs for steps
* Adjust docs for pseudonym pipeline units
* Adjust docs for sieve pipeline units
* Some units are specific to package, not to package version
* Adjust predictor documentation
* Adjust resolver section of docs
* Some modifications to the pipeline section in docs
* Mention pseudonyms in the pipeline unit docs
* Add a link to shared deps note
* Minor tweaks in the deployment section
* Fix formatting
* Adjust link to Python docs
* Note to buildconfiguration
* Fix formatting
* Fix environment variable name
* Link to beam
* limit_latest_versions is no longer supported
* Fix URL
* Fix urls in the integration section
* Adjust compatibility section in docs
* State MDP in the README file
* Fix docstring (#1418)
* Remove voluptuous from dev-packages it is already in packages
* Fix heading
* Adjust README file
* Use find_namespace_packages to discover all thoth-adviser modules (#1412)
* Add missing schema
* Optimize sieve and steps calls that are specific for a package (#1404)
* Pass package_name from unit configuration (#1400)
* Remove unused import
* Remove unused import
* Return pytest.skip if the pipeline unit cannot be verified
* Add testsuite related to pseudonym runs
### Bug Fixes
* Provide stack info if resolver failed to resolve direct dependencies
* Minor fixes in docs
* Minor fixes in the README file
### Improvements
* Minor refactoring and a note addition
* Add docs for package combinations predictor
* Make multi_package_resolution part of the step unit configuration
* Add tests for product addition to report
* Add documentation for predictor that uses a gradient based method
* Print found stack score to logs
* Add documentation for adaptive simulated annealing predictor
* Document sampling, random walk and hill climbing predictors
* Remove unused parts
* Keep resolver history only if needed
* Turn off multi package resolution for debug units
* Remove unused imports
* Rework generate score unit not to use random module
* Make temperature coefficient parametrize and increase it
* Deinstantiate solver and let gc do its job
* Update docs to reflect package_name in boots, strides and wraps
* Fix typo
* Adjust the unit section of documentation
* Add images for pipeline and pipeline builder
* Add tests for skipping a package from steps (#1411)
* Add tests related to unit_run flag
* Introduce Pseudonym pipeline unit type (#1313)
* Introduce a base class for implementing pipeline unit tests (#1314)
### Other
* Adjust types in history kept in annealing
### Automatic Updates
* :pushpin: Automatic update of dependency hypothesis from 5.37.3 to 5.38.1 (#1499)
* :pushpin: Automatic update of dependency hypothesis from 5.37.0 to 5.37.1 (#1440)
* :pushpin: Automatic update of dependency pytest from 6.1.0 to 6.1.1 (#1425)
* :pushpin: Automatic update of dependency hypothesis from 5.36.1 to 5.37.0 (#1424)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.14 to 0.25.15 (#1423)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.13 to 0.25.14 (#1413)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.12 to 0.25.13 (#1402)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1398)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.11 to 0.25.12 (#1401)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1397)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1396)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1395)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1394)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1393)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1392)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1391)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1390)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1389)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1386)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1382)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1381)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1380)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1379)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1378)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1377)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1376)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1375)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1371)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1370)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1369)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1368)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1367)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1366)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1365)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1364)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1363)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1362)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1361)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1360)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1359)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1358)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1356)
* :pushpin: Automatic update of dependency pytest from 6.0.2 to 6.1.0 (#1357)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1355)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1354)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1353)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1352)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1351)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1350)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1349)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1348)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1347)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1346)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1345)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1344)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1343)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1342)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1341)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1340)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1339)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1338)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1337)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1336)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1335)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1334)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1333)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1332)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1331)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1330)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1329)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1328)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1327)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1326)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1325)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1324)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1323)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1322)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1320)
* :pushpin: Automatic update of dependency hypothesis from 5.36.0 to 5.36.1 (#1321)
* :pushpin: Automatic update of dependency hypothesis from 5.36.0 to 5.36.1 (#1319)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1318)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1316)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1315)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1311)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1310)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1309)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1308)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1307)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1306)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1305)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1304)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1303)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1302)
* :pushpin: Automatic update of dependency voluptuous from 0.11.7 to 0.12.0 (#1301)

## Release 0.19.1 (2020-10-29T15:22:35)
### Features
* Add a generic alias pseudonym unit
* Add a link to Jupyter Notebook demonstrating pipelines
* Minor formatting changes in Kebechet docs (#1507)
* Propagate statistics to the final report
* Log message only if relevant (#1506)
* Fix trailing whitespace in docs (#1505)
### Bug Fixes
* Handle cannot produce stack exception so results are not overwritten
### Improvements
* Link Jupyter notebook showing TD-learning and MCTS predictors

## Release 0.20.0 (2020-11-03T15:20:00)
### Features
* Handle SIGUSR1 handler to stop exploitation phase (#1527)
* Introduce a sieve for filtering out incompatible TensorFlow for Py3.9 (#1528)
### Improvements
* A pipeline unit that suggests not to use h5py>=3 with TF==2.1 (#1529)
* Add links to TDS and Jupyter Notebook
### Automatic Updates
* :pushpin: Automatic update of dependency hypothesis from 5.41.0 to 5.41.1 (#1530)
* :pushpin: Automatic update of dependency hypothesis from 5.39.0 to 5.41.0 (#1523)
* :pushpin: Automatic update of dependency toml from 0.10.1 to 0.10.2 (#1522)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.15 to 0.25.16 (#1521)
* :pushpin: Automatic update of dependency hypothesis from 5.38.1 to 5.39.0 (#1518)

## Release 0.20.1 (2020-11-05T21:30:58)
### Features
* Add a temporary workaround for #1541
* Provide stack info in security indicators
* Adjust message logged to reduce confusion
* Increase verbosity to see where inspections are triggered
* Adjust description in liveness.py
* Add links to termial random
### Bug Fixes
* Fix issue when signal is sent in one call in livenenss.py
### Improvements
* :sparkles: remove the Zuul config file, as we dont use Zuul anymore
* Adjust tests for stack_info provided by security indicators
### Automatic Updates
* :pushpin: Automatic update of dependency thoth-storages from 0.25.16 to 0.25.17 (#1540)

## Release 0.21.0 (2020-11-20T06:19:52)
### Features
* Implement a sieve that filters out TensorFlow releases based on API (#1560)
* Consider library usage for TF 42475 wrap (#1564)
* Add a pipeline unit wrap for slow keras embedding layer (#1558)
* Add missing link to user-stack scoring justification (#1556)
### Bug Fixes
* Improve message logged when reporting resolver's progress (#1569)
* Match score of the user's stack printed with the final score reported (#1570)
* Add a wrap that notifies about a bug when mutliple instances of TF are running (#1559)
* Handle exception raised when the given record was not found
### Improvements
* Implement a boot pipeline unit for checking Pipfile hash (#1571)
* Report warning if Python versions do not match (#1565)
* Adjust tests accordingly
### Automatic Updates
* :pushpin: Automatic update of dependency pytest-mypy from 0.7.0 to 0.8.0 (#1567)
* :pushpin: Automatic update of dependency matplotlib from 3.3.2 to 3.3.3 (#1563)
* :pushpin: Automatic update of dependency thoth-storages from 0.26.0 to 0.26.1 (#1562)
* :pushpin: Automatic update of dependency hypothesis from 5.41.1 to 5.41.2 (#1554)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.17 to 0.26.0 (#1552)
* :pushpin: Automatic update of dependency thoth-storages from 0.25.17 to 0.26.0 (#1547)
* :pushpin: Automatic update of dependency attrs from 20.2.0 to 20.3.0 (#1551)
* :pushpin: Automatic update of dependency attrs from 20.2.0 to 20.3.0 (#1544)

## Release 0.21.1 (2020-11-25T16:44:27)
### Features
* Include dependency if at least one lib always requires it (#1594)
* :arrow_up: Automatic update of dependencies by kebechet. (#1589)
* Fix pre-commit issues
* properly JSON formatted advised manifest changes (#1584)
* Add a warning to TF API (#1581)
* h5py==3 causes troubles also on TensorFlow 2.3.1 (#1576)
* Be open, always

## Release 0.22.0 (2021-01-19T17:37:39)
### Features
* State python_requires in the compatibility section of docs (#1619)
* Implement a sieve that filters out TensorFlow==2.4.0 on non-AVX2 CPU (#1617)
* :arrow_up: Automatic update of dependencies by kebechet. (#1612)
* Add justification to stack info if a package with CVE is avoided (#1611)
* Recommend TensorFlow 2.4 based on CUDA support (#1605)
* Relock so that typing extensions have the right environment marker (#1607)
* :arrow_up: Automatic update of dependencies by kebechet. (#1609)
* Fix testsuite for Python 3.8 (#1603)
* Updated marketplace app link
* Update .aicoe-ci.yaml
* Introduce THOTH_CONFIG_CHECK environment variable (#1592)
* Update TensorFlow symbols database (#1587)
* port to python 38
### Bug Fixes
* Improve error message reported to the user (#1588)
### Improvements
* removed bissenbay, thanks for your contributions!

## Release 0.23.0 (2021-02-01T22:07:33)
### Features
* Fix pre-commit issues
* :arrow_up: Automatic update of dependencies by kebechet.
* Add a wrap that adds information about Thoth s2i used
* Invert inclusion logic, include if Thoth s2i is not used
* Fix S2I multiple include pipeline unit
* Add a sieve to filter out packages based on ABI provided by s2i Thoth
* Reformat using black
* Add a pipeline unit recommending Thoth's s2i as a base
* :arrow_up: Automatic update of dependencies by kebechet.
* Implement a pipeline unit which checks GPU and CUDA supplied
* :arrow_up: Automatic update of dependencies by kebechet.
* docs: State build-watcher in the integration section (#1620)
### Improvements
* Fix tests related to Thoth's common config changes
* Add tests for Thoth's s2i wrap pipeline unit

## Release 0.24.0 (2021-02-09T09:06:23)
### Features
* Do not enable cut pre-releases step if selective pre-releases are allowed
* :arrow_up: Automatic update of dependencies by Kebechet
* Link Experimental features section from docs index (#1656)
* Document selective pre-releases (#1650)
* Implement a pipeline unit for selective pre-release filtering (#1648)
* Add standard Thoth templates
* :arrow_up: Automatic update of dependencies by Kebechet
* :arrow_up: Automatic update of dependencies by Kebechet (#1647)

## Release 0.24.1 (2021-02-09T10:13:09)
### Features
* Thoth's additional features can be None

## Release 0.24.2 (2021-02-16T08:47:12)
### Features
* Introduce a sieve to filter out legacy versions from the resolution (#1665)
* Parameterize preparing adviser inputs
* :arrow_up: Automatic update of dependencies by Kebechet (#1673)
* Prepare inputs for adviser container run
* Fix linkage in docs (#1663)

## Release 0.24.3 (2021-02-16T14:47:15)
### Features
* No need to sort JSON keys when preparing inputs (#1677)
* Provenance checker accepts only Pipfile/Pipfile.lock
* Assign library usage only once
* Show used library usage in the resulting JSON report
* Properly open files for writing in prepare script
* :arrow_up: Automatic update of dependencies by Kebechet (#1681)

## Release 0.25.0 (2021-02-17T13:10:51)
### Features
* Remove sleep part from the prepare script used for debugging (#1693)
* Add a sieve for filtering packages based on index configured (#1692)
* Introduce a sieve for filtering packages not coming from an index
* :arrow_up: Automatic update of dependencies by Kebechet
* Rewrite method logic to bypass black issues
* Yield configuration for each pipeline unit that should be instantiated
* Document strict index configuration feature

## Release 0.25.1 (2021-02-18T09:00:13)
### Features
* Increase timeout for a test case (#1701)
* Remove parts introduced by wrong rebase
* Remove invalid entry from sieves
### Bug Fixes
* Fix issues caused when Pipfile.lock is set to null by prepare.py

## Release 0.26.0 (2021-03-03T21:48:47)
### Features
* Provide justification when filtering based on selective pre-releases (#1718)
* Add justification for index configuration filter (#1719)
* Fix when package version is any version
* Add justification for filtering packages based on index configuration
* Fixes related to thoth-common adjustments (#1717)
* :arrow_up: Automatic update of dependencies by Kebechet
* Remove bits related to preparation (#1708)
* Propagate parsed Dependency Monkey inputs to the resulting JSON report
* :arrow_up: Automatic update of dependencies by Kebechet
### Bug Fixes
* Add space after error message
### Improvements
* :sparkles: :arrow_up: some standard updates

## Release 0.27.0 (2021-03-24T09:23:18)
### Features
* Keep optimization for prescription wraps with resolved dependencies (#1800)
* Fix handling optimized wrap call based on product score (#1798)
* Fix handling prescription unit names (#1797)
* Add "not" operator to the prescription declaration (#1795)
* Move MKL specific wrap to prescriptions
* Add ability to declare advised manifest changes in wrap prescriptions (#1794)
* Allow supplying expected library usage in prescriptions (#1793)
* Register core units first before any prescriptions (#1792)
* Fix step example in prescriptions
* Reformat using black
* Provide more information in justification
* Rewrite s2i wraps to boots to match semantics
* Be more positive with justification message reported
* Use package name from configuration to reduce some hashing
* Update prescription documentation so users can start using it
* Report stack info just once in prescription units (#1785)
* :arrow_up: Automatic update of dependencies by Kebechet (#1784)
* Add Thoth's landing page (#1626)
* Remove units rewritten to prescription YAML file
* Implement prescription validation with semantics (#1781)
* Remove wisdom from the prescription yaml (#1780)
* Introduce namespace for prescriptions
* Do not enforce operating system to be set for matching (#1777)
* Adjust pseudonym example with yield matched version (#1778)
* Add ability to yield matched package version in pseudonyms
* Relax strict match for prescription wrap pipeline units
* Add a pipeline unit that notifies about prescription release used
* :arrow_up: Automatic update of dependencies by Kebechet (#1759)
* Test loading prescriptions
* Fix checking justification link
* Allow multiple prescription files being supplied to the resolver
* Be more verbose about loaded prescription
* Test prescription units
* Allow multiple hardware configurations per pipeline unit
* Allow multiple configurations for which the unit should be registered
* Add release and data infor to the prescription chema
* Register UBI boot only if UBI is used
* Add URL to logged message automatically
* Add extend justification links if links do not point to any hosted site
* Improve type handling in the prescription module
* Fix docs for step prescription
* Provide a sub-command to validate prescription YAML
* Fix links to docs for pipeline units
* Add a note to prescription docs
* :arrow_up: Automatic update of dependencies by Kebechet
* Add few examples to prescription docs
* Fix some pre-commit complains
* :arrow_up: Automatic update of dependencies by Kebechet
* Introduce prescription
* :arrow_up: Automatic update of dependencies by Kebechet
* change si scoring and add info justification
* Normalize score returned from CVE step score
* Fix tests related to metadata propagation
* Add type annotations
* Add tests related to metadata propagation
* Fix link to Thoth s2i info
* Reformat using black
* Fix missing thoth section in the recommended stack
* Remove user's stack if development dependencies are not present
* Manual dependency update
* Remove user's stack if any changes in requirements were detected (#1726)
* Fix justification messages reported by backport sieves
* :arrow_up: Automatic update of dependencies by Kebechet (#1725)
### Bug Fixes
* Remove TF Keras embedding wrap that was moved to prescriptions (#1799)
* Minor fix in the testsuite
### Improvements
* Fix referencing index URL
* return justification rather than adding it to stack_info
* Add tests related to prescription units registration
* Remove unused debug statement
* State logged message rather than logged text
* Fix typing for prescription units and core units (#1748)
* Adjust tests for passing prescription and cli_parameters
* Adjust type of the message for S2I info (#1736)
* Propagate metadata to justification and stack info
* Remove unused imports
* Add dev projects used for testing to MANIFEST.in

## Release 0.28.0 (2021-04-12T21:14:56)
### Features
* Update Thoth landing page
* :arrow_up: Automatic update of dependencies by Kebechet (#1815)
* :arrow_up: Automatic update of dependencies by Kebechet (#1814)
* Update database of symbols available for TensorFlow 2.5.0 (#1807)
* :arrow_up: Automatic update of dependencies by Kebechet (#1812)
* :arrow_up: Automatic update of dependencies by Kebechet (#1805)
* :arrow_up: Automatic update of dependencies by Kebechet (#1803)
### Improvements
* Minor improvements in docs
* Minor improvements in docs (#1813)
* Remove not relevant to do comment (#1810)
* Allow including one pipeline unit multiple times per matched entry (#1806)

## Release 0.29.0 (2021-04-26T21:32:24)
### Features
* Implement support for constraints
* :arrow_up: Automatic update of dependencies by Kebechet
* Adjust format for unsolved direct dependencies report (#1829)
* :arrow_up: Automatic update of dependencies by Kebechet (#1827)
* Add github release notes to justification (#1821)
* :arrow_up: Automatic update of dependencies by Kebechet (#1824)
* Revisit architecture overview (#1816)
### Non-functional
* Link YouTube video and pull request implementing GH release notes wrap (#1831)

## Release 0.30.0 (2021-05-11T09:16:52)
### Features
* Log recommendation type used when starting adviser (#1859)
* Log removal of a legacy version just once (#1858)
* Keep track of iteration in pipeline builder (#1860)
* :arrow_up: Automatic update of dependencies by Kebechet (#1856)
* Add support for skip package prescription unit
* :arrow_up: Automatic update of dependencies by Kebechet (#1852)
* Let users know where to report bugs or service issues (#1849)
* :arrow_up: Automatic update of dependencies by Kebechet (#1851)
* :arrow_up: Automatic update of dependencies by Kebechet (#1847)
* :arrow_up: Automatic update of dependencies by Kebechet (#1844)
* :arrow_up: Automatic update of dependencies by Kebechet
### Improvements
* Document how to use constraints files

## Release 0.31.0 (2021-06-03T13:54:32)
### Features
* Keep CVE advisory in the justification output
* :arrow_up: Automatic update of dependencies by Kebechet
* Add a sieve implementing filtering based on solver rules
* :arrow_up: Automatic update of dependencies by Kebechet
* Document solver rules
* Adjust for CVEs consumed from PyPA
* :arrow_up: Automatic update of dependencies by Kebechet
* :arrow_up: Automatic update of dependencies by Kebechet
* :arrow_up: Automatic update of dependencies by Kebechet
* :arrow_up: Automatic update of dependencies by Kebechet (#1871)
* :hatched_chick: update the prow resource limits (#1869)
* Update latest.rst
* Update annealing.rst
* Update latest.rst
* Update pipeline.rst
* Update deployment.rst
* Update architecture.rst
* Update developers_guide.rst
* :arrow_up: Automatic update of dependencies by Kebechet (#1866)
* Report all unresolved dependencies (#1864)
### Bug Fixes
* Handle error when all the direct deps are sieved (#1867)
### Improvements
* Add video demonstrating constaints.txt use
* Make boot pipeline unit responsible for providing stack info (#1863)

## Release 0.32.0 (2021-06-07T11:08:03)
### Features
* Include pipeline units if any label matches the environment
* Introduce labels to the resolution engine
* :arrow_up: Automatic update of dependencies by Kebechet
### Improvements
* Document use of labels in prescriptions

## Release 0.33.0 (2021-06-09T11:20:36)
### Features
* Fix wrong read variable
* Notify users if they use runtime environment not known to deployment
* Notify users about labels used during the resolution process
* :arrow_up: Automatic update of dependencies by Kebechet

## Release 0.33.1 (2021-06-11T07:10:33)
### Features
* :arrow_up: Automatic update of dependencies by Kebechet
* Fix spelling mistake in tests.
* :arrow_up: Automatic update of dependencies by Kebechet
### Bug Fixes
* Fix wrong CVE key obtained
### Improvements
* Add update sieve responsible for package updates

## Release 0.33.2 (2021-06-14T11:35:41)
### Features
* :arrow_up: updated labels of issue templates
### Improvements
* Turn warning to debug message

## Release 0.34.0 (2021-06-16T15:04:54)
### Features
* add priority/critical-urgent label to all bot related issue templates
* :arrow_up: Automatic update of dependencies by Kebechet
* Adjust copyright notice in headers
* Add YouTube video for solver rules
* :arrow_up: updated labels of issue templates
### Improvements
* Load prescriptions from a directory structure

## Release 0.35.0 (2021-07-01T17:50:30)
### Features
* Point users to support repository to report issues
* :arrow_up: Automatic update of dependencies by Kebechet
* Add demos from sprint 63
* docs: Add pulp-python monitoring job
* Fix docs for shared objects in prescriptions
* :arrow_up: Automatic update of dependencies by Kebechet
* :arrow_up: Automatic update of dependencies by Kebechet
* Add graph-metrics-exporter
* Update docs/source/security.rst
* Adjust reporting of RPM and SO specific issues
* Perform recommendations based on RPM packages present in the environment
* :arrow_up: Automatic update of dependencies by Kebechet
* :arrow_up: Automatic update of dependencies by Kebechet
* Adjust validate logic to consume prescriptions from a dir
* Filter Python packages present in software stack based on so files
* add docs for security advises
### Bug Fixes
* Keep pipeline run information only when adviser is run in verbose mode
### Improvements
* Adjust documentation for prescriptions living in a dir structure
* Extend documentation for security

## Release 0.36.0 (2021-07-14T07:04:54)
### Features
* Notify about packages published on Operate First Pulp instance
* :bug: converted it to a string containing a comma separated list of strings
* Add a wrap that notifies about Python package releases on PyPI
* Remove no observations wrap
* :arrow_up: Automatic update of dependencies by Kebechet
* Ignore flake8 errors on naming
* Implement a pipeline unit for filtering Python packages already present in base
* TensorFlow 2.5 is built with CUDA 11.2 support
* Update TensorFlow API symbols to include symbols in 2.6 release
* Introduce a mechanism for including unit based on Python packages
* :arrow_up: Automatic update of dependencies by Kebechet
### Improvements
* TensorFlow 2.6 uses same CUDA as TensorFlow 2.5, CUDA 11.2
* Add test for loading using yaml.CLoader
* Use CLoader to load prescriptions to speed up loading

## Release 0.37.0 (2021-07-22T16:22:52)
### Features
* Make Pulp URL configurable
* Link package information to libraries.io
* State dependency graph in the resulting document
* Do not add scored user stack to beam
* Add package name to Pulp information
* :arrow_up: Automatic update of dependencies by Kebechet
* Pin flexmock to <=0.10.4
* :arrow_up: Automatic update of dependencies by Kebechet
* Fix wrong import
* :arrow_up: Automatic update of dependencies by Kebechet
* Decrease log level accidentally stated as error
* :arrow_up: Automatic update of dependencies by Kebechet
* Use prescriptions, plural
* State also package version when notifying about PyPI packages
* Use orjson to load TensorFlow API symbols
### Bug Fixes
* Rename build time error to installation time error
### Improvements
* Add package name to PyPI release justification info
* Sort resulting justification for better UX
