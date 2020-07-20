#!/usr/bin/env sh
#
# This script is run by OpenShift's s2i. Here we guarantee that we run desired
# sub-command based on env-variables configuration.
#

case $THOTH_ADVISER_SUBCOMMAND in
    'provenance')
        exec /opt/app-root/bin/python3 thoth-adviser provenance
        ;;
    'dependency-monkey')
        exec /opt/app-root/bin/python3 thoth-adviser dependency-monkey
        ;;
    'advise')
        # No need to compute all the stacks, the first one found is sufficient to return.
        [ "${THOTH_ADVISER_RECOMMENDATION_TYPE}" = "latest" ] && export THOTH_ADVISER_LIMIT=1
        exec /opt/app-root/bin/python3 thoth-adviser advise
        ;;
    *)
        echo "Application configuration error - no adviser subcommand specified." >&2
        exit 1
        ;;
esac
