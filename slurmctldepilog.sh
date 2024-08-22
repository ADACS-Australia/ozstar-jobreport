#!/bin/bash

# SLURM: slurmctld epilog run by the control daemon on transom1
# Always exit with success so we don't accidentally drain the node

if [ -z "${SLURM_JOB_ID}" ]; then
        echo "This script can only by run by the Slurm software"
        exit 0
fi

# Run jobsummary for the job ID
/apps/jobsummary/jobsummary "$SLURM_JOB_ID" || true
exit 0
