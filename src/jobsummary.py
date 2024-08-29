import sys
import argparse
import traceback

from socket import gethostname
from pathlib import Path
from utils import Timeout, get_scontrol_data
from summary import JobSummary
from influx import InfluxQuery


def get_summary(job_id, influx_config=None, debug=False):
    query = None

    # Initialize InfluxQuery if the configuration file exists
    if influx_config is not None and Path(influx_config).exists():
        try:
            query = InfluxQuery(Path(influx_config), retries=3)
        except Exception:
            print("Warning: InfluxQuery could not be initialized")
            if debug:
                print(traceback.format_exc())
    else:
        print("Warning: InfluxDB configuration file not found")

    job_summary = JobSummary(job_id, query)
    return job_summary


def main(job_id, epilog=False, influx_config=None, debug=False):
    raw_id = JobSummary.get_raw_id(job_id)
    stdout_file = None
    batch_host = None
    is_batch_job = True

    scontrol_data = get_scontrol_data(raw_id, debug)

    if scontrol_data is not None:
        if scontrol_data["std_out"] is not None:
            stdout_file = Path(scontrol_data["std_out"])
        batch_host = scontrol_data["batch_host"]
        is_batch_job = bool(scontrol_data['batch_flag'])

    # Ensure that this only runs on the batch host if in epilog mode
    if epilog and batch_host != gethostname():
        if debug:
            print("Warning: job summary in epilog mode can only be run on the batch host")
        return

    if epilog and not is_batch_job:
        if debug:
            print("Warning: job summary in epilog mode can only be run for batch jobs")
        return

    # Create job summary
    job_summary = get_summary(job_id, influx_config, debug)

    # Do nothing if in epilog mode and the job hasn't finished
    if epilog and not job_summary.finished:
        print("Warning: job has not finished yet")
        return

    # Print/write the summary
    if job_summary is not None:
        if epilog and stdout_file is not None and job_summary.finished:
            try:
                with open(stdout_file, "a") as file:
                    file.write("\n" + str(job_summary) + "\n")
            except PermissionError:
                print("Error: permission denied writing to job stdout file")
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
        "--influx-config",
        type=str,
        help="InfluxDB configuration file",
    )
    args = parser.parse_args()

    # Handle exceptions at the top level
    try:
        # Ensure the code does not hang
        with Timeout(int(args.timeout)):
            main(args.job_id, args.epilog, args.influx_config, args.debug)

    # Print exception tracebacks if in debug mode
    except Exception:
        print("Error: job summary could not be generated")
        if args.debug:
            raise
        sys.exit(1)
