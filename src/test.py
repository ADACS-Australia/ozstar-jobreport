import sys
import os
import pyslurm

from jobsummary import get_summary
from tqdm import tqdm

# Get a list of jobs from squeue
test_jobs = pyslurm.Jobs.load()

for job in tqdm(test_jobs, desc="Testing jobs"):
    # Suppress print
    sys.stdout = open(os.devnull, "w")

    # Test job
    print(get_summary(job))

    # Restore print
    sys.stdout = sys.__stdout__
