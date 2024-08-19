# OzSTAR Job Summary

This script, specifically desigend for the OzSTAR supercomputers, generates a summary of a job based on its Job ID. It can be used to print out the summary directly or append it to the job's stdout file in a Slurm epilog.

## Prerequisites
* Python 3.x
* Required Python packages (install using pip):
    * argparse
    * influxdb-client
    * pyslurm
    * tabulate

## Usage
### Command Line Arguments
* job_id (required): The Job ID for which the summary is to be generated.
* --epilog (optional): If specified, appends the summary to the job's stdout file in a Slurm epilog.
* --debug (optional): If specified, allows debug output (e.g., stack traces) to be printed.
* --timeout (optional): Specifies the timeout in seconds for generating the job summary. Default is 30 seconds.

### Example Commands
Generate Job Summary:
```
python jobsummary.py <job_id>
```

Generate Job Summary with in Epilog, appending to job's stdout file:
```
python jobsummary.py <job_id> --epilog
```

## Installation

This script should be installed in a location accessible to users, and a symlink to `./jobsummary` included in the PATH. Since the default Python environment does not have the Python pre-requisites, they should be installed in a virtual environment created in `venv/`, which `./jobsummary` activates prior to running the Python script.
