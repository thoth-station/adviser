
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
