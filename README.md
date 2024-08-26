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


## Details

The codes aims to pull as much data as possible from the Slurm DB, and reverts to querying the InfluxDB when that's not possible. The Slurm DB only has data once the job is finished, and Lustre data is only ever available from Influx.
An Influx toml configuration file is required. See the template.

In epilog mode, the script will attempt to write to the job's standard output file, but only if the host matches the job's Batch Host. This is to prevent each node of a multi-node job from trying to write the output.
