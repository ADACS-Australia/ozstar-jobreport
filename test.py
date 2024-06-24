import sys
import os
from utils import cmd
from jobsummary import summary
from tqdm import tqdm

# Get a list of jobs from squeue
output = cmd("squeue -o '%i' -h")
test_jobs = output.splitlines()

for job in tqdm(test_jobs, desc="Testing jobs"):

    # Suppress print
    sys.stdout = open(os.devnull, "w")

    # Test job
    summary(job)

    # Restore print
    sys.stdout = sys.__stdout__
