# OzSTAR Job Report

A job reporting tool for the OzSTAR supercomputer that generates a summary of a job based on its Job ID. It can be used to print out the summary directly or append it to the job's stdout file in a Slurm epilog.

## Prerequisites
* Python 3.x
* Required Python packages (install using pip):
    * influxdb-client
    * pyslurm
    * tabulate
    * Cython
    * plotext
    * numpy
    * pandas

## Install requirements
```bash
pip install -r requirements.txt
```

## Build cython extension
Remember to build the Cython `jobload` extension by running `make`. Use the environment variables `SLURM_LIB_DIR` and `SLURM_INCLUDE_DIR` to specify where the Slurm library and header files are located (if not in `/usr/lib64` and `/usr/include`). e.g.
```bash
SLURM_INCLUDE_DIR=/apps/slurm/latest/include/ SLURM_LIB_DIR=/apps/slurm/latest/lib/ make
```

## Usage

Run the job report tool using the wrapper script:
```bash
./jobreport [options]
```

### Command Line Arguments
* job_id (required): The Job ID for which the summary is to be generated.
* --epilog (optional): If specified, appends the summary to the job's stdout file in a Slurm epilog.
* --debug (optional): If specified, allows debug output (e.g., stack traces) to be printed.
* --timeout (optional): Specifies the timeout in seconds for generating the job summary. Default is 30 seconds.

### Example Commands
Generate Job Summary:
```bash
python jobreport.py <job_id>
```

Generate Job Summary in Epilog, appending to job's stdout file:
```bash
python jobreport.py <job_id> --epilog
```

## Installation

This script should be installed in a location accessible to users, and a symlink to `./jobreport` included in the PATH. Since the default Python environment does not have the Python pre-requisites, they should be installed in a virtual environment created in `venv/`, which `./jobreport` activates prior to running the Python script.

## Details

The code aims to pull as much data as possible from the Slurm DB, and reverts to querying the InfluxDB when that's not possible. The Slurm DB only has data once the job is finished, and Lustre data is only ever available from Influx.
An Influx toml configuration file is required. See the template.

In epilog mode, the script will attempt to write to the job's standard output file, but only if the host matches the job's Batch Host. This is to prevent each node of a multi-node job from trying to write the output.

## Updating pyslurm

When updating pyslurm on dbuild, follow these steps:

1. Mount /apps as read-write:
   ```bash
   sudo /opt/root/remountApps rw
   ```

2. Make code changes to `/apps/system/software/jobreport`

3. Edit `requirements.txt` to update pyslurm version

4. Set environment variables to build against the correct version of SLURM:
   ```bash
   export SLURM_INCLUDE_DIR=/apps/slurm/24.11.5/include/
   export SLURM_LIB_DIR=/apps/slurm/24.11.5/lib/
   ```

5. Activate the virtual environment:
   ```bash
   . venv/jobreport/bin/activate
   ```

6. Use the version of Python specified in the `jobreport` wrapper script (either by loading the module or setting the library path directly):
   ```bash
   export LD_LIBRARY_PATH=/apps/modules/software/Python/3.11.3-GCCcore-12.3.0/lib:/apps/modules/software/OpenSSL/1.1/lib:$LD_LIBRARY_PATH
   ```

7. Update the environment:
   ```bash
   pip install -r requirements.txt
   ```

8. Remount apps as read-only:
   ```bash
   sudo /opt/root/remountApps ro
   ```
