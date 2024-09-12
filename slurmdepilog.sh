#!/bin/bash

# SLURM: slurmctld epilog run by the control daemon on transom1
# Always exit with success so we don't accidentally drain the node

if [ -z "${SLURM_JOB_ID}" ]; then
    echo "This script can only by run by the Slurm software"
    exit 0
fi

/usr/sbin/runuser -u "$SLURM_JOB_USER" -- /usr/local/bin/jobreport --epilog "$SLURM_JOB_ID" || true

exit 0
