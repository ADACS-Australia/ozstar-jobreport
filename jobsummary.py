from sacct import call_sacct
from lustre import get_summary, print_lustre_summary
from memory import get_max_mem, get_req_mem, print_mem_summary
from cpu import get_avg_cpu, print_cpu_summary
from runtime import print_time_summary
from warn import print_warnings
from utils import Timeout
import argparse


def summary(job_id):
    # Call sacct to get stats
    saact_data = call_sacct(job_id)

    # Get the Lustre summary
    summary = get_summary(job_id)

    # Print the Lustre summary
    print_lustre_summary(summary)
    print()

    max_mem = get_max_mem(job_id)
    req_mem = get_req_mem(saact_data)
    print_mem_summary(max_mem, req_mem)

    # Get the average CPU usage
    print()
    avg_cpu = get_avg_cpu(job_id)
    print_cpu_summary(avg_cpu)

    # Print time summary
    print()
    print_time_summary(saact_data)

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
    try:
        with Timeout(seconds=30):
            summary(args.job_id)
    except Exception as e:
        print("Job summary could not be generated (Read timed out)")


if __name__ == "__main__":
    main()
