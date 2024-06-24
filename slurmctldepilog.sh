#!/bin/bash

# SLURM: slurmctld epilog run by the control daemon on transom1

if [ -z "${SLURM_JOB_ID}" ]; then
        echo "This script can only by run by the Slurm software"
        exit 1
fi

# Run jobsummary for the job ID
/apps/jobsummary/jobsummary "$SLURM_JOB_ID"

# Always exit with success so we don't accidentally kill the job
exit 0
