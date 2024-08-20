import os
import sys
import argparse
import traceback

from utils import Timeout
from summary import JobSummary
from influx import InfluxQuery


def get_summary(job_id, config_file="conf.influxdb.toml", debug=False):
    query = None
    # Initialize InfluxQuery if the config file exists
    if os.path.exists(config_file):
        try:
            query = InfluxQuery(config_file=config_file, retries=3)
        except Exception:
            print("Warning: InfluxQuery could not be initialized")
            if debug:
                print(traceback.format_exc())
    else:
        print(f"Warning: InfluxDB configuration file '{config_file}' does not exist")

    job_summary = JobSummary(job_id, query)
    return job_summary


def main(job_id, epilog=False, config_file="conf.influxdb.toml", debug=False):
    stdout_file = None

    # Create job summary
    job_summary = get_summary(job_id, config_file, debug)

    # Get output file if epilog is enabled
    if epilog:
        stdout_file = job_summary.get_stdout_file(debug)

    # Print/write the summary
    if job_summary is not None:
        if stdout_file is not None:
            try:
                with open(stdout_file, "a") as file:
                    file.write(str(job_summary) + "\n")
            except PermissionError:
                print(f"Error: permission denied to write to '{stdout_file}'")
        else:
            print(job_summary)


if __name__ == "__main__":
    # Get command line args
    parser = argparse.ArgumentParser(
        description="Print out a summary of the job", prog="jobsummary"
    )
    parser.add_argument("job_id", type=str, help="Job ID")
    parser.add_argument(
        "-e",
        "--epilog",
        action="store_true",
        help="Append to the job's stdout file in Slurm epilog",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Allow debug output (e.g. stack traces) to be printed",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for the job summary",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        default="conf.influxdb.toml",
        help="InfluxDB configuration file",
    )
    args = parser.parse_args()

    # Handle exceptions at the top level
    try:
        # Ensure the code does not hang
        with Timeout(int(args.timeout)):
            main(args.job_id, args.epilog, args.config_file, args.debug)

    # Print exception tracebacks if in debug mode
    except Exception:
        print("Error: job summary could not be generated")
        if args.debug:
            raise
        sys.exit(1)
