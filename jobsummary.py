from slurm_stats import get_slurm_stats
from lustre import get_summary, print_lustre_summary
from memory import get_max_mem, print_mem_summary
from cpu import get_avg_cpu, print_cpu_summary
from runtime import print_time_summary
from warn import print_warnings
from utils import Timeout
import argparse


def summary(job_id):
    # Call pyslurm to get stats
    pyslurm_data = get_slurm_stats(job_id)

    # Get the Lustre summary
    summary = get_summary(job_id)

    # Print the Lustre summary
    print_lustre_summary(summary)
    print()

    if pyslurm_data["state"] == "RUNNING":
        # Use live data from InfluxDB when running
        max_mem = get_max_mem(job_id)
    else:
        max_mem = pyslurm_data["max_mem"]

    req_mem = pyslurm_data["req_mem"]
    print_mem_summary(max_mem, req_mem)

    # Get the average CPU usage
    print()
    avg_cpu = get_avg_cpu(job_id)
    print_cpu_summary(avg_cpu)

    # Print time summary
    print()
    print_time_summary(pyslurm_data)

    # Print warnings
    print()
    print_warnings(max_mem, req_mem, avg_cpu)


def main():
    """Print out a summary of the job"""

    # Get the job ID from the command line
    parser = argparse.ArgumentParser(
        description="Print out a summary of the job", prog="jobsummary"
    )
    parser.add_argument("job_id", type=str, help="Job ID")
    args = parser.parse_args()

    print()

    # Set a timeout to prevent jobs from hanging
    summary(args.job_id)
    # try:
    #     with Timeout(seconds=30):
    #         summary(args.job_id)
    # except Exception as e:
    #     print("Job summary could not be generated (Read timed out)")


if __name__ == "__main__":
    main()
