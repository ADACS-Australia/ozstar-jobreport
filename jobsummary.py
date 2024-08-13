from slurm_stats import get_slurm_stats, get_stdout_file
from lustre import get_summary, print_lustre_summary
from memory import get_max_mem, print_mem_summary
from cpu import get_avg_cpu, print_cpu_summary
from runtime import print_time_summary
from warn import print_warnings
from utils import Timeout, redirect_stdout_to_file
import argparse

def summary(job_id):
    # Call pyslurm to get stats
    pyslurm_data = get_slurm_stats(job_id)

    # Get the Lustre summary
    summary = get_summary(job_id)

    # Print the Lustre summary
    print_lustre_summary(summary)
    print()

    max_mem = get_max_mem(job_id, pyslurm_data)
    req_mem = pyslurm_data["req_mem"]
    print_mem_summary(max_mem, req_mem)

    # Get the average CPU usage
    print()
    avg_cpu = get_avg_cpu(job_id, pyslurm_data)
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
    parser.add_argument("--epilog", action="store_true", help="Append to the job's stdout file in Slurm epilog")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds for the job summary")
    args = parser.parse_args()

    if args.epilog:
        stdout_file = get_stdout_file(args.job_id)
        if stdout_file is not None:
            redirect_stdout_to_file(stdout_file)

        # Add a newline to separate the summary from the rest of the output
        print()

    if args.timeout > 0:
        try:
            with Timeout(seconds=args.timeout):
                summary(args.job_id)
        except Exception as e:
            print(f"Job summary could not be generated ({e})")

    # If timeout is zero, run directly for easier debugging
    else:
        summary(args.job_id)


if __name__ == "__main__":
    main()
