import sys
import os
import pyslurm

from jobsummary import get_summary
from tqdm import tqdm

def str_to_bool(value):
    return value.lower() in {"true", "1", "yes", "y"}

VERBOSE = str_to_bool(os.environ.get("VERBOSE", "no"))
DEBUG = str_to_bool(os.environ.get("DEBUG", "no"))

# Get current file path
fpath = os.path.abspath(__file__)

# Get a list of jobs from squeue
test_jobs = pyslurm.Jobs.load()

for job in tqdm(test_jobs, desc="Testing jobs"):
    # Suppress print
    if not VERBOSE:
        sys.stdout = open(os.devnull, "w")

    # Test job
    print(get_summary(job, influx_config=f"{fpath}/../conf.influxdb.toml"), DEBUG)

    # Restore print
    if not VERBOSE:
        sys.stdout = sys.__stdout__
