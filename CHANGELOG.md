
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

## Release 0.7.1 (2019-12-11T10:06:12)
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
