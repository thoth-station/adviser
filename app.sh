#!/usr/bin/env sh
#
# This script is run by OpenShift's s2i. Here we guarantee that we run desired
# sub-command based on env-variables configuration.
#


if [ "$THOTH_PROVENANCE" == "1" ]; then
	exec thoth-adviser provenance
else
	exec thoth-adviser pypi
fi

