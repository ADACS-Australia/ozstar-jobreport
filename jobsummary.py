import sys
import argparse
import os

from utils import Timeout
from summary import JobSummary
from influx import InfluxQuery


def get_summary(job_id):
    influxdb_url = os.environ.get("INFLUXDB_URL", None)
    influxdb_org = os.environ.get("INFLUXDB_ORG", None)
    influxdb_token = os.environ.get("INFLUXDB_TOKEN", None)

    if influxdb_url is None or influxdb_org is None or influxdb_token is None:
        query = None
    else:
        query = InfluxQuery(influxdb_url, influxdb_org, influxdb_token)

    job_summary = JobSummary(job_id, query)
    return job_summary


def main():
    # Get command line args
    parser = argparse.ArgumentParser(
        description="Print out a summary of the job", prog="jobsummary"
    )
    parser.add_argument("job_id", type=str, help="Job ID")
    parser.add_argument(
        "--epilog",
        action="store_true",
        help="Append to the job's stdout file in Slurm epilog",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout in seconds for the job summary"
    )
    args = parser.parse_args()

    # Defaults
    exit_code = 1
    stdout_file = None
    job_summary = None

    # Run the job summary with a timeout
    if args.timeout > 0:
        try:
            with Timeout(seconds=args.timeout):
                job_summary = get_summary(args.job_id)
        except Exception as e:
            print(f"Error: job summary could not be generated ({e})")

    # If timeout is zero, run directly for easier debugging
    else:
        job_summary = get_summary(args.job_id)

    # Get output file if epilog is enabled
    if args.epilog:
        stdout_file = job_summary.get_stdout_file()

    # Print/write the summary
    if job_summary is not None:
        if stdout_file is not None:
            try:
                print(f"Appending to file: {stdout_file}")
                with open(stdout_file, "a") as file:
                    file.write(job_summary + "\n")
                exit_code = 0
            except PermissionError:
                print(f"Permission denied to write to {stdout_file}")
        else:
            print(job_summary)
            exit_code = 0

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
